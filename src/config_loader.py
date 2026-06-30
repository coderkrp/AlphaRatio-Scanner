import yaml
from sqlalchemy.orm import Session
from src.models import Symbol, Benchmark
import os
from src.config import load_and_validate
from src.config.models import FullConfig

def load_config(config_path="config.yaml") -> FullConfig:
    return load_and_validate(config_path)

def sync_config(db: Session, config: FullConfig):
    # Sync Benchmarks
    for b_data in config.benchmarks:
        benchmark = db.query(Benchmark).filter(Benchmark.ticker == b_data.ticker).first()
        if not benchmark:
            benchmark = Benchmark(ticker=b_data.ticker, name=b_data.name)
            db.add(benchmark)
        else:
            benchmark.name = b_data.name
    
    # Sync Symbols
    # Also include benchmarks in symbols table for price storage
    all_tickers_in_config = [s.ticker for s in config.symbols] + [b.ticker for b in config.benchmarks]
    
    # Mark symbols not in config as inactive
    db.query(Symbol).filter(Symbol.ticker.notin_(all_tickers_in_config)).update({Symbol.is_active: False})
    
    # Process symbols
    for s_data in config.symbols:
        symbol = db.query(Symbol).filter(Symbol.ticker == s_data.ticker).first()
        if not symbol:
            symbol = Symbol(
                ticker=s_data.ticker,
                name=s_data.name,
                sector=s_data.sector,
                is_active=True
            )
            db.add(symbol)
        else:
            symbol.name = s_data.name
            symbol.sector = s_data.sector
            symbol.is_active = True
            
    # Process benchmarks as symbols
    for b_data in config.benchmarks:
        symbol = db.query(Symbol).filter(Symbol.ticker == b_data.ticker).first()
        if not symbol:
            symbol = Symbol(
                ticker=b_data.ticker,
                name=b_data.name,
                is_active=True
            )
            db.add(symbol)
        else:
            symbol.is_active = True
    
    db.commit()

