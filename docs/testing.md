# Testing Strategy

AlphaRatio Scanner requires strict testing methodologies, as bugs in the math engines can lead to disastrous financial decisions.

## 1. Local Testing Setup

We use `pytest` as our testing framework. 
To install test dependencies:
```bash
uv pip install -e .[dev]
```

To run the test suite:
```bash
pytest tests/ -v --cov=src
```

## 2. Testing Philosophy

### 2.1. Deterministic Math (No Live Data)
The math engines (`ratio_engine`, `indicator_engine`) are tested against static, mocked DataFrames. We **do not** connect to `yfinance` during unit tests. Network flakiness would cause test instability. 

We maintain a suite of static CSV files in `tests/fixtures/` that contain known OHLCV data and expected indicator outputs (calculated manually or exported from TradingView for cross-verification).

### 2.2. Database Isolation
Unit tests that require a database session utilize an **in-memory SQLite database** (`sqlite:///:memory:`). This ensures tests run blazingly fast and do not mutate your actual `ratio_scanner.db`.

In `tests/conftest.py`, we define a fixture:
```python
@pytest.fixture
def db_session():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
```

### 2.3. Mocking Telegram
We mock the `httpx` asynchronous calls in the Telegram Bot class so that running the test suite doesn't spam your phone.

```python
from unittest.mock import patch

@patch('src.telegram_bot.httpx.AsyncClient.post')
async def test_telegram_alert(mock_post):
    mock_post.return_value.status_code = 200
    # trigger alert...
```

## 3. Integration Testing
We provide a separate marker for integration tests (`pytest -m integration`), which *does* hit the live Yahoo Finance API to ensure the API contracts haven't unexpectedly changed. These are run sparsely (e.g., on weekend CI runs).
