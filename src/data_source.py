import yfinance as yf
import pandas as pd
from pathlib import Path
from typing import Optional, Iterable, Dict


OHLCV = ["Open", "High", "Low", "Close", "Volume"]

# period strings (yfinance style) -> approximate pandas offset for slicing a
# full-history cached series. "max"/None means "everything".
_PERIOD_TO_OFFSET = {
    "1mo": pd.DateOffset(months=1),
    "3mo": pd.DateOffset(months=3),
    "6mo": pd.DateOffset(months=6),
    "1y": pd.DateOffset(years=1),
    "2y": pd.DateOffset(years=2),
    "5y": pd.DateOffset(years=5),
    "10y": pd.DateOffset(years=10),
}


class DailyDataCache:
    """Local Parquet cache of daily OHLCV bars, one file per ticker.

    Built for backtesting: download once, read many times, refresh
    incrementally. The backtester should read only from here and never call
    yfinance inside its loop.

    Layout:  <cache_dir>/<TICKER>.parquet  (DatetimeIndex named "Date").
    """

    def __init__(self, cache_dir: str = "data/daily", auto_adjust: bool = True):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        # auto_adjust=True -> split/dividend-adjusted OHLC (right default for
        # return-based backtests). Set False if a signal needs raw price levels.
        self.auto_adjust = auto_adjust
        self._mem: Dict[str, pd.DataFrame] = {}  # in-process memo

    def _path(self, ticker: str) -> Path:
        return self.cache_dir / f"{ticker.upper()}.parquet"

    # ---- normalization -----------------------------------------------------
    def _normalize(self, df: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
        if df is None or df.empty:
            return None
        # yfinance hands back a MultiIndex (field, ticker) even for one ticker.
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df[[c for c in OHLCV if c in df.columns]].copy()
        df.index = pd.to_datetime(df.index)
        df.index.name = "Date"
        df = df[~df.index.duplicated(keep="last")].sort_index()
        return df if not df.empty else None

    # ---- network -----------------------------------------------------------
    def _download(self, ticker: str, start: Optional[str] = None) -> Optional[pd.DataFrame]:
        df = yf.download(
            ticker,
            start=start,
            period=None if start else "max",
            interval="1d",
            auto_adjust=self.auto_adjust,
            progress=False,
            threads=False,
        )
        return self._normalize(df)

    def _store(self, ticker: str, df: pd.DataFrame) -> None:
        ticker = ticker.upper()
        df.to_parquet(self._path(ticker))
        self._mem[ticker] = df

    # ---- public ------------------------------------------------------------
    def load(self, ticker: str) -> Optional[pd.DataFrame]:
        """Return the full cached series from memory/disk, or None if uncached."""
        ticker = ticker.upper()
        if ticker in self._mem:
            return self._mem[ticker]
        path = self._path(ticker)
        if path.exists():
            df = pd.read_parquet(path)
            self._mem[ticker] = df
            return df
        return None

    def ensure(self, ticker: str, refresh: bool = False) -> Optional[pd.DataFrame]:
        """Guarantee the ticker is cached; optionally top up with newer bars."""
        ticker = ticker.upper()
        existing = self.load(ticker)

        if existing is None:
            fresh = self._download(ticker)
            if fresh is not None:
                self._store(ticker, fresh)
            return fresh

        if refresh:
            # fetch only bars after the last cached day (incremental top-up)
            next_day = existing.index.max() + pd.Timedelta(days=1)
            if next_day.normalize() <= pd.Timestamp.today().normalize():
                new = self._download(ticker, start=next_day.date().isoformat())
                if new is not None:
                    merged = pd.concat([existing, new])
                    merged = merged[~merged.index.duplicated(keep="last")].sort_index()
                    self._store(ticker, merged)
                    return merged
        return existing

    def get(
        self,
        ticker: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        refresh: bool = False,
    ) -> Optional[pd.DataFrame]:
        """Date-range slice for backtesting. Downloads on first use."""
        df = self.ensure(ticker, refresh=refresh)
        if df is None:
            return None
        if start:
            df = df[df.index >= pd.Timestamp(start)]
        if end:
            df = df[df.index <= pd.Timestamp(end)]
        return df

    def bulk_download(
        self, tickers: Iterable[str], refresh: bool = False
    ) -> Dict[str, bool]:
        """Pre-warm the cache for a whole universe. Returns ticker -> ok."""
        results: Dict[str, bool] = {}
        for t in tickers:
            try:
                results[t] = self.ensure(t, refresh=refresh) is not None
            except Exception as e:  # one bad ticker shouldn't kill the batch
                print(f"Failed {t}: {e}")
                results[t] = False
        return results


class YahooFinanceSource:
    def __init__(self, cache: Optional[DailyDataCache] = None):
        # Pass a DailyDataCache to back daily fetches with the Parquet store;
        # leave None to keep the original live, in-memory-only behavior.
        self.cache = cache
        self.mem_cache = {}

    def fetch_stock_data(
        self,
        ticker: str,
        period: str = "1y",
        interval: str = "1d"
    ) -> Optional[pd.DataFrame]:
        """Fetch historical data for a single stock."""
        try:
            # Route daily requests through the Parquet cache when available.
            if self.cache is not None and interval == "1d":
                df = self.cache.ensure(ticker)
                if df is None:
                    return None
                offset = _PERIOD_TO_OFFSET.get(period)
                if offset is not None and not df.empty:
                    start = df.index.max() - offset
                    df = df[df.index >= start]
                return df

            key = (ticker, period, interval)
            if key not in self.mem_cache:
                data = yf.download(
                    ticker,
                    period=period,
                    interval=interval,
                    progress=False
                )
                self.mem_cache[key] = data
            return self.mem_cache[key]
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            return None

    def fetch_stock_info(self, ticker: str) -> dict:
        """Fetch stock metadata (sector, market cap, etc)."""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return {
                'ticker': ticker,
                'name': info.get('longName', ''),
                'sector': info.get('sector', ''),
                'market_cap': info.get('marketCap', 0),
                'volume': info.get('volume', 0),
                'pe_ratio': info.get('trailingPE', None),
                'dividend_yield': info.get('dividendYield', None),
            }
        except Exception as e:
            print(f"Error fetching info for {ticker}: {e}")
            return {}
