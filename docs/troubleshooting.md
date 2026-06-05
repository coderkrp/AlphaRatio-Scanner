# Troubleshooting Guide

This document covers common issues you might encounter while deploying or running AlphaRatio Scanner, and how to resolve them.

## 1. Telegram Alerts Not Arriving

**Symptoms:** The pipeline runs successfully (no errors in logs), but you receive no Telegram message.
**Causes & Solutions:**
- **Wrong Chat ID**: If your chat ID starts with a `-` (which is common for groups/channels), ensure you wrap it in quotes in the `config.yaml` to prevent the YAML parser from interpreting it as a mathematical subtraction or negative integer improperly.
- **Bot Not Initialized**: You must start a conversation with your bot first. Search for your bot in Telegram and click "Start", otherwise the Telegram API blocks the bot from initiating the conversation to prevent spam.
- **Hysteresis Threshold**: If a stock is sitting at 94.5% RS, it hasn't crossed the 95% threshold yet. No alert is generated unless a state transition occurs.

## 2. "Database is Locked" Error (SQLite)

**Symptoms:** `sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) database is locked`
**Causes & Solutions:**
- **Concurrent Writes**: SQLite locks the entire database file during a write transaction. If you try to run `main.py` and `scripts/import_ohlc_csv.py` at the exact same time, one will fail. 
- **Solution**: AlphaRatio handles DB connections with a `timeout=30` argument, which usually mitigates this. Ensure you aren't trying to run multiple parallel backtesting scripts against the same `ratio_scanner.db` file.

## 3. Data Fetching Failures (yfinance)

**Symptoms:** `ERROR: Critical: Failed to fetch benchmark ^NSEI`
**Causes & Solutions:**
- **Rate Limiting (HTTP 429)**: Yahoo Finance temporary blocks IP addresses that spam requests. The pipeline has built-in backoff, but if you are running it on a shared VPN/VPS with other active trading bots, you might get blocked.
- **Symbol Restrictions (Period 'max' is invalid)**: Certain indices (e.g., `^CNXSC`) are restricted by Yahoo and do not allow `period='max'`. This causes seeding to fail for those symbols.
- **Solution**: Manually import the historical data using `scripts/import_ohlc_csv.py` from a reliable CSV source like TradingView.
- **Delisted/Symbol Changes**: Ensure the `.NS` or `.BO` suffix is correct for Indian equities.

## 4. Pipeline Not Running via Cron

...

## 6. Configuration Parsing Errors (UTF-8 BOM)

**Symptoms:** Newly added benchmarks or symbols in `config.yaml` are completely ignored by the scanner, even though they appear correctly in the text file.
**Causes & Solutions:**
- **Byte Order Mark (BOM)**: Some Windows-based text editors save UTF-8 files with a hidden Byte Order Mark (BOM) at the start. Standard YAML loaders may fail to recognize the first key (e.g., reading `ï»¿benchmarks` instead of `benchmarks`).
- **Solution**: The scanner's `config_loader.py` is now equipped with `encoding='utf-8-sig'` to handle this. If you are using a custom loader, ensure it supports BOM-aware UTF-8 reading.

**Symptoms:** The scanner runs fine manually (`uv run main.py`), but nothing happens at the scheduled time.
**Causes & Solutions:**
- **Path Issues**: Cron runs in a highly restricted shell environment without your usual `$PATH` or aliases. 
- **Solution**: Use absolute paths for everything in your crontab. Always use `cd /absolute/path/to/repo` before invoking the Python binary. Ensure you export `PYTHONPATH=.` in the cron command.

## 5. Corrupted Ratios (Corporate Actions)

**Symptoms:** A stock suddenly shows a massive drop (e.g., -50%) in its ratio, triggering a false exit alert.
**Causes & Solutions:**
- **Stock Split / Bonus Issue**: If a stock splits 2-for-1, the price halves. Yahoo Finance adjusts historical prices, but if the scanner uses old cached absolute prices, the ratio calculation will break.
- **Solution**: The `Smart Invalidation` layer in the ingestion stage compares the *previously saved* `Adj Close` for yesterday against the *newly fetched* `Adj Close`. If they differ significantly, the system automatically drops the history for that symbol and re-fetches it to synchronize with the post-split prices. If this fails, run `scripts/import_ohlc_csv.py` with a fresh TradingView export to overwrite the broken data.
