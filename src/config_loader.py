import yaml
from sqlalchemy.orm import Session
from src.models import Symbol, Benchmark
import os

def load_config(config_path="config.yaml"):
    with open(config_path, 'r', encoding='utf-8-sig') as f:
        return yaml.safe_load(f)

def sync_config(db: Session, config: dict):
    # Sync Benchmarks
    config_benchmarks = config.get('benchmarks', [])
    for b_data in config_benchmarks:
        benchmark = db.query(Benchmark).filter(Benchmark.ticker == b_data['ticker']).first()
        if not benchmark:
            benchmark = Benchmark(ticker=b_data['ticker'], name=b_data['name'])
            db.add(benchmark)
        else:
            benchmark.name = b_data['name']
    
    # Sync Symbols
    config_symbols = config.get('symbols', [])
    # Also include benchmarks in symbols table for price storage
    all_tickers_in_config = [s['ticker'] for s in config_symbols] + [b['ticker'] for b in config_benchmarks]
    
    # Mark symbols not in config as inactive
    db.query(Symbol).filter(Symbol.ticker.notin_(all_tickers_in_config)).update({Symbol.is_active: False})
    
    # Process symbols
    for s_data in config_symbols:
        symbol = db.query(Symbol).filter(Symbol.ticker == s_data['ticker']).first()
        if not symbol:
            symbol = Symbol(
                ticker=s_data['ticker'],
                name=s_data['name'],
                sector=s_data['sector'],
                is_active=True
            )
            db.add(symbol)
        else:
            symbol.name = s_data['name']
            symbol.sector = s_data['sector']
            symbol.is_active = True
            
    # Process benchmarks as symbols
    for b_data in config_benchmarks:
        symbol = db.query(Symbol).filter(Symbol.ticker == b_data['ticker']).first()
        if not symbol:
            symbol = Symbol(
                ticker=b_data['ticker'],
                name=b_data['name'],
                is_active=True
            )
            db.add(symbol)
        else:
            symbol.is_active = True
    
    db.commit()
