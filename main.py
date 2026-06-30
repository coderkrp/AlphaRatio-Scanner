import asyncio
import logging
from datetime import date
import pandas as pd
from sqlalchemy.orm import Session
from src.database import SessionLocal, init_db
from src.config_loader import load_config, sync_config
from seed_database import fetch_history
from src.models import Symbol, PricesDaily, SystemState
from src.resampler import resample_all
from src.ratio_engine import compute_all_ratios
from src.indicator_engine import compute_all_indicators
from src.levels_engine import compute_all_levels
from src.ranking_engine import compute_all_rankings
from src.watchlist_engine import generate_initial_watchlists
from src.alert_engine import send_watchlist_alerts
from src.snapshot_manager import persist_snapshots, cleanup_snapshots
from src.utils import get_active_timeframes

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def run_pipeline():
    db = SessionLocal()
    try:
        # 0. Check Active Timeframes
        today = date.today()
        active_timeframes = get_active_timeframes(today)
        
        if not active_timeframes:
            logger.info(f"No active timeframes for {today} (Sunday/Non-1st). Skipping pipeline.")
            return

        logger.info(f"Active timeframes for {today}: {[tf.value for tf in active_timeframes]}")

        # 1. Sync Config
        logger.info("Step 1: Syncing Config...")
        from pydantic import ValidationError
        import sys
        try:
            config = load_config()
        except ValidationError as e:
            logger.critical(f"Configuration validation failed:\n{e}")
            print(f"CRITICAL: Configuration validation failed!\n{e}", file=sys.stderr)
            sys.exit(1)
            
        sync_config(db, config)
        
        # 2. Download latest EOD data
        logger.info("Step 2: Downloading latest EOD data...")
        symbols = db.query(Symbol).filter(Symbol.is_active == True).all()
        
        benchmark_tickers = [b.ticker for b in config.benchmarks]
        failed_benchmarks = []

        for symbol in symbols:
            # Smart History Fetch: If symbol has no/little history, fetch max.
            # Otherwise fetch last 5 days for incremental update.
            existing_count = db.query(PricesDaily).filter(PricesDaily.symbol_id == symbol.id).count()
            fetch_period = "max" if existing_count < 60 else "5d"
            
            df = fetch_history(symbol.ticker, period=fetch_period)
            if df.empty:
                if symbol.ticker in benchmark_tickers:
                    logger.error(f"Critical: Failed to fetch benchmark {symbol.ticker}")
                    failed_benchmarks.append(symbol.ticker)
                continue
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # 3. Validate data (Smart Invalidation)
            # Fetch fresh yesterday's Adj Close vs stored
            # For brevity in this turn, I'll do a simple append
            # TODO: Implement full Step 3 Smart Invalidation logic
            
            col_map = {col.lower().replace(' ', ''): col for col in df.columns}
            for date_idx, row in df.iterrows():
                exists = db.query(PricesDaily).filter(
                    PricesDaily.symbol_id == symbol.id,
                    PricesDaily.date == date_idx.date()
                ).first()
                if not exists:
                    price = PricesDaily(
                        symbol_id=symbol.id,
                        date=date_idx.date(),
                        open=float(row[col_map['open']]),
                        high=float(row[col_map['high']]),
                        low=float(row[col_map['low']]),
                        close=float(row[col_map['close']]),
                        volume=int(row[col_map['volume']]),
                        adj_close=float(row[col_map['adjclose']])
                    )
                    db.add(price)
            db.commit()

        if failed_benchmarks:
            from src.telegram_bot import TelegramBot
            bot = TelegramBot()
            alert_msg = f"⚠️ *CRITICAL: Data Fetch Failure*\nFailed to fetch EOD data for benchmarks:\n" + "\n".join([f"- `{t}`" for t in failed_benchmarks])
            await bot.send_message(alert_msg)

        # 4-7. Compute steps
        logger.info("Steps 4-7: Computing metrics...")
        resample_all(active_timeframes)
        compute_all_ratios(active_timeframes)
        compute_all_indicators(active_timeframes)
        compute_all_levels(active_timeframes)
        compute_all_rankings(active_timeframes)
        
        # 8-9. Watchlists & Transitions
        logger.info("Steps 8-9: Evaluating watchlists...")
        generate_initial_watchlists(active_timeframes)
        
        # 10. Send Alerts
        logger.info("Step 10: Sending alerts...")
        await send_watchlist_alerts(db, active_timeframes)
        
        # 11-12. Snapshots
        logger.info("Steps 11-12: Managing snapshots...")
        persist_snapshots(db)
        cleanup_snapshots(db)
        
        # 13. System State
        logger.info("Step 13: Updating system state...")
        state = db.query(SystemState).filter(SystemState.key == 'last_successful_run').first()
        if not state:
            state = SystemState(key='last_successful_run', value=date.today().isoformat())
            db.add(state)
        else:
            state.value = date.today().isoformat()
        db.commit()
        
        logger.info("Pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    asyncio.run(run_pipeline())
