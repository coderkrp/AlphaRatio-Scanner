import pandas as pd
import argparse
import logging
from src.database import SessionLocal
from src.models import Symbol, PricesDaily, Timeframe
from src.resampler import resample_symbol
from src.ratio_engine import compute_ratios_for_timeframe
from src.indicator_engine import compute_indicators_for_timeframe
from src.levels_engine import compute_levels_for_timeframe
from src.ranking_engine import compute_rankings_for_timeframe
from src.watchlist_engine import evaluate_watchlist_for_timeframe
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from src.config_loader import load_config, sync_config

def import_csv(symbol_ticker, csv_path, timeframe_str, on_conflict):
    db = SessionLocal()
    config = load_config()
    
    # 1. Check if symbol is in config §4.3
    all_config_tickers = [s['ticker'] for s in config.get('symbols', [])] + \
                         [b['ticker'] for b in config.get('benchmarks', [])]
    
    if symbol_ticker not in all_config_tickers:
        logger.error(f"Symbol {symbol_ticker} not found in config.yaml. Please add it to config.yaml first.")
        db.close()
        return

    # 2. Ensure symbol is in database
    symbol = db.query(Symbol).filter(Symbol.ticker == symbol_ticker).first()
    if not symbol:
        logger.info(f"Symbol {symbol_ticker} found in config but missing from DB. Syncing config...")
        sync_config(db, config)
        symbol = db.query(Symbol).filter(Symbol.ticker == symbol_ticker).first()
        if not symbol:
            logger.error(f"Failed to create symbol {symbol_ticker} in database after sync.")
            db.close()
            return

    if not os.path.exists(csv_path):
        logger.error(f"CSV file {csv_path} not found.")
        db.close()
        return

    df = pd.read_csv(csv_path)
    
    # Column normalisation §4.3
    COLUMN_MAP = {
        'time':   'date',   'Date':   'date',
        'open':   'open',   'Open':   'open',
        'high':   'high',   'High':   'high',
        'low':    'low',    'Low':    'low',
        'close':  'close',  'Close':  'close',
        'volume': 'volume', 'Volume': 'volume'
    }
    
    df.rename(columns=COLUMN_MAP, inplace=True)
    required = ['date', 'open', 'high', 'low', 'close', 'volume']
    for col in required:
        if col not in df.columns:
            logger.error(f"Missing required column: {col}")
            return
            
    df['date'] = pd.to_datetime(df['date']).dt.date
    
    # Architecture says 'close' in CSV is mapped to 'Adj Close' in DB
    # We store both. In TV export, if adjusted is enabled, close IS adj_close.
    
    rows_inserted = 0
    rows_overwritten = 0
    rows_skipped = 0
    
    for _, row in df.iterrows():
        exists = db.query(PricesDaily).filter(
            PricesDaily.symbol_id == symbol.id,
            PricesDaily.date == row['date']
        ).first()
        
        if exists:
            if on_conflict == 'overwrite':
                exists.open = float(row['open'])
                exists.high = float(row['high'])
                exists.low = float(row['low'])
                exists.close = float(row['close']) # Store raw close as reference
                exists.volume = int(row['volume'])
                exists.adj_close = float(row['close']) # Canonical
                rows_overwritten += 1
            else:
                rows_skipped += 1
        else:
            new_price = PricesDaily(
                symbol_id=symbol.id,
                date=row['date'],
                open=float(row['open']),
                high=float(row['high']),
                low=float(row['low']),
                close=float(row['close']),
                volume=int(row['volume']),
                adj_close=float(row['close'])
            )
            db.add(new_price)
            rows_inserted += 1
            
    db.commit()
    logger.info(f"Import Summary: {rows_inserted} inserted, {rows_overwritten} overwritten, {rows_skipped} skipped.")
    
    # Trigger recalculation cascade §4.3
    logger.info(f"Triggering recalculation cascade for {symbol_ticker}...")
    
    # 1. Resample
    resample_symbol(db, symbol.id)
    
    # 2. Recompute ratios, indicators, levels, rankings, watchlists
    # For now, we reuse the compute functions. Ideally they should be scoped to a symbol.
    # Architecture says recalculation is scoped to the affected symbol only.
    # I'll need to modify the engines to accept a symbol_id filter.
    
    # For Phase 1, we can just run them all, but let's try to be efficient if possible.
    # Since I don't have scoped functions yet, I'll run them globally for now.
    # TODO: Refactor engines for symbol-scoped recompute.
    
    for tf in [Timeframe.DAILY, Timeframe.WEEKLY, Timeframe.MONTHLY]:
        compute_ratios_for_timeframe(db, tf)
        compute_indicators_for_timeframe(db, tf)
        compute_levels_for_timeframe(db, tf)
        compute_rankings_for_timeframe(db, tf)
        evaluate_watchlist_for_timeframe(db, tf)
        
    db.close()
    logger.info("Recalculation cascade complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import historical OHLC data from TradingView CSV.")
    parser.add_argument("--symbol", required=True, help="Ticker symbol (e.g., RELIANCE.NS)")
    parser.add_argument("--csv", required=True, help="Path to CSV file")
    parser.add_argument("--timeframe", default="daily", help="Timeframe (default: daily)")
    parser.add_argument("--on-conflict", default="overwrite", choices=["skip", "overwrite"], help="Conflict strategy")
    
    args = parser.parse_args()
    import_csv(args.symbol, args.csv, args.timeframe, args.on_conflict)
