from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, UniqueConstraint, Enum
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()

class WatchlistType(enum.Enum):
    ATH = 'ATH'
    W52H = '52WH'

class Timeframe(enum.Enum):
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'

class Status(enum.Enum):
    INSIDE = 'INSIDE'
    OUTSIDE = 'OUTSIDE'

class Transition(enum.Enum):
    ENTRY = 'ENTRY'
    EXIT = 'EXIT'

class Symbol(Base):
    __tablename__ = 'symbols'
    id = Column(Integer, primary_key=True)
    ticker = Column(String, unique=True, nullable=False)
    name = Column(String)
    sector = Column(String)
    is_active = Column(Boolean, default=True)
    thin_history = Column(Boolean, default=False)
    deactivated_date = Column(Date, nullable=True)

class Benchmark(Base):
    __tablename__ = 'benchmarks'
    id = Column(Integer, primary_key=True)
    ticker = Column(String, unique=True, nullable=False)
    name = Column(String)

def create_price_table(timeframe: str):
    return type(f'Prices{timeframe.capitalize()}', (Base,), {
        '__tablename__': f'prices_{timeframe}',
        'symbol_id': Column(Integer, ForeignKey('symbols.id'), primary_key=True),
        'date': Column(Date, primary_key=True),
        'open': Column(Float),
        'high': Column(Float),
        'low': Column(Float),
        'close': Column(Float),
        'volume': Column(Integer),
        'adj_close': Column(Float),
    })

def create_ratio_table(timeframe: str):
    return type(f'Ratios{timeframe.capitalize()}', (Base,), {
        '__tablename__': f'ratios_{timeframe}',
        'symbol_id': Column(Integer, ForeignKey('symbols.id'), primary_key=True),
        'benchmark_id': Column(Integer, ForeignKey('benchmarks.id'), primary_key=True),
        'date': Column(Date, primary_key=True),
        'ratio': Column(Float),
    })

def create_indicator_table(timeframe: str):
    return type(f'Indicators{timeframe.capitalize()}', (Base,), {
        '__tablename__': f'indicators_{timeframe}',
        'symbol_id': Column(Integer, ForeignKey('symbols.id'), primary_key=True),
        'benchmark_id': Column(Integer, ForeignKey('benchmarks.id'), primary_key=True),
        'date': Column(Date, primary_key=True),
        'rsi': Column(Float),
        'ema21': Column(Float),
        'ema_distance_pct': Column(Float),
    })

def create_level_table(timeframe: str):
    return type(f'Levels{timeframe.capitalize()}', (Base,), {
        '__tablename__': f'levels_{timeframe}',
        'symbol_id': Column(Integer, ForeignKey('symbols.id'), primary_key=True),
        'benchmark_id': Column(Integer, ForeignKey('benchmarks.id'), primary_key=True),
        'date': Column(Date, primary_key=True),
        'ath': Column(Float),
        'high_52wh': Column(Float),
        'distance_to_ath_pct': Column(Float),
        'rs_strength_pct': Column(Float),
    })

def create_ranking_table(timeframe: str):
    return type(f'Rankings{timeframe.capitalize()}', (Base,), {
        '__tablename__': f'rankings_{timeframe}',
        'symbol_id': Column(Integer, ForeignKey('symbols.id'), primary_key=True),
        'benchmark_id': Column(Integer, ForeignKey('benchmarks.id'), primary_key=True),
        'date': Column(Date, primary_key=True),
        'rs_strength_pct': Column(Float),
        'percentile_rank': Column(Float),
    })

# Instantiate timeframe tables
PricesDaily = create_price_table('daily')
PricesWeekly = create_price_table('weekly')
PricesMonthly = create_price_table('monthly')

RatiosDaily = create_ratio_table('daily')
RatiosWeekly = create_ratio_table('weekly')
RatiosMonthly = create_ratio_table('monthly')

IndicatorsDaily = create_indicator_table('daily')
IndicatorsWeekly = create_indicator_table('weekly')
IndicatorsMonthly = create_indicator_table('monthly')

LevelsDaily = create_level_table('daily')
LevelsWeekly = create_level_table('weekly')
LevelsMonthly = create_level_table('monthly')

RankingsDaily = create_ranking_table('daily')
RankingsWeekly = create_ranking_table('weekly')
RankingsMonthly = create_ranking_table('monthly')

class WatchlistMembership(Base):
    __tablename__ = 'watchlist_memberships'
    id = Column(Integer, primary_key=True)
    symbol_id = Column(Integer, ForeignKey('symbols.id'))
    benchmark_id = Column(Integer, ForeignKey('benchmarks.id'))
    watchlist_type = Column(Enum(WatchlistType))
    timeframe = Column(Enum(Timeframe))
    status = Column(Enum(Status))
    entry_timestamp = Column(Date, nullable=True)
    exit_timestamp = Column(Date, nullable=True)
    last_evaluated_date = Column(Date)
    
    __table_args__ = (
        UniqueConstraint('symbol_id', 'benchmark_id', 'watchlist_type', 'timeframe', name='uix_membership'),
    )

class AlertSent(Base):
    __tablename__ = 'alerts_sent'
    id = Column(Integer, primary_key=True)
    symbol_id = Column(Integer, ForeignKey('symbols.id'))
    benchmark_id = Column(Integer, ForeignKey('benchmarks.id'))
    watchlist_type = Column(Enum(WatchlistType))
    timeframe = Column(Enum(Timeframe))
    transition = Column(Enum(Transition))
    alert_date = Column(Date)
    sent_timestamp = Column(DateTime)
    failed = Column(Boolean, default=False)

class SystemState(Base):
    __tablename__ = 'system_state'
    key = Column(String, primary_key=True)
    value = Column(String)

class ScanSnapshot(Base):
    __tablename__ = 'scan_snapshots'
    id = Column(Integer, primary_key=True)
    snapshot_date = Column(Date)
    symbol_id = Column(Integer, ForeignKey('symbols.id'))
    benchmark_id = Column(Integer, ForeignKey('benchmarks.id'))
    timeframe = Column(Enum(Timeframe))
    watchlist_type = Column(Enum(WatchlistType))
    status = Column(Enum(Status))
    rs_strength_pct = Column(Float)
    distance_to_ath_pct = Column(Float)
    percentile_rank = Column(Float)
    rsi = Column(Float)
    ema_distance_pct = Column(Float)
