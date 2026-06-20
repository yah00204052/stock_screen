"""
Does an N-session losing streak predict anything tradeable? Test forward returns
WITHOUT look-ahead.

Tradeable rule: the moment a stock has closed down exactly N sessions in a row,
enter at that close and hold H sessions. We do NOT wait for the streak to end
(that would be look-ahead -- you'd only know the last down day in hindsight, and
it forces the next day to be an up day by construction).

Reports raw forward return, the index's return over the same forward window, and
the excess (stock - index). Reuses the cache from long_decline_vs_index.py.

Run:
    PYTHONPATH=scripts venv/bin/python3 scripts/decline_forward_returns.py --streak 14
"""
import argparse
import warnings

import numpy as np
import pandas as pd

from long_decline_vs_index import (
    load_close, cached_tickers, sp500_tickers, INDEX_TICKER,
)

warnings.filterwarnings("ignore")

HORIZONS = [1, 3, 5, 10, 20, 60]


def streak_entries(close: pd.Series, n: int):
    """Yield positions where trailing consecutive down-day count == n exactly
    (the first day the streak reaches length n). No conditioning on the future."""
    is_down = (close.diff() < 0).to_numpy()
    cur = 0
    for pos in range(len(is_down)):
        cur = cur + 1 if is_down[pos] else 0
        if cur == n:
            yield pos


def fwd(close, pos, h):
    if pos + h >= len(close):
        return np.nan
    p0, p1 = float(close.iloc[pos]), float(close.iloc[pos + h])
    return (p1 - p0) / p0 * 100


def idx_fwd(idx_close, end_date, h):
    pos = idx_close.index.searchsorted(end_date)
    if pos >= len(idx_close) or pos + h >= len(idx_close):
        return np.nan
    p0, p1 = float(idx_close.iloc[pos]), float(idx_close.iloc[pos + h])
    return (p1 - p0) / p0 * 100


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--streak", type=int, default=14)
    ap.add_argument("--sp500-only", action="store_true")
    args = ap.parse_args()

    universe = cached_tickers()
    if args.sp500_only:
        try:
            members = set(sp500_tickers())
            universe = [t for t in universe if t in members]
        except Exception as e:
            print(f"(S&P list fetch failed: {e}; using all cached)")

    idx_close = load_close(INDEX_TICKER)

    recs = []
    for t in universe:
        if t == INDEX_TICKER:
            continue
        close = load_close(t)
        if len(close) < args.streak + max(HORIZONS) + 5:
            continue
        for pos in streak_entries(close, args.streak):
            end_date = close.index[pos]
            row = {"ticker": t, "entry": end_date.date()}
            for h in HORIZONS:
                r = fwd(close, pos, h)
                ir = idx_fwd(idx_close, end_date, h)
                row[f"r{h}"] = r
                row[f"x{h}"] = (r - ir) if (r == r and ir == ir) else np.nan
            recs.append(row)

    df = pd.DataFrame(recs)
    n = len(df)
    print(f"Entries: {n} (enter on the {args.streak}th consecutive down close, "
          f"no look-ahead)\n")
    if n == 0:
        return

    def stat(col):
        s = df[col].dropna()
        return len(s), s.mean(), s.median(), (s > 0).mean() * 100

    print(f"{'H':>4} | {'n':>5} | {'raw mean%':>9} {'raw med%':>9} {'win%':>6} "
          f"|| {'exc mean%':>9} {'exc med%':>9} {'exc win%':>8}")
    print("-" * 80)
    for h in HORIZONS:
        nr, rm, rmd, rw = stat(f"r{h}")
        nx, xm, xmd, xw = stat(f"x{h}")
        print(f"{h:>4} | {nr:>5} | {rm:>9.2f} {rmd:>9.2f} {rw:>6.1f} "
              f"|| {xm:>9.2f} {xmd:>9.2f} {xw:>8.1f}")

    print("\nraw = stock return after entry; exc = excess over S&P over same window")
    print("win% = share of entries with positive return")


if __name__ == "__main__":
    main()
