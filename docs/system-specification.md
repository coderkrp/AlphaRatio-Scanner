# AlphaRatio Scanner — Technical Architecture

---

# 1. System Overview

AlphaRatio Scanner is a modular Python-based end-of-day relative strength analysis platform.

The system architecture follows a layered pipeline:

```text
Data Ingestion
    ↓
Validation
    ↓
Ratio Engine
    ↓
Indicator Engine
    ↓
ATH/52WH Engine
    ↓
Ranking Engine
    ↓
Watchlist Engine
    ↓
Alert Engine
    ↓
Dashboard
```

---

# 2. Core Technology Stack

| Layer         | Technology       | Status          |
| ------------- | ---------------- | --------------- |
| Backend       | Python 3.12+     | Active (Phase 1)|
| Data Provider | yfinance         | Active (Phase 1)|
| Indicators    | pandas-ta        | Active (Phase 1)|
| Database      | SQLite           | Active (Phase 1)|
| ORM           | SQLAlchemy       | Active (Phase 1)|
| Alerts        | Telegram Bot API | Active (Phase 1)|
| Deployment    | systemd / Docker | Active (Phase 1)|
| Package Mgr   | uv               | Active (Phase 1)|
| Config        | YAML             | Active (Phase 1)|

*Frontend (Streamlit) and Charts (Plotly) are deferred to Phase 2.*

---

# 3. High-Level Architecture

## 3.1 Components

The system contains:

1. Config Loader
2. Market Data Downloader
3. Validation Engine
4. Ratio Engine
5. Indicator Engine
6. ATH/52WH Engine
7. Ranking Engine
8. Watchlist Engine
9. Alert Engine
10. Dashboard UI
11. Scheduler Service

---

# 4. Data Ingestion Layer

## 4.1 Responsibilities

Responsibilities:

* download EOD OHLC data
* fetch benchmark data
* validate downloaded candles
* persist raw prices

---

## 4.2 Initial Seed — Data Source Priority

For the initial database seed, the pipeline employs **Smart History Fetching**. The system interrogates the database for existing records; if a symbol has fewer than 60 candles (e.g., it is a new addition to `config.yaml`), it triggers a `period='max'` fetch. Otherwise, it defaults to a standard `5d` incremental update.

### yfinance Limitations
Users should note that Yahoo Finance restricts historical data for specific secondary indices (e.g., `^CNXSC`, `NIFTYSMLCAP250.NS`). For these tickers, `yfinance` typically only returns current-day or 5-day data. 

If deeper history is required (e.g., for an accurate ATH baseline or to compute indicators requiring 200+ candles), the user must supplement or override yfinance data using the CSV Import Script (see §4.3).

---

## 4.3 CSV Import Script

A standalone utility script (`scripts/import_ohlc_csv.py`) for importing historical OHLC data from Tradingview-exported CSVs into the SQLite database.

### Config-First Enforcement
To maintain data integrity and ensure the scanner ignores untracked data, the import script enforces a **Config-First** approach:
1. It validates that the target symbol ticker exists in `config.yaml`.
2. If the symbol is found in the configuration but is missing from the database schema, the script automatically triggers `sync_config()` to initialize the record before inserting price data.
3. If the symbol is missing from both the configuration and the database, the script halts and instructs the user to update `config.yaml` first.

### Expected CSV format

Tradingview default export columns (both naming conventions are handled):

```text
time, open, high, low, close, volume
Date, Open, High, Low, Close, Volume
```

### Column normalisation

The script normalises column names on load before any processing:

```python
COLUMN_MAP = {
    'time':   'date',   'Date':   'date',
    'open':   'open',   'Open':   'open',
    'high':   'high',   'High':   'high',
    'low':    'low',    'Low':    'low',
    'close':  'close',  'Close':  'close',
    'volume': 'volume', 'Volume': 'volume'
}
```

If any required column is missing after normalisation, the script aborts with a descriptive error before touching the database. No partial writes.

### Important — adjusted prices required

Tradingview CSV exports must use adjusted prices. The `close` column in the CSV is mapped to `Adj Close` in the database. Users must ensure the Tradingview export has adjustment enabled before downloading.

### Script behavior

