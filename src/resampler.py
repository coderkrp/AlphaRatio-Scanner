from sqlalchemy import func
import pandas as pd
from sqlalchemy.orm import Session
from src.models import PricesDaily, PricesWeekly, PricesMonthly, Symbol, Timeframe
from src.database import SessionLocal
import logging

logger = logging.getLogger(__name__)

def resample_symbol(db: Session, symbol_id: int, timeframes: list[Timeframe] = None):
    if timeframes is None:
        timeframes = [Timeframe.WEEKLY, Timeframe.MONTHLY]
    
    # Filter for timeframes we actually handle here
    active_tf = [tf for tf in timeframes if tf in [Timeframe.WEEKLY, Timeframe.MONTHLY]]
    if not active_tf:
        return

    # Get high-watermarks
    max_weekly = None
    if Timeframe.WEEKLY in active_tf:
        max_weekly = db.query(func.max(PricesWeekly.date)).filter(PricesWeekly.symbol_id == symbol_id).scalar()
    
    max_monthly = None
    if Timeframe.MONTHLY in active_tf:
        max_monthly = db.query(func.max(PricesMonthly.date)).filter(PricesMonthly.symbol_id == symbol_id).scalar()
    
    # We need to fetch daily prices from the earliest high-watermark
    watermarks = [m for m in [max_weekly, max_monthly] if m is not None]
    start_date = min(watermarks) if watermarks else None
    
    query = db.query(PricesDaily).filter(PricesDaily.symbol_id == symbol_id)
    if start_date:
        query = query.filter(PricesDaily.date > start_date)
    
    df = pd.read_sql(query.order_by(PricesDaily.date.asc()).statement, db.bind)
    
    if df.empty:
        return
    
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    
    last_daily_date = df.index.max().date()
    
    resample_rules = {
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum',
        'adj_close': 'last'
    }

    # Helper to process and bulk insert
    def process_resample(rule, target_model, watermark):
        resampled = df.resample(rule).agg(resample_rules)
        # Drop incomplete bars (anchor date is in the future)
        resampled = resampled[resampled.index.date <= last_daily_date]
        # Drop bars already in DB
        if watermark:
            resampled = resampled[resampled.index.date > watermark]
            
        if not resampled.empty:
            resampled['symbol_id'] = symbol_id
            resampled.reset_index(inplace=True)
            resampled['date'] = resampled['date'].dt.date
            records = resampled.to_dict(orient='records')
            db.bulk_insert_mappings(target_model, records)
            return len(records)
        return 0

    inserted_w = 0
    if Timeframe.WEEKLY in active_tf:
        inserted_w = process_resample('W-FRI', PricesWeekly, max_weekly)
    
    inserted_m = 0
    if Timeframe.MONTHLY in active_tf:
        inserted_m = process_resample('ME', PricesMonthly, max_monthly)
    
    if inserted_w or inserted_m:
        db.commit()
        logger.info(f"Resampled symbol {symbol_id}: {inserted_w} weekly, {inserted_m} monthly bars added.")


def resample_all(timeframes: list[Timeframe] = None):
    db = SessionLocal()
    symbols = db.query(Symbol).all()
    for symbol in symbols:
        logger.info(f"Resampling {symbol.ticker}...")
        # Note: resample_symbol internally handles all timeframes.
        # However, to respect the timeframes list, we'll need to pass it down or filter inside.
        # Let's refactor resample_symbol to accept target timeframes.
        resample_symbol(db, symbol.id, timeframes)
    db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    resample_all()
