# Data Fetching: Latency Analysis & Design

## Problem

Screening 20 tickers currently takes 20–30 seconds. This makes the web UI feel broken.

## Root Cause

The bottleneck is not Python. It is the number of sequential HTTP round-trips to Yahoo Finance:

```
for ticker in tickers:
    fetch_stock_info(ticker)   # 1 HTTP call → Yahoo Finance
    fetch_stock_data(ticker)   # 1 HTTP call → Yahoo Finance
```

For N tickers this is 2N serial network calls. At ~1s per call, 20 tickers = ~40s.

## Why Switching to JavaScript Would Not Help

A JS rewrite is sometimes suggested as a performance fix, but it does not address the root cause:

| Concern | Reality |
|---|---|
| Yahoo Finance has no public API | `yfinance` reverse-engineers private Yahoo endpoints. A JS equivalent (`yahoo-finance2`) hits the same endpoints with the same latency. |
| CORS blocks browser-side calls | Yahoo Finance does not set CORS headers. Direct browser calls fail. A Node proxy is required — the same server-side hop exists regardless of language. |
| Data processing speed | Pandas MA/filtering on 1 year of daily OHLCV is microseconds. Language is not the bottleneck. |

Moving to Node would add migration cost with no latency improvement.

## Proposed Fix: Two Layers

### Layer 1 — Batch + Concurrent Fetches (immediate, ~5–10× speedup)

**Price history**: `yf.download` accepts a list of tickers and fetches them in a single HTTP request.

```python
# Before: N calls
for ticker in tickers:
    yf.download(ticker, period='1y')

# After: 1 call
yf.download(tickers, period='1y', group_by='ticker')
```

**Stock info** (name, sector, market cap): no batch API exists, but fetches are IO-bound and safe to parallelize.

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=10) as pool:
    infos = list(pool.map(fetch_stock_info, tickers))
```

Expected result: 20 tickers in ~3–5s instead of 20–30s.

### Layer 2 — Daily Cache with TTL (long-term, makes repeated queries instant)

Stock fundamentals and OHLCV data are published once per trading day. Caching keyed on `(ticker, date)` means:

- First request of the day: fetches from Yahoo, stores result
- All subsequent requests: served from cache, ~milliseconds

**Storage**: SQLite file (`cache.db`) — no external dependencies, zero ops overhead.

**Schema**:

```
stock_info  (ticker TEXT, date TEXT, data JSON, PRIMARY KEY (ticker, date))
stock_ohlcv (ticker TEXT, date TEXT, data JSON, PRIMARY KEY (ticker, date))
```

**Background refresh** (optional): a nightly job pre-warms the S&P 500 list so the first user of the day never waits.

```
0 6 * * 1-5   cd /app/src && python warm_cache.py   # weekdays at 6am before market open
```

## Limitations That Remain

These are structural constraints of using Yahoo Finance as the data source:

| Limitation | Detail |
|---|---|
| Unofficial API | Yahoo Finance can break `yfinance` at any time (has happened before). No SLA, no notice. |
| Rate limiting | Aggressive screening (hundreds of tickers rapidly) will get throttled or blocked by Yahoo. The concurrent fetch cap (`max_workers`) must stay conservative (~10). |
| Data quality | `stock.info` fields (sector, market cap) are sometimes stale or missing. No recourse — Yahoo controls what it publishes. |
| No intraday data | `yfinance` free tier is daily/weekly only. Real-time or minute-level data requires a paid provider (Polygon.io, Alpaca, etc.). |
| Hosting cold starts | Free-tier hosting (Render, Railway free) spins down after inactivity. First request after spin-down adds 10–20s regardless of caching. Requires a paid always-on tier or keep-alive pings to avoid. |

## If the Unofficial API Becomes a Problem

Paid alternatives that offer a stable, documented API:

| Provider | Free tier | Notes |
|---|---|---|
| Polygon.io | 5 calls/min | Clean REST API, good Python SDK |
| Alpaca Markets | Unlimited historical | Requires brokerage account |
| Alpha Vantage | 25 calls/day | Very limited free tier |
| Tiingo | 500 calls/day | Reasonable for personal use |

Switching providers would only require replacing `data_source.py` — the screener and indicators layers are decoupled from the data source.
