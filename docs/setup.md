# Setup Guide

This guide walks you through setting up AlphaRatio Scanner for local development or private deployment.

## 1. System Requirements
- **OS**: Linux, macOS, or Windows (WSL2 recommended for Windows users).
- **Python**: Version 3.12 or 3.13. (Note: Numba and some TA libraries may lag behind bleeding-edge Python releases).
- **RAM**: 1GB Minimum (4GB recommended if scanning >1000 symbols).

## 2. Environment Setup

We highly recommend using `uv` by Astral for managing the Python environment, as it is significantly faster than standard `pip`.

### Installing `uv`
**Linux/macOS:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Cloning and Installing Dependencies
```bash
git clone https://github.com/coderkrp/ratio-scanner.git
cd ratio-scanner

# Create a virtual environment specifically for Python 3.12
uv venv --python 3.12

# Activate it (Linux/macOS)
source .venv/bin/activate
# Activate it (Windows)
# .venv\Scripts\activate

# Install dependencies from pyproject.toml / requirements.txt
uv pip install -r requirements.txt
```

## 3. Telegram Bot Setup

AlphaRatio uses Telegram as its primary UI for delivering alerts. 

1. Open Telegram and search for `@BotFather`.
2. Send the command `/newbot` and follow the prompts to name your bot.
3. BotFather will provide an **HTTP API Token** (e.g., `123456789:ABCdefGHIjklMNOpqrSTUvwxYZ`). Keep this secret.
4. Next, find out your personal Chat ID by searching for `@userinfobot` and sending it a message. It will reply with your `Id`.
5. If you want the bot to post to a group/channel, add the bot to the group, and use a tool like `@RawDataBot` in the group to get the group's Chat ID (usually starts with a `-`).

## 4. Configuration

Copy the template configuration file:
```bash
cp config.example.yaml config.yaml
```
Edit `config.yaml` to include your Telegram credentials and desired watchlists. See [Configuration Guide](configuration.md) for details.

## 5. Database Initialization

Before running the daily scanner, you must create the SQLite database schema and perform the initial historical data fetch. This process downloads maximum available history for your configured symbols to establish a baseline for All-Time Highs and long-term moving averages.

```bash
# Ensure the root directory is in the Python Path
export PYTHONPATH=. 

# Run the seeder
uv run scripts/seed_database.py
```
*Note: If you have hundreds of symbols, this may take a few minutes. `yfinance` rate limits are handled automatically.*

## 6. Running the Pipeline

To execute a manual run of the entire pipeline:
```bash
uv run main.py
```
Check your Telegram app—you should receive a Daily Digest!
