from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional

class TelegramConfig(BaseModel):
    token: Optional[str] = None
    chat_id: List[str] = Field(default_factory=list)

    @field_validator("chat_id", mode="before")
    @classmethod
    def normalize_chat_id(cls, v):
        if isinstance(v, list):
            return [str(item) for item in v]
        if v is not None:
            return [str(v)]
        return []

class DatabaseConfig(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def validate_db_url(cls, v):
        if not v.startswith("sqlite://"):
            raise ValueError("Database URL must start with 'sqlite://'")
        return v

class BenchmarkEntry(BaseModel):
    ticker: str
    name: str

    @field_validator("ticker", "name")
    @classmethod
    def non_empty_str(cls, v):
        if not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

class SymbolEntry(BaseModel):
    ticker: str
    name: str
    sector: str
    benchmarks: List[str]

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v):
        if not v.endswith(".NS"):
            raise ValueError("Symbol tickers must end with '.NS'")
        return v

    @field_validator("name", "sector")
    @classmethod
    def non_empty_str(cls, v):
        if not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

class FullConfig(BaseModel):
    telegram: Optional[TelegramConfig] = None
    database: DatabaseConfig
    benchmarks: List[BenchmarkEntry] = Field(default_factory=list)
    symbols: List[SymbolEntry] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_config_cross_references(self) -> "FullConfig":
        if not self.symbols:
            raise ValueError("At least one symbol must be defined under 'symbols'")
        if not self.benchmarks:
            raise ValueError("At least one benchmark must be defined under 'benchmarks'")

        symbol_tickers = [s.ticker for s in self.symbols]
        benchmark_tickers = [b.ticker for b in self.benchmarks]

        if len(symbol_tickers) != len(set(symbol_tickers)):
            duplicates = {t for t in symbol_tickers if symbol_tickers.count(t) > 1}
            raise ValueError(f"Duplicate tickers found in symbols: {duplicates}")

        if len(benchmark_tickers) != len(set(benchmark_tickers)):
            duplicates = {t for t in benchmark_tickers if benchmark_tickers.count(t) > 1}
            raise ValueError(f"Duplicate tickers found in benchmarks: {duplicates}")

        # Strict benchmark resolvability check (Agreed)
        benchmark_tickers_set = set(benchmark_tickers)
        for symbol in self.symbols:
            for b_ref in symbol.benchmarks:
                if b_ref not in benchmark_tickers_set:
                    raise ValueError(
                        f"Benchmark '{b_ref}' referenced by symbol '{symbol.ticker}' "
                        f"is not defined in the top-level 'benchmarks' list."
                    )
        return self
