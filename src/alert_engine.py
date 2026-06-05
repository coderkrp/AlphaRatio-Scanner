import asyncio
import logging
import html
from datetime import date, datetime
from sqlalchemy.orm import Session
from src.models import (
    Symbol, Benchmark, WatchlistMembership, WatchlistType, Timeframe, Status,
    AlertSent, Transition, LevelsDaily, LevelsWeekly, LevelsMonthly,
    IndicatorsDaily, IndicatorsWeekly, IndicatorsMonthly
)
from src.database import SessionLocal
from src.telegram_bot import TelegramBot

logger = logging.getLogger(__name__)

def get_latest_metrics(db: Session, symbol_id, benchmark_id, timeframe, watchlist_type):
    # Map models
    lvl_models = {
        Timeframe.DAILY: LevelsDaily,
        Timeframe.WEEKLY: LevelsWeekly,
        Timeframe.MONTHLY: LevelsMonthly
    }
    ind_models = {
        Timeframe.DAILY: IndicatorsDaily,
        Timeframe.WEEKLY: IndicatorsWeekly,
        Timeframe.MONTHLY: IndicatorsMonthly
    }
    
    LvlModel = lvl_models[timeframe]
    IndModel = ind_models[timeframe]
    
    # Get latest date
    latest_date_res = db.query(LvlModel.date).filter(
        LvlModel.symbol_id == symbol_id,
        LvlModel.benchmark_id == benchmark_id
    ).order_by(LvlModel.date.desc()).first()
    
    if not latest_date_res: return None
    latest_date = latest_date_res[0]
    
    lvl = db.query(LvlModel).filter(
        LvlModel.symbol_id == symbol_id,
        LvlModel.benchmark_id == benchmark_id,
        LvlModel.date == latest_date
    ).first()
    
    ind = db.query(IndModel).filter(
        IndModel.symbol_id == symbol_id,
        IndModel.benchmark_id == benchmark_id,
        IndModel.date == latest_date
    ).first()
    
    return lvl, ind

