"""
Run a strategy backtest against the local Parquet cache.

Reads bars from data/daily/ (populated by scripts/build_cache.py) — never hits
the network. Prints a metrics summary vs buy-and-hold.

Run:
    venv/bin/python3 scripts/run_backtest.py SPY
    venv/bin/python3 scripts/run_backtest.py SPY --fast 50 --slow 200
    venv/bin/python3 scripts/run_backtest.py QQQ --start 2010-01-01 --short
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from data_source import DailyDataCache       # noqa: E402
from backtest import Backtester, SmaCross    # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("ticker")
    ap.add_argument("--fast", type=int, default=50)
    ap.add_argument("--slow", type=int, default=200)
    ap.add_argument("--short", action="store_true", help="allow short side")
    ap.add_argument("--start")
    ap.add_argument("--end")
    ap.add_argument("--cash", type=float, default=10_000.0)
    ap.add_argument("--cost-bps", type=float, default=1.0)
    ap.add_argument("--cache-dir", default="data/daily")
    args = ap.parse_args()

    cache = DailyDataCache(cache_dir=args.cache_dir)
    bt = Backtester(cache, initial_cash=args.cash, cost_bps=args.cost_bps)
    strat = SmaCross(fast=args.fast, slow=args.slow, allow_short=args.short)
    result = bt.run(args.ticker.upper(), strat, start=args.start, end=args.end)
    print(result.summary())


if __name__ == "__main__":
    main()