1. Accepts arguments: `--symbol`, `--csv`, `--timeframe` (default: `daily`), `--on-conflict` (`skip` or `overwrite`, default: `overwrite`)
2. Validates CSV structure and date parsing before any writes
3. Maps the symbol to its entry in the `symbols` table — aborts if symbol not found
4. Merge strategy: inserts new rows; for overlapping dates, CSV data wins over existing yfinance data (when `--on-conflict overwrite`)
5. After writing to `prices_daily`, triggers a full recalculation cascade for the affected symbol:

```text
1. Resample         → prices_weekly, prices_monthly
2. Recompute ratios → ratios_daily, ratios_weekly, ratios_monthly (all benchmarks)
3. Recompute        → indicators_daily, indicators_weekly, indicators_monthly
4. Recompute        → levels_daily, levels_weekly, levels_monthly (ATH, 52WH)
5. Recompute        → rankings_daily, rankings_weekly, rankings_monthly
6. Recompute        → watchlist_memberships (re-evaluate full history)
7. Persist          → scan_snapshots
```

6. Recalculation is scoped to the affected symbol only
7. Prints a summary: rows inserted, rows skipped/overwritten, date range imported, recalculation status

**No alerts are sent during CSV import.** Historical watchlist membership changes are written silently — only forward-looking daily pipeline runs trigger Telegram alerts.

### Usage example

```bash
python scripts/import_ohlc_csv.py \
  --symbol RELIANCE \
  --csv ~/Downloads/RELIANCE_daily.csv \
  --timeframe daily \
  --on-conflict overwrite
```

---

## 4.4 Price Storage Policy

The system stores both `Close` and `Adj Close` in all `prices_{timeframe}` tables.

* `Adj Close` is the canonical price for all downstream calculations — ratios, indicators, levels, and rankings.
* `Close` is stored for reference purposes only and is never used in computation.

---

## 4.5 Initial Seed Procedure

The seed is a one-time script (`scripts/seed_database.py`) distinct from the daily pipeline.

### Execution order

1. Sync Config (YAML → Database)
2. For each symbol in config:
   a. Fetch full history from yfinance (period='max')
   b. If fetch fails after 3 retries — log and skip, do not abort
   c. Validate: minimum 60 candles required to proceed
      * Below threshold: log warning, insert what's available, flag symbol
   d. Insert into prices_daily
3. Resample → prices_weekly, prices_monthly for all symbols
4. Compute ratios (all benchmarks, all timeframes)
5. Compute indicators (all timeframes)
6. Compute ATH/52WH levels (all timeframes)
7. Compute rankings (all timeframes)
8. Generate initial watchlist memberships
   * All symbols start with status = 'OUTSIDE'
   * Evaluate current metric values and immediately apply entry conditions
   * No alerts are sent during seed
9. Print seed summary:
   * Total symbols attempted
   * Successfully seeded
   * Skipped (fetch failure)
   * Flagged (thin history)
   * Date range per symbol

### 60-candle minimum rationale

60 candles guarantees at least 2 monthly bars, ensuring monthly resampling, ratio computation, and indicator calculation all have meaningful data from day one.

Symbols below this threshold are seeded but flagged via a `thin_history BOOLEAN` column on the `symbols` table.

---

## 4.6 Download Frequency

Data refresh schedule:

* once daily
* approximately 30 minutes after market close

---

# 5. Validation Layer

## 5.1 Validation Goals

Validation layer should:

* detect missing candles
* detect duplicate rows
* validate benchmark availability
* validate timestamp alignment
* prevent corrupted downstream calculations

---

## 5.2 Smart Invalidation (Corporate Actions)

