# Performance & Optimization

AlphaRatio Scanner was refactored to support institutional-grade execution speeds, reducing daily execution times from minutes to seconds even for a 500+ symbol universe.

## 1. The Vectorization Imperative

In early iterations, the scanner iterated row-by-row over historical prices to calculate relative strength. This is an anti-pattern in Python. 

**Before (Slow):**
```python
# Anti-pattern: Iterating rows
for index, row in asset_df.iterrows():
    bench_price = benchmark_df.loc[index]['Close']
    ratio = row['Close'] / bench_price
```

**After (Vectorized - 100x faster):**
```python
# The Pandas Way
aligned_asset, aligned_bench = asset_df.align(benchmark_df, join='inner', axis=0)
ratio_series = aligned_asset['Close'] / aligned_bench['Close']
```
By utilizing Pandas alignment and C-level vectorized operations, we offload the heavy mathematical lifting from Python's interpreter.

## 2. Technical Indicator Optimization (`pandas-ta`)

We utilize `pandas-ta` instead of manually writing moving average loops. This library heavily leverages NumPy for speed.
(Note: For pure HFT latency, `ta-lib` C-bindings are superior, but `pandas-ta` offers significantly better developer experience and deployment compatibility on Windows/macOS, making it the right tradeoff for End-of-Day scanning).

## 3. Caching Strategy (Incremental Updates)

The pipeline is designed to be **idempotent and incremental**.
- The SQLite database acts as a localized cache.
- On daily execution, the `yfinance` fetcher queries the DB for `MAX(date)` for each symbol.
- It only requests the delta (the missing days) from the external API.
- This prevents the system from re-downloading and re-saving 10 years of history every day, bypassing API rate limits and keeping network I/O to < 5 seconds total.

## 4. Avoiding Lookahead Bias in Resampling

When converting Daily data to Weekly data, it is critical to group by standard calendar weeks (e.g., ending Friday). 
If Thursday's data is the latest available, calculating a "Weekly Close" using Thursday as the end-point introduces lookahead bias if backtesting. The `Resampler` strictly adheres to `pandas` standard `W-FRI` frequency, ensuring that partial weeks are handled cleanly and metrics are only evaluated on confirmed weekly closes.
