import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List


class YahooFinanceSource:
    def __init__(self):
        self.cache = {}

    def fetch_stock_data(
        self,
        ticker: str,
        period: str = "1y",
        interval: str = "1d"
    ) -> Optional[pd.DataFrame]:
        """Fetch historical data for a single stock."""
        try:
            key = (ticker, period, interval)
            if key not in self.cache:
                data = yf.download(
                    ticker,
                    period=period,
                    interval=interval,
                    progress=False
                )
                self.cache[key] = data
            return self.cache[key]
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
