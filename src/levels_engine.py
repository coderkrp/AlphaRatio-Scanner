from sqlalchemy import func
import pandas as pd
from sqlalchemy.orm import Session
from src.models import RatiosDaily, RatiosWeekly, RatiosMonthly, LevelsDaily, LevelsWeekly, LevelsMonthly, Timeframe
from src.database import SessionLocal
import logging

logger = logging.getLogger(__name__)

def compute_levels_for_timeframe(db: Session, timeframe: Timeframe):
    # Map timeframe to models
    models = {
        Timeframe.DAILY: (RatiosDaily, LevelsDaily, 252),
        Timeframe.WEEKLY: (RatiosWeekly, LevelsWeekly, 52),
        Timeframe.MONTHLY: (RatiosMonthly, LevelsMonthly, 12)
    }
    RatioModel, LevelModel, window = models[timeframe]
    
    pairs = db.query(RatioModel.symbol_id, RatioModel.benchmark_id).distinct().all()
    
    for s_id, b_id in pairs:
        # Find the last date already processed in Levels
        max_date = db.query(func.max(LevelModel.date)).filter(
            LevelModel.symbol_id == s_id,
            LevelModel.benchmark_id == b_id
        ).scalar()
        
        if max_date:
            # Fetch enough history to warm up rolling window (window size + buffer)
            subquery = db.query(RatioModel.date).filter(
                RatioModel.symbol_id == s_id,
                RatioModel.benchmark_id == b_id,
                RatioModel.date <= max_date
            ).order_by(RatioModel.date.desc()).limit(window + 50).subquery()
            
            min_date = db.query(func.min(subquery.c.date)).scalar()
            
            query = db.query(RatioModel).filter(
                RatioModel.symbol_id == s_id,
                RatioModel.benchmark_id == b_id,
                RatioModel.date >= min_date
            ).order_by(RatioModel.date.asc())
        else:
            query = db.query(RatioModel).filter(
                RatioModel.symbol_id == s_id,
                RatioModel.benchmark_id == b_id
            ).order_by(RatioModel.date.asc())
        
        df = pd.read_sql(query.statement, db.bind)
        if df.empty: continue
        
        # ATH Calculation (excluding current candle)
        df['ath'] = df['ratio'].expanding().max().shift(1)
        
        # 52WH Calculation (excluding current candle, rolling window)
        df['high_52wh'] = df['ratio'].rolling(window=window).max().shift(1)
        
        # Distances
        df['rs_strength_pct'] = ((df['ratio'] - df['high_52wh']) / df['high_52wh']) * 100
        df['distance_to_ath_pct'] = ((df['ath'] - df['ratio']) / df['ath']) * 100
        
        # Drop rows where we don't have enough history
        df.dropna(subset=['ath', 'high_52wh'], inplace=True)
        
        # If incremental, only keep rows after max_date
        if max_date:
            df = df[df['date'] > max_date]
            
        if not df.empty:
            df['symbol_id'] = s_id
            df['benchmark_id'] = b_id
            # Ensure date is date object for consistent SQLite storage
            df['date'] = pd.to_datetime(df['date']).dt.date
            
            records = df[['symbol_id', 'benchmark_id', 'date', 'ath', 'high_52wh', 'distance_to_ath_pct', 'rs_strength_pct']].to_dict(orient='records')
            db.bulk_insert_mappings(LevelModel, records)
            db.commit()
            logger.info(f"Computed {len(records)} new levels for symbol_id {s_id} vs benchmark_id {b_id} ({timeframe.value})")

def compute_all_levels(timeframes: list[Timeframe] = None):
    if timeframes is None:
        timeframes = [Timeframe.DAILY, Timeframe.WEEKLY, Timeframe.MONTHLY]
    db = SessionLocal()
    for tf in timeframes:
        logger.info(f"Computing levels for {tf.value}...")
        compute_levels_for_timeframe(db, tf)
    db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    compute_all_levels()
