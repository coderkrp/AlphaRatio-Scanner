# AlphaRatio Scanner Roadmap

This document outlines the strategic vision and upcoming features for the AlphaRatio Scanner. We organize our roadmap by broad themes rather than strict timelines.

## Phase 1: Stability & Developer Experience (Current)
- [x] Refactor core engines to stateless, functional architecture
- [x] Implement YAML-based configuration
- [x] Standardize multi-timeframe resampling
- [x] Open-source release and documentation polish
- [ ] Implement `pydantic` for strict `config.yaml` validation on startup

## Phase 2: Observability & Performance (Next)
- **Metrics & Logging**: Integrate structured JSON logging (e.g., `structlog`) to enable easy parsing by tools like Datadog or ELK.
- **Profiling Suite**: Add memory profiling scripts (`memory_profiler`) to ensure Pandas DataFrames don't leak RAM during long-running backfills.
- **Benchmarking Suite**: Introduce automated benchmarking using `pytest-benchmark` to ensure new PRs do not degrade the vectorization performance of the engines.

## Phase 3: APIs and Dashboards
- **FastAPI Layer**: Expose the SQLite database state via a REST API.
  - `/api/v1/symbols`
  - `/api/v1/rankings?benchmark=^NSEI&timeframe=daily`
- **React Frontend**: Build a lightweight, local-first dashboard to visualize ratio charts and scanner results, reducing dependency on Telegram.
- **Websocket Streaming**: (Research Phase) Transition from EOD batch processing to intraday streaming by listening to broker websocket feeds (e.g., Zerodha Kite Connect, Upstox) and updating the DB in near real-time.

## Phase 4: Advanced Quant Capabilities
- **Plugin Architecture**: Allow users to dynamically load `.py` scripts containing custom technical indicators without altering the core engine codebase.
- **Backtesting Module**: Build a vectorized backtester that can ingest historical ranking states and output standard performance metrics (Sharpe, Sortino, Max Drawdown).
- **Statistical Arbitrage Flags**: Detect abnormal standard deviation divergences in sector peer ratios.
