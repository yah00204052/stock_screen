"""Backtester tests on synthetic data — no network, deterministic."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from backtest import Backtester, BuyAndHold, SmaCross  # noqa: E402


class FakeCache:
    """Stand-in for DailyDataCache that serves a fixed frame."""

    def __init__(self, df):
        self._df = df

    def get(self, ticker, start=None, end=None, refresh=False):
        df = self._df
        if start:
            df = df[df.index >= pd.Timestamp(start)]
        if end:
            df = df[df.index <= pd.Timestamp(end)]
        return df


def _frame(closes):
    idx = pd.date_range("2020-01-01", periods=len(closes), freq="B")
    c = pd.Series(closes, index=idx, dtype=float)
    return pd.DataFrame({"Open": c, "High": c, "Low": c, "Close": c,
                         "Volume": 1_000_000}, index=idx)


def test_buy_and_hold_matches_asset_return():
    df = _frame(np.linspace(100, 200, 300))  # steady uptrend
    bt = Backtester(FakeCache(df), initial_cash=1_000, cost_bps=0)
    res = bt.run("X", BuyAndHold())
    # buy & hold should equal the asset's own return (within fp noise)
    assert abs(res.metrics["total_return"] - res.metrics["bh_total_return"]) < 1e-9
    assert res.metrics["total_return"] > 0.9  # ~doubled


def test_no_lookahead_first_position_is_flat():
    df = _frame(np.linspace(100, 200, 300))
    bt = Backtester(FakeCache(df), cost_bps=0)
    res = bt.run("X", SmaCross(fast=5, slow=20))
    assert res.positions.iloc[0] == 0.0          # can't trade on bar 0
    assert res.returns.iloc[0] == 0.0


def test_costs_reduce_return():
    # oscillating price -> lots of crossover churn -> costs bite
    closes = 100 + 10 * np.sin(np.linspace(0, 30, 400))
    df = _frame(closes)
    free = Backtester(FakeCache(df), cost_bps=0).run("X", SmaCross(5, 20))
    pricey = Backtester(FakeCache(df), cost_bps=50).run("X", SmaCross(5, 20))
    assert pricey.metrics["total_return"] < free.metrics["total_return"]
    assert pricey.metrics["n_trades"] > 0


def test_flat_strategy_never_loses_when_flat():
    df = _frame(np.linspace(200, 100, 300))  # downtrend
    res = Backtester(FakeCache(df), cost_bps=0).run("X", SmaCross(5, 20))
    # long/flat strategy in a downtrend should beat buy & hold
    assert res.metrics["total_return"] > res.metrics["bh_total_return"]
