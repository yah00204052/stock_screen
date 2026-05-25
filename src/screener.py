from dataclasses import dataclass
from typing import List, Optional, Dict
import pandas as pd
from data_source import YahooFinanceSource
from indicators import ma_crossover, above_resistance, volume_trend


@dataclass
class ScreenFilter:
    """Represents a single screening criterion."""
    name: str
    value: str  # Store as string for flexibility
    enabled: bool = True


@dataclass
class ScreenResult:
    """Result of screening a single stock."""
    ticker: str
    name: str
    sector: str
    market_cap: float
    price: float
    ma_bullish: bool
    above_resistance: bool
    high_volume: bool
    ma_20: float
    ma_50: float
    resistance: float
    current_volume: float
    avg_volume: float


class StockScreener:
    def __init__(self):
        self.data_source = YahooFinanceSource()

    def screen(
        self,
        tickers: List[str],
        min_market_cap: Optional[float] = None,
        sector: Optional[str] = None,
        require_ma_bullish: bool = False,
        require_above_resistance: bool = False,
        require_high_volume: bool = False,
    ) -> List[ScreenResult]:
        """
        Screen a list of tickers against specified criteria.

        Args:
            tickers: List of stock tickers to screen
            min_market_cap: Minimum market cap in USD (e.g., 1e9 for 1B)
            sector: Filter by sector (partial match)
            require_ma_bullish: Require 20-MA above 50-MA
            require_above_resistance: Require price above 20-day resistance
            require_high_volume: Require volume above 20-day average

        Returns:
            List of stocks that pass all enabled filters
        """
        results = []

        for ticker in tickers:
            # Fetch stock info
            info = self.data_source.fetch_stock_info(ticker)
            if not info:
                continue

            # Check fundamental filters
            if min_market_cap and info['market_cap'] < min_market_cap:
                continue

            if sector and sector.lower() not in info['sector'].lower():
                continue

            # Fetch price data for technical filters
            data = self.data_source.fetch_stock_data(ticker)
            if data is None or len(data) < 50:  # Need enough history for MA-50
                continue

            close = data['Close']
            if isinstance(close, pd.DataFrame):
                close = close.iloc[:, 0]
            price = float(close.iloc[-1])

            # Technical filters
            ma_bullish, ma_20, ma_50 = ma_crossover(data)
            if require_ma_bullish and not ma_bullish:
                continue

            above_res, res_price, resistance = above_resistance(data)
            if require_above_resistance and not above_res:
                continue

            high_vol, cur_vol, avg_vol = volume_trend(data)
            if require_high_volume and not high_vol:
                continue

            # All filters passed
            result = ScreenResult(
                ticker=ticker,
                name=info['name'],
                sector=info['sector'],
                market_cap=info['market_cap'],
                price=price,
                ma_bullish=ma_bullish,
                above_resistance=above_res,
                high_volume=high_vol,
                ma_20=ma_20,
                ma_50=ma_50,
                resistance=resistance,
                current_volume=cur_vol,
                avg_volume=avg_vol,
            )
            results.append(result)

        return results
