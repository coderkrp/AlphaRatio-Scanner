# Deployment Guide

AlphaRatio Scanner is designed to run unattended on a cloud VPS (Virtual Private Server) as a cron-scheduled pipeline.

## 1. VPS Selection

For optimal cost/performance, a basic $4-$6/month VPS is sufficient:
- **Providers**: DigitalOcean (Basic Droplet), AWS (t3.micro/t4g.micro), Hetzner (CX11), Linode.
- **OS**: Ubuntu 24.04 LTS or Debian 12.
- **Hardware**: 1 vCPU, 1GB RAM minimum.

## 2. Standard Deployment (Bare Metal / Systemd + Cron)

1. **SSH into your server**: `ssh ubuntu@your_server_ip`
2. **Install system dependencies**:
   ```bash
   sudo apt update && sudo apt install -y git curl sqlite3 build-essential
   ```
3. **Install Python environment manager (`uv`)**:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   source $HOME/.cargo/env
   ```
4. **Deploy Application**:
   ```bash
   git clone https://github.com/coderkrp/ratio-scanner.git
   cd ratio-scanner
   uv venv
   uv pip install -r requirements.txt
   ```
5. **Configure**: Create `config.yaml` using nano or vim, and run `uv run scripts/seed_database.py`.

### Scheduling with Cron
You want the script to run shortly after market close. For Indian Equities (NSE), the market closes at 15:30 IST. Yahoo Finance usually updates EOD data by 16:00 IST.

Open cron editor: `crontab -e`
Add the following line (Ensure your VPS timezone is set to IST, or adjust UTC accordingly):
```cron
# Run at 16:15 every weekday (1-5 = Mon-Fri)
15 16 * * 1-5 cd /home/ubuntu/ratio-scanner && export PYTHONPATH=. && /home/ubuntu/.cargo/bin/uv run main.py >> /home/ubuntu/ratio-scanner/data/pipeline.log 2>&1
```

## 3. Docker Deployment

If you prefer containerization to avoid messing with server Python environments, AlphaRatio provides a complete Docker setup.

### 3.1. Build the Image
```bash
docker build -t ratio-scanner:latest .
```

### 3.2. Docker Compose
We provide a `docker-compose.yml` for easy volume management (persisting the SQLite DB across container rebuilds).

1. Edit `.env` to match your credentials (or mount your `config.yaml`).
2. Run the seed command inside a temporary container:
   ```bash
   docker-compose run --rm scanner python scripts/seed_database.py
   ```
3. To trigger a manual pipeline run:
   ```bash
   docker-compose run --rm scanner python main.py
   ```

### 3.3. Scheduling with Docker
You can set up a host-level cron job that spins up the docker container:
```cron
15 16 * * 1-5 cd /path/to/repo && docker-compose run --rm scanner python main.py >> /var/log/ratio-scanner.log 2>&1
```

## 4. API Rate Limit Handling

`yfinance` connects to public Yahoo Finance APIs, which can occasionally enforce rate limits (HTTP 429 Too Many Requests).
- **Caching**: We heavily limit API calls by calculating the *exact* date delta missing from the local SQLite DB and only fetching those days.
- **Jitter/Backoff**: The data ingestion layer uses standard `httpx` backoff logic. If you encounter frequent 429s on a VPS, consider assigning an Elastic IP or spacing out the cron job to a less common minute (e.g., `17` instead of `00` or `15`).

## 5. Data Source Fallbacks (CSV)

Yahoo Finance restricts historical data for specific secondary indices (e.g., `^CNXSC`, `NIFTYSMLCAP250.NS`). For these tickers, automatic seeding with `scripts/seed_database.py` will fail to retrieve more than a few days of history.

**Action Required**:
1. Export the historical daily OHLCV data from a primary source (e.g., TradingView).
2. Upload the CSV to your server.
3. Import the data manually using the utility script:
   ```bash
   uv run scripts/import_ohlc_csv.py --symbol ^CNXSC --csv data/external/cnxsc_history.csv
   ```
4. This script will automatically synchronize the database with `config.yaml` if the symbol is tracked but missing from the database.
