# Extensibility & Plugins

AlphaRatio Scanner is designed so that quants and developers can add new trading logic without tearing apart the core system.

## 1. Engine Architecture

The pipeline (`main.py`) passes data through a series of "Engines".
Currently, these include:
1. `RatioEngine`
2. `IndicatorEngine`
3. `LevelsEngine`
4. `RankingEngine`

If you want to add a completely new concept—for example, a **Volatility Contraction (VCP) Engine**—you simply create `src/engines/vcp_engine.py` and insert it into the pipeline flow.

## 2. Adding Custom Indicators

The `IndicatorEngine` relies on `pandas-ta`. If you want to add a custom metric (e.g., a proprietary MACD of the Ratio), you do not need to alter the database schema immediately. 

Instead, append the column to the pandas DataFrame generated in memory:
```python
# Inside indicator_engine.py
def compute_custom_macd(ratio_df: pd.DataFrame) -> pd.DataFrame:
    # Calculate MACD on the ratio close
    macd = ratio_df.ta.macd(close='ratio_close', fast=12, slow=26, signal=9)
    ratio_df = ratio_df.join(macd)
    return ratio_df
```

To persist this to the database, simply add the column to the `Models.py` SQLAlchemy definition (and optionally use Alembic for migrations if deploying to production PostgreSQL).

## 3. Webhooks & Alternative Alerting

Currently, the `AlertEngine` is tightly coupled to Telegram. 
In the future roadmap, this will be abstracted into a `BaseNotifier` class.

**Future Implementation:**
```python
class BaseNotifier(ABC):
    @abstractmethod
    async def dispatch(self, message: str, payload: dict):
        pass

class TelegramNotifier(BaseNotifier):
    # Current implementation

class DiscordNotifier(BaseNotifier):
    # Your custom implementation here

class WebhookNotifier(BaseNotifier):
    # Fire off JSON payloads to your own API / Make.com / Zapier
```
You can currently achieve Webhook integrations by overriding the `send_watchlist_alerts()` function in `alert_engine.py`.
