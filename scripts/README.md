# Scripts Directory

This directory contains utility scripts that are separate from the main daily pipeline execution of AlphaRatio Scanner. These tools help manage the database, backfill data, and patch missing or incorrect OHLCV prices.

## Available Scripts

### `seed_database.py`
This script is used to perform the initial bulk ingestion of historical data. It reads your `config.yaml`, queries Yahoo Finance for the maximum available history for each symbol and benchmark, and seeds the SQLite database.
**Usage:**
```bash
uv run scripts/seed_database.py
```

### `import_ohlc_csv.py`
A fallback utility script used to patch or bulk-load data for a specific ticker directly from a CSV file (e.g., exported from TradingView). This is highly useful for indices or stocks where Yahoo Finance data is unreliable, incomplete, or corrupted due to corporate actions.
**Usage:**
```bash
uv run scripts/import_ohlc_csv.py --symbol <TICKER> --csv path/to/data.csv
```

### `backfill_missing.py`
A script to identify and fetch missing data points in the database. Instead of a full initialization, this sweeps the database for any symbols that have gaps in their daily prices and attempts to fill them using Yahoo Finance.
**Usage:**
```bash
uv run scripts/backfill_missing.py
```

## Running Scripts Properly
Always run scripts from the project root directory (where `pyproject.toml` and `config.yaml` are located) to ensure the Python Path and Configuration Loader can find the required modules.

Example:
```bash
# Correct
cd /path/to/ratio-scanner
uv run scripts/seed_database.py

# Incorrect
cd /path/to/ratio-scanner/scripts
uv run seed_database.py
```
