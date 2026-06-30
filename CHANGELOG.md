# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **Telegram Alert Formatting**: Upgraded Telegram alerts from Markdown to HTML parse mode. Messages now feature bold headers, italicized counts, and monospaced (`<pre>`) tabular data to ensure perfect columnar alignment across both desktop and mobile screens without distortion. Label lengths were condensed to optimize for smaller smartphone displays.

## [1.0.0] - 2026-05-18

### Added
- **Public Open-Source Release**: Transitioned from a private personal trading script to a production-ready public repository.
- **Multi-Benchmark Support**: Refactored the core engine to support comparing a single symbol against multiple benchmarks (e.g., NIFTY50 and Sector Index) concurrently.
- **Smart Invalidation Engine**: The data ingestion layer now detects corporate actions (splits, dividends) and automatically invalidates and backfills historical data to prevent corrupted ratio calculations.
- **Configuration Driven Workflow**: Replaced hardcoded symbols and rules with a clean `config.yaml` architecture.
- **Telegram Alert Hysteresis**: Added a hysteresis buffer to the watchlist engine to drastically reduce whipsaw alerts when a stock hovers near the 95% threshold.
- **Vectorized Math**: Rewrote indicator and ratio engines to utilize `pandas` vectorization instead of slow row-by-row iteration. Daily runtime reduced from 4 minutes to <30 seconds for 500 symbols.
- **Docker Support**: Added `Dockerfile` and `docker-compose.yml` for isolated deployments.
- **Comprehensive Documentation**: Added architectural diagrams, setup guides, and engineering tradeoff explanations.
- **Auto-Config Sync on Import**: Automated configuration synchronization (`sync_config()`) directly within `scripts/import_ohlc_csv.py` to seamlessly handle manual fallback data ingestion.

### Changed
- **Smart History Fetching**: Upgraded `main.py` Data Ingestion to dynamically pull full history for new configuration entries while maintaining incremental updates for existing records.

### Fixed
- **UTF-8 BOM Support**: Fixed an issue in `config_loader.py` where configuration files saved with a Byte Order Mark (BOM) would have their root keys ignored.

## [0.9.0] - 2026-02-15 (Private MVP)

### Added
- Initial private script for calculating Relative Strength (RS) against NIFTY50.
- SQLite database integration using SQLAlchemy.
- Basic Cron job setup.
- Basic Telegram messaging integration.

### Fixed
- Addressed Yahoo Finance API rate limits by implementing batch downloading and random jitters.
