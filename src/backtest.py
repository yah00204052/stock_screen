"""
Vectorized daily backtest harness that reads bars from DailyDataCache.

Design / guardrails:
- Single-asset, long/flat or long/short by target *weight* per day.
- Look-ahead safe: a signal computed from bars up to day t is acted on at t+1
  (positions are shifted one bar before being multiplied into returns).
- Close-to-close returns with proportional transaction costs on turnover.
- Never touches the network: data comes from the local Parquet cache.

A Strategy maps a price frame to a target-weight Series aligned to its index:
    0.0 = flat, 1.0 = fully long, -1.0 = fully short (fractions allowed).
"""
from dataclasses import dataclass, field
from typing import Optional, Dict

import numpy as np
import pandas as pd

from indicators import moving_average

TRADING_DAYS = 252


# --------------------------------------------------------------------------- #
# Strategies
# --------------------------------------------------------------------------- #
class Strategy:
    """Base class. Override generate_signals to return target weights."""

    name = "strategy"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        raise NotImplementedError

    @staticmethod
    def _close(df: pd.DataFrame) -> pd.Series:
        close = df["Close"]
        if isinstance(close, pd.DataFrame):  # tolerate MultiIndex leftovers
            close = close.iloc[:, 0]
        return close


class BuyAndHold(Strategy):
    name = "buy-and-hold"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        return pd.Series(1.0, index=df.index)


class SmaCross(Strategy):
    """Long when fast SMA is above slow SMA, flat otherwise."""

    def __init__(self, fast: int = 50, slow: int = 200, allow_short: bool = False):
        if fast >= slow:
            raise ValueError("fast period must be < slow period")
        self.fast, self.slow, self.allow_short = fast, slow, allow_short
        self.name = f"sma-cross({fast}/{slow})"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = self._close(df)
        fast = moving_average(close, self.fast)
        slow = moving_average(close, self.slow)
        long = (fast > slow).astype(float)
        if self.allow_short:
            return long - (fast < slow).astype(float)  # +1 / -1
        return long  # +1 / 0


# --------------------------------------------------------------------------- #
# Result + metrics
# --------------------------------------------------------------------------- #
@dataclass
class BacktestResult:
    ticker: str
    strategy: str
    equity: pd.Series
    returns: pd.Series
    positions: pd.Series
    benchmark_equity: pd.Series
    metrics: Dict[str, float] = field(default_factory=dict)

    def summary(self) -> str:
        m = self.metrics
        lines = [
            f"{self.strategy} on {self.ticker}  "
            f"[{self.equity.index.min().date()} -> {self.equity.index.max().date()}]",
            f"  total return   : {m['total_return']:+.1%}   "
            f"(buy & hold {m['bh_total_return']:+.1%})",
            f"  CAGR           : {m['cagr']:+.2%}   (buy & hold {m['bh_cagr']:+.2%})",
            f"  ann. volatility: {m['ann_vol']:.2%}",
            f"  Sharpe         : {m['sharpe']:.2f}",
            f"  max drawdown   : {m['max_drawdown']:.1%}",
            f"  exposure       : {m['exposure']:.0%}   trades: {int(m['n_trades'])}",
        ]
        return "\n".join(lines)


def _metrics(strat_ret: pd.Series, equity: pd.Series, positions: pd.Series,
             bench_ret: pd.Series, bench_equity: pd.Series) -> Dict[str, float]:
    n = len(strat_ret)
    years = n / TRADING_DAYS if n else np.nan

    def cagr(eq):
        if len(eq) < 2 or eq.iloc[0] <= 0 or years <= 0:
            return np.nan
        return (eq.iloc[-1] / eq.iloc[0]) ** (1 / years) - 1

    std = strat_ret.std()
    sharpe = (strat_ret.mean() / std * np.sqrt(TRADING_DAYS)) if std > 0 else np.nan
    drawdown = (equity / equity.cummax() - 1.0).min()
    n_trades = int((positions.diff().fillna(positions).abs() > 1e-9).sum())

    return {
        "total_return": equity.iloc[-1] / equity.iloc[0] - 1.0,
        "cagr": cagr(equity),
        "ann_vol": std * np.sqrt(TRADING_DAYS),
        "sharpe": sharpe,
        "max_drawdown": drawdown,
        "exposure": positions.abs().mean(),
        "n_trades": n_trades,
        "bh_total_return": bench_equity.iloc[-1] / bench_equity.iloc[0] - 1.0,
        "bh_cagr": cagr(bench_equity),
    }


# --------------------------------------------------------------------------- #
# Engine
# --------------------------------------------------------------------------- #
class Backtester:
    def __init__(self, cache, initial_cash: float = 10_000.0, cost_bps: float = 1.0):
        # cost_bps: per-unit-turnover cost in basis points (1 bps = 0.01%).
        self.cache = cache
        self.initial_cash = initial_cash
        self.cost = cost_bps / 10_000.0

    def run(self, ticker: str, strategy: Strategy,
            start: Optional[str] = None, end: Optional[str] = None) -> BacktestResult:
        df = self.cache.get(ticker, start=start, end=end)
        if df is None or len(df) < 2:
            raise ValueError(f"no/insufficient cached data for {ticker} "
                             f"(run scripts/build_cache.py first)")

        close = Strategy._close(df)
        asset_ret = close.pct_change().fillna(0.0)

        # signal at t -> position held over t+1 (no look-ahead)
        target = strategy.generate_signals(df).reindex(df.index).fillna(0.0)
        position = target.shift(1).fillna(0.0)

        turnover = position.diff().abs().fillna(position.abs())
        strat_ret = position * asset_ret - turnover * self.cost

        equity = self.initial_cash * (1.0 + strat_ret).cumprod()
        bench_equity = self.initial_cash * (1.0 + asset_ret).cumprod()

        metrics = _metrics(strat_ret, equity, position, asset_ret, bench_equity)
        return BacktestResult(
            ticker=ticker, strategy=strategy.name,
            equity=equity, returns=strat_ret, positions=position,
            benchmark_equity=bench_equity, metrics=metrics,
        )
