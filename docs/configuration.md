# Configuration Guide

AlphaRatio Scanner is highly customizable without requiring code changes. All configurations are managed in `config.yaml` located in the root directory.

## Core Structure

The `config.yaml` file is divided into three main sections:
1. **Infrastructure**: Telegram API keys and Database paths.
2. **Benchmarks**: The indices/assets you want to compare your stocks against.
3. **Symbols**: The actual stocks you want to scan.

---

## Realistic Configuration Pattern

Here is a production-ready example of how to structure your configuration.

```yaml
telegram:
  token: "YOUR_TELEGRAM_BOT_TOKEN_HERE"
  # You can specify a single ID or a list of IDs for broadcasting
  chat_id: 
    - "123456789"    # Your personal ID
    - "-1009876543"  # A private Telegram group

database:
  # SQLite is the default. You can point this to a specific directory.
  url: "sqlite:///./data/ratio_scanner.db"

# Define the benchmarks. The engine will download data for these just like normal stocks.
benchmarks:
  - ticker: "^NSEI"
    name: "Nifty 50"
  - ticker: "^NSMIDCP"
    name: "Nifty Midcap 100"
  - ticker: "^CNXAUTO"
    name: "Nifty Auto"

# Define the universe of stocks to scan
symbols:
  # Example 1: Broad Market Comparison
  - ticker: "RELIANCE.NS"
    name: "Reliance Industries"
    benchmarks: ["^NSEI"]

  # Example 2: Multi-Benchmark Sector Comparison
  # Compare Tata Motors against both the broad market AND its sector index.
  - ticker: "TATAMOTORS.NS"
    name: "Tata Motors"
    benchmarks: ["^NSEI", "^CNXAUTO"]

  # Example 3: Midcap tracking
  - ticker: "CLEAN.NS"
    name: "Clean Science and Technology"
    benchmarks: ["^NSMIDCP"]
```

## Security Best Practices
- **NEVER** commit `config.yaml` to version control. It is included in the `.gitignore` by default.
- If deploying via Docker, you can optionally override these yaml settings using Environment Variables (e.g., `TELEGRAM_TOKEN`), though the YAML structure remains the primary source of truth for the asset universe.

## Modifying the Universe Dynamically
When you add or remove a ticker from the `symbols` list:
- **Adding**: The next time `main.py` runs, the `ConfigLoader` detects the new symbol, adds it to the DB, and automatically initiates a historical backfill for that specific symbol before proceeding to the daily calculations.
- **Removing**: The symbol is marked as `is_active = False` in the database. Historical data is retained, but no further API calls or calculations are wasted on it.
