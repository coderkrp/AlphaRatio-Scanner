# Project Standards & Setup (Phase 1)

This document outlines the recommended production-grade structure, naming conventions, and technical stack for the AlphaRatio Scanner repository.

## 1. Repository Structure

```text
ratio-scanner/
├── .github/                  # GitHub Actions CI/CD and Issue/PR Templates
├── docs/                     # Comprehensive project documentation
├── src/                      # Core business logic and engines
│   ├── api/                  # (Future) FastAPI endpoints
│   ├── core/                 # Shared utilities, DB connections, configs
│   ├── engines/              # The computation modules (ratio, levels, ranking)
│   ├── models/               # SQLAlchemy ORM definitions
│   └── plugins/              # (Future) Extensible indicator plugins
├── tests/                    # Pytest suite (unit and integration tests)
├── scripts/                  # Utility scripts (seed_database.py, import_ohlc_csv.py, backfill_missing.py)
├── pyproject.toml            # Modern Python dependency & tool configuration
├── requirements.txt          # Frozen dependencies (optional, generated from pyproject.toml)
├── config.example.yaml       # Template for system configuration
├── main.py                   # Primary entry point (CLI/Cron)
├── Dockerfile                # Containerization for production deployment
├── docker-compose.yml        # Multi-container orchestration (App + DB in future)
├── Makefile                  # Developer shortcuts (make test, make lint)
└── README.md
```

## 2. Folder Responsibilities

* **`src/engines/`**: The heart of the quant logic. Each engine (`ratio_engine.py`, `ranking_engine.py`) takes an input DataFrame/DB Session, applies mathematical transformations, and returns/commits state. They must be stateless themselves.
* **`tests/`**: Must mirror the `src/` directory structure. Test data should use mocked CSVs to ensure tests can run completely offline.
* **`docs/`**: Markdown files separated by concern (Setup, Config, Architecture, etc.) to keep the root directory clean.

## 3. Naming Conventions

* **Files and Directories**: `snake_case.py` (e.g., `ratio_engine.py`).
* **Classes**: `PascalCase` (e.g., `RatioEngine`, `PricesDaily`).
* **Functions and Variables**: `snake_case` (e.g., `calculate_relative_strength()`).
* **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_RSI_PERIOD = 14`).
* **Database Tables**: Plural `snake_case` (e.g., `daily_prices`, `symbols`).

## 4. Suggested Tech Stack & Justifications

* **Language**: Python 3.12+ (Best ecosystem for quant data processing).
* **Package Manager**: `uv` by Astral (10-100x faster than pip, essential for fast CI/CD builds).
* **Formatting/Linting**: `Ruff` (Replaces Flake8, Black, Isort in a single extremely fast Rust binary).
* **Testing**: `pytest` with `pytest-cov` and `pytest-asyncio`.
* **Data Processing**: `pandas` and `pandas-ta` (Robust, industry-standard, vectorized).
* **Database**: `SQLite` via `SQLAlchemy 2.0` (Type-safe ORM, zero-config local storage).

## 5. Recommended Dependency Stack

* **Core**: `pandas`, `numpy`, `SQLAlchemy`, `PyYAML`, `yfinance`.
* **Quant**: `pandas-ta` (or `ta-lib` if strict C-bindings are required and build pipelines support it).
* **Network**: `httpx` (modern, async HTTP client for Telegram integration).
* **DevOps/Formatting**: `ruff`, `pre-commit`, `pytest`.

## 6. License Recommendation

**Apache License 2.0**
*Justification*: The Apache 2.0 license is highly recommended for professional engineering and quant tools. It allows open-source contributors and corporations to freely use, modify, and distribute the software. Crucially, it includes an explicit grant of patent rights, which provides a layer of legal protection not found in the MIT license, making it highly attractive to serious software engineers and enterprise environments.