When a corporate action is detected (yesterday's stored `Adj Close` differs from freshly fetched `Adj Close`), the system triggers a full historical backfill for that symbol:

1. Delete all existing rows for that symbol from `prices_daily`
2. Re-fetch full history from yfinance (`period='max'`)
3. Re-insert the complete freshly-adjusted history
4. Mark symbol for full recalculation cascade (same cascade as §4.3)

The fresh yfinance history is always fully self-consistent because yfinance adjusts the entire price history retroactively on every corporate action.

**The backfill is synchronous.** It must fully complete before ratio computation begins for that symbol. See §13.2 for pipeline branching behavior.

---

## 5.3 Missing Data & Retry Logic

* **Scheduler:** If data fetching fails, retry 3 times with exponential backoff.
* **Failure Policy:** If data is still unavailable after retries (e.g., holiday or API outage), the pipeline must fail gracefully and log the error. No stale or duplicate data should be written to the database.

---

# 6. Database Design

## 6.1 Database Philosophy

The dashboard should NEVER calculate indicators dynamically.

All indicators and scanner outputs must be precomputed and persisted.

---

## 6.2 Core Tables

Tables are duplicated for `daily`, `weekly`, and `monthly` timeframes (e.g., `prices_daily`, `prices_weekly`, `prices_monthly`).

### symbols

Stores symbol metadata. **Source of Truth:** Synchronized from `config.yaml` on every run.

* `id` (PK)
* `ticker` (unique)
* `name`
* `sector`
* `is_active` (BOOLEAN DEFAULT TRUE)
* `thin_history` (BOOLEAN DEFAULT FALSE)
* `deactivated_date` (DATE nullable)

### benchmarks

Stores benchmark metadata and ticker mappings.

### prices_{timeframe}

Stores OHLCV and adjusted close data.

* `symbol_id` (FK)
* `date` (PK)
* `open`, `high`, `low`, `close`, `volume`
* `adj_close` (Canonical price for calculations)

### ratios_{timeframe}

Stores computed stock/benchmark ratios.

* `symbol_id` (FK)
* `benchmark_id` (FK)
* `date` (PK)
* `ratio`

### indicators_{timeframe}

Stores computed indicators on ratio values.

* `symbol_id` (FK)
* `benchmark_id` (FK)
* `date` (PK)
* `rsi`
* `ema21`
* `ema_distance_pct`

### levels_{timeframe}

Stores ATH and 52WH metrics.

* `symbol_id` (FK)
* `benchmark_id` (FK)
* `date` (PK)
* `ath`
* `high_52wh`
* `distance_to_ath_pct`
* `rs_strength_pct`

### rankings_{timeframe}

Stores percentile rankings. Rankings are always benchmark-scoped.

* `symbol_id` (FK)
* `benchmark_id` (FK)
* `date` (PK)
* `rs_strength_pct`
* `percentile_rank`

### watchlist_memberships

One row per `(symbol_id, benchmark_id, watchlist_type, timeframe)` combination. Updated in place.

* `id` (PK)
* `symbol_id` (FK)
* `benchmark_id` (FK)
* `watchlist_type` (ENUM: 'ATH', '52WH')
* `timeframe` (ENUM: 'daily', 'weekly', 'monthly')
* `status` (ENUM: 'INSIDE', 'OUTSIDE')
* `entry_timestamp` (DATE nullable)
* `exit_timestamp` (DATE nullable)
* `last_evaluated_date` (DATE)

### alerts_sent

Prevents duplicate alerts.

* `id` (PK)
* `symbol_id` (FK)
* `benchmark_id` (FK)
* `watchlist_type` (ENUM: 'ATH', '52WH')
* `timeframe` (ENUM: 'daily', 'weekly', 'monthly')
* `transition` (ENUM: 'ENTRY', 'EXIT')
* `alert_date` (DATE)
* `sent_timestamp` (DATETIME)
* `failed` (BOOLEAN DEFAULT FALSE)

### system_state (new)

Used to store pipeline metadata.

* `key` (TEXT PRIMARY KEY)
* `value` (TEXT)

Example: `last_successful_run` = 'YYYY-MM-DD'.

---

## 6.3 Symbol Removal Policy

When a symbol is present in the database but absent from `config.yaml`, the daily pipeline marks it inactive via `is_active = FALSE`. It is never deleted.

### Behavior for inactive symbols

* **Daily pipeline:** Skipped entirely — no download, no computation, no ranking.
* **Watchlist engine:** If `status = 'INSIDE'` at deactivation time, immediately transition to `status = 'OUTSIDE'` and write exit timestamp. No Telegram alert is sent for this transition.
* **Rankings:** Excluded from all ranking universes.
* **Reactivation:** If a symbol reappears in `config.yaml`, `is_active` is flipped back to `TRUE`. The daily pipeline resumes incremental updates. No historical backfill is triggered automatically.

---

## 6.4 scan_snapshots

`scan_snapshots` is an append-only audit log storing a daily point-in-time record of every symbol's scanner output.

### Schema

* `id` (PK)
* `snapshot_date` (DATE)
* `symbol_id` (FK)
* `benchmark_id` (FK)
* `timeframe` (ENUM)
* `watchlist_type` (ENUM)
* `status` (ENUM)
* `rs_strength_pct` (FLOAT)
* `distance_to_ath_pct` (FLOAT)
* `percentile_rank` (FLOAT)
* `rsi` (FLOAT)
* `ema_distance_pct` (FLOAT)

### Retention policy

Retain 365 days of snapshots. A cleanup job runs at the end of every daily pipeline run, deleting rows where `snapshot_date < today - 365 days`.

---

# 7. Ratio Engine

## 7.1 Responsibilities

The ratio engine:

* computes benchmark-relative ratios
* persists ratios
* handles multiple benchmarks per stock

---

## 7.2 Formula

```text
ratio = asset_close / benchmark_close
```

---

## 7.3 Timeframe Handling

Weekly and monthly candles should be:

* internally resampled from daily candles
* not directly fetched from Yahoo Finance

This ensures consistency.

---

## 7.3 Resampling Rules

Weekly and monthly candles are resampled from `prices_daily` in-memory after daily validation, before writing to `prices_weekly` / `prices_monthly`.

* **Weekly anchor:** `resample('W-FRI')` — bar closes on Friday, or the last available trading day if Friday is a holiday.
* **Monthly anchor:** `resample('ME')` — bar closes on the last available trading day of the calendar month.
* **OHLC aggregation:** Open = first, High = max, Low = min, Close = last, Volume = sum, Adj Close = last.
* **Incomplete bars are always excluded.** A weekly bar is only written once Friday's close is available. A monthly bar is only written once the month's last trading day is confirmed. This is hardcoded behavior and not configurable.

---

# 8. Indicator Engine

## 8.1 Responsibilities

Indicator engine computes:

* RSI
* EMA21
* EMA distance

Indicators are calculated on ratio values.

---

## 8.2 Indicator Storage Policy

Indicator rows are only written to `indicators_{timeframe}` when all computed values are non-null. Rows where any indicator value is NaN (due to insufficient history) are silently dropped and never persisted. This applies to all timeframes and both the initial seed and daily pipeline runs.

### Minimum history before a valid indicator row is produced

| Indicator | Minimum candles |
|-----------|----------------|
| RSI14     | 14             |
| EMA21     | 21             |
| Combined  | 21 (EMA21 is the binding constraint) |

Given the 60-candle minimum seed threshold, all symbols will have valid indicator rows from day one of the seed.

For newly added symbols mid-operation, the daily pipeline produces no indicator rows until 21 daily candles have accumulated. This is expected behavior requiring no special handling.

### Downstream implications

* **Rankings engine:** Only rank symbols that have a valid indicator row for that date. Symbols without one are excluded from rankings silently — not ranked last, just absent.
* **Watchlist engine:** A symbol with no indicator row cannot be evaluated for watchlist entry. It stays at `status = 'OUTSIDE'` until indicators become available.

---

# 9. ATH / 52WH Engine

## 9.1 Responsibilities

Engine computes:

* ATH
* 52WH
* distance metrics
* breakout states

---

## 9.2 Rules

ATH:

* full historical high
* excluding current candle

52WH:

* rolling 252 trading sessions
* excluding current candle

---

# 10. Ranking Engine

## 10.1 Responsibilities

Ranking engine computes:

* percentile rankings
* benchmark-relative rankings

---

## 10.2 Ranking Scope

Rankings occur:

* within same benchmark universe
* within same timeframe

---

# 11. Watchlist Engine

## 11.1 Responsibilities

Watchlist engine:

* generates dynamic watchlists
* detects watchlist entries
* detects watchlist exits
* persists membership states

---

## 11.2 Watchlist Logic

Example:

```text
distance_to_ath_pct <= 1
```

---

# 12. Alert Engine

## 12.1 Responsibilities

Alert engine:

* detects state transitions
* sends Telegram alerts
* prevents duplicate alerts

---

## 12.2 Alert Rules

Alerts trigger only:

* on watchlist entry
* on watchlist exit

---

## 12.3 Alert Delivery Policy

The alert engine uses an at-least-once delivery guarantee.

### Send logic

1. Query `alerts_sent` for matching (symbol_id, benchmark_id, watchlist_type, timeframe, transition, alert_date)
2. If matching row exists — skip send
3. If no matching row exists:
   a. Attempt Telegram send
   b. If send succeeds — write row to `alerts_sent`, continue
   c. If send fails — log error, do not write to `alerts_sent` (transition will be re-detected and retried on next pipeline run)

### Retry cap

If a send fails 3 consecutive times across 3 pipeline runs for the same transition, log a critical error and write a sentinel row to `alerts_sent` with `failed = TRUE`. This prevents infinite retry on a permanently undeliverable alert while keeping the failure visible.

---

# 13. Scheduler Architecture

## 13.1 Scheduler

Use:

* APScheduler

---

## 13.2 Daily Pipeline

The YAML configuration (`config.yaml`) is the absolute source of truth.

Execution sequence:

1. Sync Config (YAML → Database)
2. Download latest EOD data for all symbols
3. Validate data
   * If corporate action detected for any symbol:
     a. Delete full price history for affected symbol/s from `prices_daily`
     b. Re-fetch full history from yfinance (`period='max'`) [synchronous]
     c. Re-insert freshly adjusted history
     d. Mark affected symbol/s for full recalculation cascade
   * Continue
4. Compute ratios
   * Full recalculation cascade for CA-affected symbols
   * Incremental update (append latest row only) for all other symbols
5. Compute indicators (same cascade/incremental split)
6. Compute ATH/52WH levels (same cascade/incremental split)
7. Compute rankings (same cascade/incremental split)
8. Generate watchlists (with hysteresis)
9. Detect transitions
10. Send alerts
    For each watchlist × benchmark combination (in consistent order):
    a. Compute transition summary for this run
    b. If transitions exist → send transition summary message
       * ▲ Entries: [symbols alphabetically]
       * ▼ Exits: [symbols alphabetically]
    c. Send daily digest message (always)
       * ATH watchlists: sort by `distance_to_ath_pct` ASC
       * 52WH watchlists: sort by `rs_strength_pct` DESC
       * Empty watchlists: send with (empty) body
       * Split into multiple messages if > 4096 characters
11. Persist `scan_snapshots`
12. Cleanup `scan_snapshots` (delete rows older than 365 days)
13. Write `last_successful_run` to `system_state`

**Cascade vs incremental flag:** Each engine receives a `recalculate_full=True` flag for CA-affected symbols. Non-affected symbols receive `recalculate_full=False` and only append the latest row.

---

# 14. Frontend Architecture (Deferred to V2)

The entire frontend architecture section is deferred to V2. Streamlit, Plotly, and all dashboard page specifications are out of scope for Phase 1.

---

# 15. Charting Architecture (Deferred to V2)

The entire charting architecture section is deferred to V2.

---

# 16. Deployment Architecture

## 16.1 Hosting Stack

AlphaRatio Scanner is optimized for low-overhead deployment on a Linux VPS.

* **Standard**: Python virtual environment managed via `uv`.
* **Process Management**: `systemd` service (`rs_scanner.service`).
* **Containerized**: Docker support via `Dockerfile` and `docker-compose.yml`.
* **Reverse Proxy**: Not required for Phase 1 as there is no web frontend.

---

## 16.2 Services

Recommended services:

* `rs_scanner.service` (for standard deployment)
* `docker-compose.yml` (for containerized deployment)

---

# 17. Logging & Monitoring

## 17.1 Logging Requirements

System should log:

* download failures
* validation errors
* alert events
* scheduler runs
* scan durations

---

## 17.2 Stale Data Detection (Deferred to V2)

Stale data banner is a V2 feature — no dashboard to display it on in Phase 1.

The `system_state` table and `last_successful_run` write (pipeline step 13) are retained for logging and debugging purposes but have no user-facing consumer in Phase 1.

---

---

