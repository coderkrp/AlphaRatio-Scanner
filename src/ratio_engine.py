from sqlalchemy import func
import pandas as pd
from sqlalchemy.orm import Session
from src.models import Symbol, Benchmark, PricesDaily, PricesWeekly, PricesMonthly, RatiosDaily, RatiosWeekly, RatiosMonthly, Timeframe
from src.database import SessionLocal
from src.config_loader import load_config
import logging

logger = logging.getLogger(__name__)

def compute_ratios_for_timeframe(db: Session, timeframe: Timeframe):
    config = load_config()
    symbols_config = config.get('symbols', [])
    
    # Map timeframe to models
    models = {
        Timeframe.DAILY: (PricesDaily, RatiosDaily),
        Timeframe.WEEKLY: (PricesWeekly, RatiosWeekly),
        Timeframe.MONTHLY: (PricesMonthly, RatiosMonthly)
    }
    PriceModel, RatioModel = models[timeframe]
    
    for s_config in symbols_config:
        ticker = s_config['ticker']
        symbol = db.query(Symbol).filter(Symbol.ticker == ticker).first()
        if not symbol: continue
        
        benchmarks_tickers = s_config.get('benchmarks', [])
        for b_ticker in benchmarks_tickers:
            benchmark = db.query(Benchmark).filter(Benchmark.ticker == b_ticker).first()
            if not benchmark: continue
            
            # 1. Get high-watermark
            max_date = db.query(func.max(RatioModel.date)).filter(
                RatioModel.symbol_id == symbol.id,
                RatioModel.benchmark_id == benchmark.id
            ).scalar()
            
            # 2. Fetch prices for symbol and benchmark since max_date
            s_prices_query = db.query(PriceModel).filter(PriceModel.symbol_id == symbol.id)
            
            b_sym = db.query(Symbol).filter(Symbol.ticker == b_ticker).first()
            if not b_sym:
                logger.warning(f"Benchmark symbol {b_ticker} not found in symbols table.")
                continue
                
            b_prices_query = db.query(PriceModel).filter(PriceModel.symbol_id == b_sym.id)
            
            if max_date:
                s_prices_query = s_prices_query.filter(PriceModel.date > max_date)
                b_prices_query = b_prices_query.filter(PriceModel.date > max_date)
            
            s_df = pd.read_sql(s_prices_query.order_by(PriceModel.date.asc()).statement, db.bind)
            b_df = pd.read_sql(b_prices_query.order_by(PriceModel.date.asc()).statement, db.bind)
            
            if s_df.empty or b_df.empty: continue
            
            s_df.set_index('date', inplace=True)
            b_df.set_index('date', inplace=True)
            
            # Align dates and compute ratio
            combined = pd.merge(s_df[['adj_close']], b_df[['adj_close']], left_index=True, right_index=True, suffixes=('_s', '_b'))
            
            if combined.empty:
                continue
                
            combined['ratio'] = combined['adj_close_s'] / combined['adj_close_b']
            combined['symbol_id'] = symbol.id
            combined['benchmark_id'] = benchmark.id
            combined.reset_index(inplace=True)
            
            # Ensure date is date object for consistent SQLite storage
            combined['date'] = pd.to_datetime(combined['date']).dt.date
            
            # Prepare records for bulk insert
            records = combined[['symbol_id', 'benchmark_id', 'date', 'ratio']].to_dict(orient='records')
            db.bulk_insert_mappings(RatioModel, records)
            db.commit()
            
            logger.info(f"Computed {len(records)} new {timeframe.value} ratios for {ticker} vs {b_ticker}")


def compute_all_ratios(timeframes: list[Timeframe] = None):
    if timeframes is None:
        timeframes = [Timeframe.DAILY, Timeframe.WEEKLY, Timeframe.MONTHLY]
    db = SessionLocal()
    for tf in timeframes:
        logger.info(f"Computing ratios for {tf.value}...")
        compute_ratios_for_timeframe(db, tf)
    db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    compute_all_ratios()
