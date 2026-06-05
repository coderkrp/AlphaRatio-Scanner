from sqlalchemy import func
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from src.models import LevelsDaily, LevelsWeekly, LevelsMonthly, RankingsDaily, RankingsWeekly, RankingsMonthly, Timeframe, Symbol
from src.database import SessionLocal
import logging

logger = logging.getLogger(__name__)

def compute_rankings_for_timeframe(db: Session, timeframe: Timeframe):
    # Map timeframe to models
    models = {
        Timeframe.DAILY: (LevelsDaily, RankingsDaily),
        Timeframe.WEEKLY: (LevelsWeekly, RankingsWeekly),
        Timeframe.MONTHLY: (LevelsMonthly, RankingsMonthly)
    }
    LevelModel, RankingModel = models[timeframe]
    
    # Rankings are benchmark-scoped. Get all benchmarks.
    benchmarks = db.query(LevelModel.benchmark_id).distinct().all()
    
    for (b_id,) in benchmarks:
        # Find the last date already processed in Rankings for this benchmark
        max_date = db.query(func.max(RankingModel.date)).filter(
            RankingModel.benchmark_id == b_id
        ).scalar()
        
        # Get all dates present for this benchmark in levels after max_date
        query = db.query(LevelModel.date).filter(LevelModel.benchmark_id == b_id)
        if max_date:
            query = query.filter(LevelModel.date > max_date)
        
        dates = query.distinct().order_by(LevelModel.date.asc()).all()
        
        if not dates:
            logger.debug(f"No new rankings for benchmark_id {b_id} ({timeframe.value})")
            continue
            
        for (date,) in dates:
            # Get all levels for this benchmark and date
            query = db.query(LevelModel).filter(
                LevelModel.benchmark_id == b_id,
                LevelModel.date == date
            )
            df = pd.read_sql(query.statement, db.bind)
            if df.empty: continue
            
            # Compute percentile rank based on rs_strength_pct
            df['percentile_rank'] = df['rs_strength_pct'].rank(pct=True) * 100
            
            # Ensure date is date object and replace NaNs with None for SQLite
            df['date'] = pd.to_datetime(df['date']).dt.date
            df = df.replace({np.nan: None})

            # Prepare records for bulk insert
            records = df[['symbol_id', 'benchmark_id', 'date', 'rs_strength_pct', 'percentile_rank']].to_dict(orient='records')
            
            db.bulk_insert_mappings(RankingModel, records)
            db.commit()
            logger.info(f"Inserted {len(records)} rankings for benchmark_id {b_id} on {date} ({timeframe.value})")

def compute_all_rankings(timeframes: list[Timeframe] = None):
    if timeframes is None:
        timeframes = [Timeframe.DAILY, Timeframe.WEEKLY, Timeframe.MONTHLY]
    db = SessionLocal()
    for tf in timeframes:
        logger.info(f"Computing rankings for {tf.value}...")
        compute_rankings_for_timeframe(db, tf)
    db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    compute_all_rankings()
