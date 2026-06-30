import yfinance as yf
import pandas as pd
from sqlalchemy.orm import Session
from src.database import SessionLocal, init_db
from src.models import Symbol, Benchmark, PricesDaily, PricesWeekly, PricesMonthly
from src.config_loader import load_config, sync_config
from src.resampler import resample_all
from src.ratio_engine import compute_all_ratios
from src.indicator_engine import compute_all_indicators
from src.levels_engine import compute_all_levels
from src.ranking_engine import compute_all_rankings
from src.watchlist_engine import generate_initial_watchlists
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_history(ticker: str, period="max"):
    periods = [period]
    if period == "max":
        periods.extend(["10y", "5y", "1y"])

    for p in periods:
        for attempt in range(3):
            try:
                logger.info(f"Fetching {ticker} (period={p}, attempt {attempt+1})...")
                # auto_adjust=False ensures we get 'Adj Close'
                data = yf.download(ticker, period=p, progress=False, auto_adjust=False)
                if not data.empty:
                    return data
            except Exception as e:
                logger.error(f"Error fetching {ticker} (period={p}): {e}")
                time.sleep(2)
    return pd.DataFrame()

def seed_database():
    init_db()
    db = SessionLocal()
    config = load_config()
    sync_config(db, config)
    
    # REVISED STRATEGY: Treat benchmarks as symbols for price storage
    # Step 1: Ensure all benchmark tickers are in Symbols table
    for b_data in config.benchmarks:
        sym = db.query(Symbol).filter(Symbol.ticker == b_data.ticker).first()
        if not sym:
            sym = Symbol(ticker=b_data.ticker, name=b_data.name, is_active=True)
            db.add(sym)
    db.commit()

    symbols = db.query(Symbol).filter(Symbol.is_active == True).all()
    
    for symbol in symbols:
        df = fetch_history(symbol.ticker)
        if df.empty:
            logger.warning(f"No data for {symbol.ticker}")
            continue
            
        if len(df) < 60:
            logger.warning(f"Thin history for {symbol.ticker} ({len(df)} candles)")
            symbol.thin_history = True
            
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        # yfinance columns might be lowercase or have spaces
        col_map = {col.lower().replace(' ', ''): col for col in df.columns}
        
        for date, row in df.iterrows():
            exists = db.query(PricesDaily).filter(
                PricesDaily.symbol_id == symbol.id,
                PricesDaily.date == date.date()
            ).first()
            
            if not exists:
                try:
                    price = PricesDaily(
                        symbol_id=symbol.id,
                        date=date.date(),
                        open=float(row[col_map['open']]),
                        high=float(row[col_map['high']]),
                        low=float(row[col_map['low']]),
                        close=float(row[col_map['close']]),
                        volume=int(row[col_map['volume']]),
                        adj_close=float(row[col_map['adjclose']])
                    )
                    db.add(price)
                except KeyError as e:
                    logger.error(f"Missing column in {symbol.ticker}: {e}")
                    break
        
        db.commit()
        logger.info(f"Seeded {symbol.ticker}")
    
    # Step 3: Run full computation pipeline for all timeframes
    logger.info("Running full initial computation pipeline...")
    resample_all()
    compute_all_ratios()
    compute_all_indicators()
    compute_all_levels()
    compute_all_rankings()
    generate_initial_watchlists()
    
    logger.info("Seeding and initial computation complete.")
    db.close()

if __name__ == "__main__":
    seed_database()
