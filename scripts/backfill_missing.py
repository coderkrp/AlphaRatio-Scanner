import logging
import pandas as pd
from src.database import SessionLocal, init_db
from src.config_loader import load_config, sync_config
from seed_database import fetch_history
from src.models import Symbol, PricesDaily, Timeframe, Benchmark
from src.resampler import resample_all
from src.ratio_engine import compute_all_ratios
from src.indicator_engine import compute_all_indicators
from src.levels_engine import compute_all_levels
from src.ranking_engine import compute_all_rankings
from src.watchlist_engine import generate_initial_watchlists

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def backfill():
    db = SessionLocal()
    init_db()
    
    # 1. Sync Config
    logger.info("Step 1: Syncing configuration from config.yaml...")
    config = load_config()
    sync_config(db, config)
    
    # 2. Identify missing symbols (those with < 60 days of history)
    # This includes the newly added benchmarks
    logger.info("Step 2: Identifying symbols with missing history...")
    symbols = db.query(Symbol).filter(Symbol.is_active == True).all()
    missing_symbols = []
    for s in symbols:
        count = db.query(PricesDaily).filter(PricesDaily.symbol_id == s.id).count()
        if count < 60:
            missing_symbols.append(s)
            
    if not missing_symbols:
        logger.info("No missing symbols found. Database is up to date.")
    else:
        logger.info(f"Found {len(missing_symbols)} symbols needing backfill: {[s.ticker for s in missing_symbols]}")
        
        # 3. Fetch data for missing symbols
        for s in missing_symbols:
            logger.info(f"Fetching history for {s.ticker}...")
            df = fetch_history(s.ticker, period="max")
            if df.empty:
                logger.warning(f"Failed to fetch data for {s.ticker}")
                continue
                
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            col_map = {col.lower().replace(' ', ''): col for col in df.columns}
            
            records_to_add = []
            for date_idx, row in df.iterrows():
                exists = db.query(PricesDaily).filter(
                    PricesDaily.symbol_id == s.id,
                    PricesDaily.date == date_idx.date()
                ).first()
                
                if not exists:
                    try:
                        records_to_add.append({
                            'symbol_id': s.id,
                            'date': date_idx.date(),
                            'open': float(row[col_map['open']]),
                            'high': float(row[col_map['high']]),
                            'low': float(row[col_map['low']]),
                            'close': float(row[col_map['close']]),
                            'volume': int(row[col_map['volume']]),
                            'adj_close': float(row[col_map['adjclose']])
                        })
                    except Exception as e:
                        logger.error(f"Error parsing {s.ticker} at {date_idx.date()}: {e}")
                        break
            
            if records_to_add:
                db.bulk_insert_mappings(PricesDaily, records_to_add)
                db.commit()
                logger.info(f"Inserted {len(records_to_add)} records for {s.ticker}")

    # 4. Trigger full computation for all timeframes
    logger.info("Step 3: Triggering full computation pipeline for all timeframes...")
    tfs = [Timeframe.DAILY, Timeframe.WEEKLY, Timeframe.MONTHLY]
    
    logger.info(" - Resampling...")
    resample_all(tfs)
    
    logger.info(" - Computing Ratios...")
    compute_all_ratios(tfs)
    
    logger.info(" - Computing Indicators...")
    compute_all_indicators(tfs)
    
    logger.info(" - Computing Levels...")
    compute_all_levels(tfs)
    
    logger.info(" - Computing Rankings...")
    compute_all_rankings(tfs)
    
    logger.info(" - Generating Watchlists...")
    generate_initial_watchlists(tfs)
    
    logger.info("Backfill and computation complete.")
    db.close()

if __name__ == "__main__":
    backfill()
