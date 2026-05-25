import pandas as pd
import numpy as np
from typing import Tuple, Optional


def moving_average(data: pd.Series, period: int) -> pd.Series:
    """Calculate simple moving average."""
    return data.rolling(window=period).mean()


def ma_crossover(
    data: pd.DataFrame,
    fast_period: int = 20,
    slow_period: int = 50
) -> Tuple[bool, float, float]:
    """
    Check if fast MA is above slow MA (bullish).
    Returns: (is_bullish, fast_ma_value, slow_ma_value)
    """
    close = data['Close']
    # Handle case where close is a DataFrame with single column
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    ma_fast = moving_average(close, fast_period)
    ma_slow = moving_average(close, slow_period)

    # Get the last valid values (skip NaN)
    latest_fast = float(ma_fast.dropna().iloc[-1])
    latest_slow = float(ma_slow.dropna().iloc[-1])

    is_bullish = latest_fast > latest_slow

    return is_bullish, latest_fast, latest_slow


def above_resistance(
    data: pd.DataFrame,
    lookback: int = 20
) -> Tuple[bool, float, float]:
    """
    Check if current price is above recent resistance (highest high in lookback period).
    Returns: (is_above_resistance, current_price, resistance_level)
    """
    high = data['High']
    close = data['Close']

    # Handle case where these are DataFrames with single column
    if isinstance(high, pd.DataFrame):
        high = high.iloc[:, 0]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    close_price = float(close.iloc[-1])
    resistance = float(high.iloc[-lookback:].max())

    is_above = close_price > resistance

    return is_above, close_price, resistance


def volume_trend(
    data: pd.DataFrame,
    period: int = 20
) -> Tuple[bool, float, float]:
    """
    Check if recent volume is above average volume.
    Returns: (is_high_volume, current_volume, avg_volume)
    """
    volume = data['Volume']

    # Handle case where volume is a DataFrame with single column
    if isinstance(volume, pd.DataFrame):
        volume = volume.iloc[:, 0]

    current_vol = float(volume.iloc[-1])
    avg_vol = float(volume.iloc[-period:].mean())

    is_high = current_vol > avg_vol

    return is_high, current_vol, avg_vol


def sma_series(data: pd.DataFrame, period: int) -> pd.Series:
    """Get the full SMA series for a period."""
    return moving_average(data['Close'], period)
