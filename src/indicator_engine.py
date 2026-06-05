from sqlalchemy import func
import pandas as pd
import pandas_ta as ta
from sqlalchemy.orm import Session
from src.models import RatiosDaily, RatiosWeekly, RatiosMonthly, IndicatorsDaily, IndicatorsWeekly, IndicatorsMonthly, Timeframe
from src.database import SessionLocal
import logging

logger = logging.getLogger(__name__)

def compute_indicators_for_timeframe(db: Session, timeframe: Timeframe):
    # Map timeframe to models
    models = {
        Timeframe.DAILY: (RatiosDaily, IndicatorsDaily),
        Timeframe.WEEKLY: (RatiosWeekly, IndicatorsWeekly),
        Timeframe.MONTHLY: (RatiosMonthly, IndicatorsMonthly)
    }
    RatioModel, IndicatorModel = models[timeframe]
    
    # Get all unique (symbol_id, benchmark_id) pairs from Ratios
    pairs = db.query(RatioModel.symbol_id, RatioModel.benchmark_id).distinct().all()
    
    for s_id, b_id in pairs:
        # Find the last date already processed in Indicators
        max_date = db.query(func.max(IndicatorModel.date)).filter(
            IndicatorModel.symbol_id == s_id,
            IndicatorModel.benchmark_id == b_id
        ).scalar()
        
        if max_date:
            # Incremental mode: fetch enough history to warm up EMA/RSI (100 periods)
            # Find the date 150 records before max_date to be safe, or just use a subquery
            subquery = db.query(RatioModel.date).filter(
                RatioModel.symbol_id == s_id,
                RatioModel.benchmark_id == b_id,
                RatioModel.date <= max_date
            ).order_by(RatioModel.date.desc()).limit(100).subquery()
            
            min_date = db.query(func.min(subquery.c.date)).scalar()
            
            query = db.query(RatioModel).filter(
                RatioModel.symbol_id == s_id,
                RatioModel.benchmark_id == b_id,
                RatioModel.date >= min_date
            ).order_by(RatioModel.date.asc())
        else:
            # Full recalculation
            query = db.query(RatioModel).filter(
                RatioModel.symbol_id == s_id,
                RatioModel.benchmark_id == b_id
            ).order_by(RatioModel.date.asc())
        
        df = pd.read_sql(query.statement, db.bind)
        if df.empty: continue
        
        if len(df) < 21:
            logger.info(f"Skipping indicators for symbol_id {s_id} vs benchmark_id {b_id} ({timeframe.value}): insufficient history ({len(df)} points)")
            continue
        
        # Calculate RSI (default 14)
        df['rsi'] = ta.rsi(df['ratio'], length=14)
        
        # Calculate EMA (default 21)
        df['ema21'] = ta.ema(df['ratio'], length=21)
        
        # Calculate EMA distance %
        df['ema_distance_pct'] = ((df['ratio'] - df['ema21']) / df['ema21']) * 100
        
        # Filter for non-null rows
        df.dropna(subset=['rsi', 'ema21'], inplace=True)
        
        # If incremental, only keep rows after max_date
        if max_date:
            df = df[df['date'] > max_date]
        
        if not df.empty:
            # Ensure identifiers are present for bulk insert
            df['symbol_id'] = s_id
            df['benchmark_id'] = b_id
            
            # Prepare records for bulk insert
            records = df.to_dict(orient='records')
            db.bulk_insert_mappings(IndicatorModel, records)
            db.commit()
            logger.info(f"Computed {len(records)} new {timeframe.value} indicators for symbol_id {s_id} vs benchmark_id {b_id}")
        else:
            logger.info(f"No new {timeframe.value} indicators for symbol_id {s_id} vs benchmark_id {b_id}")

def compute_all_indicators(timeframes: list[Timeframe] = None):
    if timeframes is None:
        timeframes = [Timeframe.DAILY, Timeframe.WEEKLY, Timeframe.MONTHLY]
    db = SessionLocal()
    for tf in timeframes:
        logger.info(f"Computing indicators for {tf.value}...")
        compute_indicators_for_timeframe(db, tf)
    db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    compute_all_indicators()
