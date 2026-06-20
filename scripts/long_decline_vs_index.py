"""
Research: S&P 500 names that fell N+ sessions in a row, while the index did not.

Reads the local parquet cache in data/daily/ (full OHLCV history per ticker) and
uses SPY as the S&P 500 proxy. For each stock we find every *maximal* run of
consecutive down-close sessions of length >= STREAK. For each run we report what
the index did over the exact same dates: its total return and its own longest
down-streak. The point is to surface *idiosyncratic* declines -- a stock bleeding
for weeks while the broad market did something else.

Self-contained ad-hoc script (same spirit as scripts/screen_new_high.py).

Run:
    venv/bin/python3 scripts/long_decline_vs_index.py
    venv/bin/python3 scripts/long_decline_vs_index.py --streak 14
    venv/bin/python3 scripts/long_decline_vs_index.py --sp500-only --out data/declines.csv
"""
import argparse
import glob
import os
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

CACHE_DIR = "data/daily"
INDEX_TICKER = "SPY"          # S&P 500 proxy that's in the cache
SP500_CSV = (
    "https://raw.githubusercontent.com/datasets/"
    "s-and-p-500-companies/main/data/constituents.csv"
)


def load_close(ticker: str) -> pd.Series:
    """Load a ticker's Close series from the parquet cache, or empty if absent."""
    path = os.path.join(CACHE_DIR, f"{ticker}.parquet")
    if not os.path.exists(path):
        return pd.Series(dtype=float)
    close = pd.read_parquet(path, columns=["Close"])["Close"]
    return close.dropna()


def cached_tickers() -> list:
    files = glob.glob(os.path.join(CACHE_DIR, "*.parquet"))
    return sorted(os.path.splitext(os.path.basename(f))[0] for f in files)


def sp500_tickers() -> list:
    """Live S&P 500 constituents; '-' not '.' to match cache naming (BRK-B)."""
    df = pd.read_csv(SP500_CSV)
    return df["Symbol"].astype(str).str.replace(".", "-", regex=False).tolist()


def down_runs(close: pd.Series, min_len: int):
    """Yield (start_pos, end_pos) of maximal strictly-down runs with len>=min_len.
    Positions index into `close`; the reference close is at start_pos-1."""
    is_down = (close.diff() < 0).to_numpy()
    n = len(is_down)
    i = 1
    while i < n:
        if is_down[i]:
            j = i
            while j + 1 < n and is_down[j + 1]:
                j += 1
            if j - i + 1 >= min_len:
                yield i, j
            i = j + 1
        else:
            i += 1


def max_down_streak(close: pd.Series) -> int:
    """Longest run of consecutive down closes in a series."""
    best = cur = 0
    for d in (close.diff() < 0).to_numpy():
        cur = cur + 1 if d else 0
        best = max(best, cur)
    return best


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--streak", type=int, default=14,
                    help="minimum consecutive down sessions (default 14)")
    ap.add_argument("--index-streak", type=int, default=None,
                    help="exclude windows where the index also fell this many "
                         "sessions straight (default: == --streak)")
    ap.add_argument("--sp500-only", action="store_true",
                    help="restrict to current S&P 500 constituents (needs network "
                         "for the list); otherwise screens all cached tickers")
    ap.add_argument("--out", help="save instances to CSV")
    args = ap.parse_args()

    cap = args.index_streak or args.streak

    universe = cached_tickers()
    note = f"all {len(universe)} cached tickers"
    if args.sp500_only:
        try:
            members = set(sp500_tickers())
            universe = [t for t in universe if t in members]
            note = f"{len(universe)} current S&P 500 names present in cache"
        except Exception as e:
            print(f"(could not fetch S&P 500 list: {e}; using all cached tickers)")

    idx_close = load_close(INDEX_TICKER)
    if idx_close.empty:
        raise SystemExit(f"No cached {INDEX_TICKER} data for the index proxy.")
    print(f"Universe: {note}")
    print(f"Index proxy: {INDEX_TICKER} "
          f"({idx_close.index.min().date()} -> {idx_close.index.max().date()})")

    rows = []
    for t in universe:
        if t == INDEX_TICKER:
            continue
        close = load_close(t)
        if len(close) < args.streak + 5:
            continue
        for i, j in down_runs(close, args.streak):
            ref = float(close.iloc[i - 1])
            end = float(close.iloc[j])
            start_date, end_date = close.index[i], close.index[j]
            stock_drop = (end - ref) / ref * 100

            win = idx_close.loc[close.index[i - 1]:end_date]
            if len(win) >= 2:
                idx_ret = (float(win.iloc[-1]) - float(win.iloc[0])) / float(win.iloc[0]) * 100
                idx_streak = max_down_streak(win)
            else:
                idx_ret, idx_streak = np.nan, 0

            if idx_streak >= cap:
                continue
            rows.append({
                "ticker": t,
                "start": start_date.date(),
                "end": end_date.date(),
                "down_days": j - i + 1,
                "stock_%": round(stock_drop, 1),
                "spx_%": round(idx_ret, 1),
                "idx_max_down": idx_streak,
            })

    df = pd.DataFrame(rows)
    if df.empty:
        print("No instances found.")
        return

    df = df.sort_values(["down_days", "stock_%"],
                        ascending=[False, True]).reset_index(drop=True)

    print(f"\n>= {args.streak} consecutive down sessions, index fell < {cap} "
          f"straight over the same window:")
    print(f"{len(df)} runs across {df['ticker'].nunique()} names\n")

    pd.set_option("display.max_rows", 300)
    pd.set_option("display.width", 130)
    print(df.to_string(index=False))

    print("\nBy decade (run start):")
    by_dec = df.assign(decade=(pd.to_datetime(df["start"]).dt.year // 10 * 10)
                       ).groupby("decade").size()
    print(by_dec.to_string())

    if args.out:
        df.to_csv(args.out, index=False)
        print(f"\nSaved {len(df)} rows to {args.out}")


if __name__ == "__main__":
    main()
