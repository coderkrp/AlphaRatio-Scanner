from sqlalchemy.orm import Session
from src.models import Symbol, LevelsDaily, LevelsWeekly, LevelsMonthly, WatchlistMembership, WatchlistType, Timeframe, Status
from src.database import SessionLocal
import logging

logger = logging.getLogger(__name__)

def evaluate_watchlist_for_timeframe(db: Session, timeframe: Timeframe):
    # Map timeframe to levels model
    models = {
        Timeframe.DAILY: LevelsDaily,
        Timeframe.WEEKLY: LevelsWeekly,
        Timeframe.MONTHLY: LevelsMonthly
    }
    LevelModel = models[timeframe]
    
    # Get the latest date for this timeframe
    latest_date = db.query(LevelModel.date).order_by(LevelModel.date.desc()).first()
    if not latest_date: return
    latest_date = latest_date[0]
    
    # Get all levels for the latest date
    levels = db.query(LevelModel).filter(LevelModel.date == latest_date).all()
    
    for lvl in levels:
        # Check ATH Watchlist
        membership_ath = db.query(WatchlistMembership).filter(
            WatchlistMembership.symbol_id == lvl.symbol_id,
            WatchlistMembership.benchmark_id == lvl.benchmark_id,
            WatchlistMembership.watchlist_type == WatchlistType.ATH,
            WatchlistMembership.timeframe == timeframe
        ).first()
        
        if not membership_ath:
            membership_ath = WatchlistMembership(
                symbol_id=lvl.symbol_id,
                benchmark_id=lvl.benchmark_id,
                watchlist_type=WatchlistType.ATH,
                timeframe=timeframe,
                status=Status.OUTSIDE,
                last_evaluated_date=latest_date
            )
            db.add(membership_ath)
            db.flush()
            
        # Entry: distance_to_ath_pct <= 1
        # Exit: distance_to_ath_pct > 3
        if membership_ath.status == Status.OUTSIDE:
            if lvl.distance_to_ath_pct <= 1:
                membership_ath.status = Status.INSIDE
                membership_ath.entry_timestamp = latest_date
                membership_ath.exit_timestamp = None
                logger.info(f"Entry: {lvl.symbol_id} into ATH {timeframe.value} watchlist")
        else: # Status.INSIDE
            if lvl.distance_to_ath_pct > 3:
                membership_ath.status = Status.OUTSIDE
                membership_ath.exit_timestamp = latest_date
                logger.info(f"Exit: {lvl.symbol_id} from ATH {timeframe.value} watchlist")
        
        membership_ath.last_evaluated_date = latest_date
        
        # Check 52WH Watchlist
        membership_52wh = db.query(WatchlistMembership).filter(
            WatchlistMembership.symbol_id == lvl.symbol_id,
            WatchlistMembership.benchmark_id == lvl.benchmark_id,
            WatchlistMembership.watchlist_type == WatchlistType.W52H,
            WatchlistMembership.timeframe == timeframe
        ).first()
        
        if not membership_52wh:
            membership_52wh = WatchlistMembership(
                symbol_id=lvl.symbol_id,
                benchmark_id=lvl.benchmark_id,
                watchlist_type=WatchlistType.W52H,
                timeframe=timeframe,
                status=Status.OUTSIDE,
                last_evaluated_date=latest_date
            )
            db.add(membership_52wh)
            db.flush()
            
        # Entry: rs_strength_pct >= -1
        # Exit: rs_strength_pct < -3
        if membership_52wh.status == Status.OUTSIDE:
            if lvl.rs_strength_pct >= -1:
                membership_52wh.status = Status.INSIDE
                membership_52wh.entry_timestamp = latest_date
                membership_52wh.exit_timestamp = None
                logger.info(f"Entry: {lvl.symbol_id} into 52WH {timeframe.value} watchlist")
        else: # Status.INSIDE
            if lvl.rs_strength_pct < -3:
                membership_52wh.status = Status.OUTSIDE
                membership_52wh.exit_timestamp = latest_date
                logger.info(f"Exit: {lvl.symbol_id} from 52WH {timeframe.value} watchlist")
                
        membership_52wh.last_evaluated_date = latest_date
        
    db.commit()

def generate_initial_watchlists(timeframes: list[Timeframe] = None):
    if timeframes is None:
        timeframes = [Timeframe.DAILY, Timeframe.WEEKLY, Timeframe.MONTHLY]
    db = SessionLocal()
    for tf in timeframes:
        logger.info(f"Evaluating watchlists for {tf.value}...")
        evaluate_watchlist_for_timeframe(db, tf)
    db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_initial_watchlists()
