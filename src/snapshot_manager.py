from datetime import date, timedelta
from sqlalchemy.orm import Session
from src.models import (
    ScanSnapshot, WatchlistMembership, 
    LevelsDaily, LevelsWeekly, LevelsMonthly, 
    IndicatorsDaily, IndicatorsWeekly, IndicatorsMonthly, 
    RankingsDaily, RankingsWeekly, RankingsMonthly,
    Timeframe, WatchlistType, Status
)
# Wait, I need to use the actual model classes I instantiated in models.py

def persist_snapshots(db: Session):
    today = date.today()
    
    # Map timeframe to models
    tf_models = {
        Timeframe.DAILY: (LevelsDaily, IndicatorsDaily, RankingsDaily),
        Timeframe.WEEKLY: (LevelsWeekly, IndicatorsWeekly, RankingsWeekly),
        Timeframe.MONTHLY: (LevelsMonthly, IndicatorsMonthly, RankingsMonthly)
    }
    
    memberships = db.query(WatchlistMembership).all()
    
    for m in memberships:
        LvlModel, IndModel, RnkModel = tf_models[m.timeframe]
        
        # Get latest data for this symbol/benchmark/timeframe
        lvl = db.query(LvlModel).filter(
            LvlModel.symbol_id == m.symbol_id,
            LvlModel.benchmark_id == m.benchmark_id
        ).order_by(LvlModel.date.desc()).first()
        
        ind = db.query(IndModel).filter(
            IndModel.symbol_id == m.symbol_id,
            IndModel.benchmark_id == m.benchmark_id
        ).order_by(IndModel.date.desc()).first()
        
        rnk = db.query(RnkModel).filter(
            RnkModel.symbol_id == m.symbol_id,
            RnkModel.benchmark_id == m.benchmark_id
        ).order_by(RnkModel.date.desc()).first()
        
        if lvl:
            snapshot = ScanSnapshot(
                snapshot_date=today,
                symbol_id=m.symbol_id,
                benchmark_id=m.benchmark_id,
                timeframe=m.timeframe,
                watchlist_type=m.watchlist_type,
                status=m.status,
                rs_strength_pct=lvl.rs_strength_pct,
                distance_to_ath_pct=lvl.distance_to_ath_pct,
                percentile_rank=rnk.percentile_rank if rnk else None,
                rsi=ind.rsi if ind else None,
                ema_distance_pct=ind.ema_distance_pct if ind else None
            )
            db.add(snapshot)
            
    db.commit()

def cleanup_snapshots(db: Session):
    cutoff = date.today() - timedelta(days=365)
    db.query(ScanSnapshot).filter(ScanSnapshot.snapshot_date < cutoff).delete()
    db.commit()