async def send_watchlist_alerts(db: Session, active_timeframes: list[Timeframe] = None):
    bot = TelegramBot()
    today = date.today()
    
    # For each watchlist × benchmark combination
    combinations = db.query(
        WatchlistMembership.benchmark_id,
        WatchlistMembership.watchlist_type,
        WatchlistMembership.timeframe
    ).distinct().all()
    
    for b_id, w_type, tf in combinations:
        if active_timeframes is not None and tf not in active_timeframes:
            continue
            
        benchmark = db.query(Benchmark).get(b_id)
        
        # 1. Transition Summary
        # We need to detect entries/exits from the current run.
        # In this implementation, we assume evaluate_watchlist_for_timeframe just ran.
        # Entries are memberships where entry_timestamp == latest_evaluated_date and status == INSIDE
        # Exits are memberships where exit_timestamp == latest_evaluated_date and status == OUTSIDE
        
        latest_date = db.query(WatchlistMembership.last_evaluated_date).filter(
            WatchlistMembership.benchmark_id == b_id,
            WatchlistMembership.watchlist_type == w_type,
            WatchlistMembership.timeframe == tf
        ).order_by(WatchlistMembership.last_evaluated_date.desc()).first()
        
        if not latest_date: continue
        latest_date = latest_date[0]
        
        entries = db.query(Symbol).join(WatchlistMembership).filter(
            WatchlistMembership.benchmark_id == b_id,
            WatchlistMembership.watchlist_type == w_type,
            WatchlistMembership.timeframe == tf,
            WatchlistMembership.status == Status.INSIDE,
            WatchlistMembership.entry_timestamp == latest_date
        ).order_by(Symbol.ticker).all()
        
        exits = db.query(Symbol).join(WatchlistMembership).filter(
            WatchlistMembership.benchmark_id == b_id,
            WatchlistMembership.watchlist_type == w_type,
            WatchlistMembership.timeframe == tf,
            WatchlistMembership.status == Status.OUTSIDE,
            WatchlistMembership.exit_timestamp == latest_date
        ).order_by(Symbol.ticker).all()
        
        if entries or exits:
            summary_text = f"<b>[{tf.value.capitalize()} {w_type.value} — {html.escape(benchmark.name)}]</b>\n\n"
            if entries:
                summary_text += f"<b>▲ Entries:</b> {', '.join([s.ticker for s in entries])}\n"
            if exits:
                summary_text += f"<b>▼ Exits:</b> {', '.join([s.ticker for s in exits])}\n"
            
            # Send Summary
            success = await bot.send_message(summary_text)
            if success:
                # Log to alerts_sent
                for s in entries:
                    alert = AlertSent(symbol_id=s.id, benchmark_id=b_id, watchlist_type=w_type, timeframe=tf, transition=Transition.ENTRY, alert_date=today, sent_timestamp=datetime.now())
                    db.add(alert)
                for s in exits:
                    alert = AlertSent(symbol_id=s.id, benchmark_id=b_id, watchlist_type=w_type, timeframe=tf, transition=Transition.EXIT, alert_date=today, sent_timestamp=datetime.now())
                    db.add(alert)
                db.commit()

        # 2. Daily Digest
        # Get all symbols currently INSIDE
        members = db.query(Symbol, WatchlistMembership).join(WatchlistMembership).filter(
            WatchlistMembership.benchmark_id == b_id,
            WatchlistMembership.watchlist_type == w_type,
            WatchlistMembership.timeframe == tf,
            WatchlistMembership.status == Status.INSIDE
        ).all()
        
        # Sort as per spec
        # ATH watchlists → distance_to_ath_pct ascending
        # 52WH watchlists → rs_strength_pct descending
        
        data_list = []
        for s, m in members:
            metrics = get_latest_metrics(db, s.id, b_id, tf, w_type)
            if metrics:
                lvl, ind = metrics
                data_list.append({
                    'symbol': s,
                    'lvl': lvl,
                    'ind': ind
                })
        
        if w_type == WatchlistType.ATH:
            data_list.sort(key=lambda x: x['lvl'].distance_to_ath_pct)
        else:
            data_list.sort(key=lambda x: x['lvl'].rs_strength_pct, reverse=True)
            
        header = f"<b>[{tf.value.capitalize()} {w_type.value} — {html.escape(benchmark.name)}]</b> • <i>{len(data_list)} stocks</i>\n"
        if not data_list:
            await bot.send_message(header + "(empty)")
        else:
            lines = []
            for item in data_list:
                s = item['symbol']
                lvl = item['lvl']
                ind = item['ind']
                rsi_val = f"{ind.rsi:.0f}" if ind and ind.rsi is not None else "N/A"
                if w_type == WatchlistType.ATH:
                    metric_str = f"Dist: {lvl.distance_to_ath_pct:5.1f}%"
                else:
                    metric_str = f"Str:  {lvl.rs_strength_pct:5.1f}%"
                lines.append(f"{s.ticker:12} | RSI: {rsi_val:3} | {metric_str}")
            
            # Message splitting
            full_body = "\n".join(lines)
            if len(header + "\n<pre>" + full_body + "</pre>") <= 4096:
                await bot.send_message(header + "\n<pre>" + full_body + "</pre>")
            else:
                # Chunking logic
                chunks = []
                current_chunk = ""
                for line in lines:
                    # Estimate overhead for tags and pagination
                    if len(header + " (9/9)\n<pre>" + current_chunk + line + "\n</pre>") > 4000:
                        chunks.append(current_chunk)
                        current_chunk = line + "\n"
                    else:
                        current_chunk += line + "\n"
                chunks.append(current_chunk)
                
                for i, chunk in enumerate(chunks):
                    pagination = f" ({i+1}/{len(chunks)})"
                    await bot.send_message(f"{header.strip()}{pagination}\n<pre>{chunk.strip()}</pre>")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    db = SessionLocal()
    asyncio.run(send_watchlist_alerts(db))
    db.close()
