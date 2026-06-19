"""
Ad-hoc screen: S&P 500 names that made a new ~1-year high in the last N sessions.

Self-contained on purpose — fetches the universe and prices online, applies one
filter, prints the list. Tweak the knobs below and rerun; nothing else depends
on this file.

Run:
    venv/bin/python3 scripts/screen_new_high.py
"""
import warnings
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")

# ---- knobs -----------------------------------------------------------------
SESSIONS = 5            # made a new high within this many trailing sessions
LOOKBACK = 252          # window defining the "1-year" high (trading days)
PERIOD = "1y"           # how much history to pull
USE_FIELD = "High"      # "High" = intraday new high, "Close" = closing-basis
SP500_CSV = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv"
# ----------------------------------------------------------------------------


def sp500_tickers():
    """Live S&P 500 constituents (yfinance uses '-' not '.', e.g. BRK-B)."""
    df = pd.read_csv(SP500_CSV)
    return df["Symbol"].astype(str).str.replace(".", "-", regex=False).tolist()


def made_recent_high(series, sessions, lookback):
    """True if `series` equals its trailing `lookback` max on any of the last
    `sessions` days. Returns (hit, sessions_ago_of_newest_high)."""
    s = series.dropna()
    if len(s) < 30:
        return False, None
    rolling_max = s.rolling(window=lookback, min_periods=1).max()
    is_new = s >= rolling_max
    window = is_new.iloc[-sessions:]
    if not bool(window.any()):
        return False, None
    newest_idx = [i for i, v in enumerate(window.values) if v][-1]
    return True, (len(window) - 1) - newest_idx


def main():
    syms = sp500_tickers()
    print(f"Universe: {len(syms)} S&P 500 tickers")

    data = yf.download(
        syms, period=PERIOD, interval="1d",
        group_by="ticker", progress=False, threads=True,
    )

    hits, missing = [], 0
    for s in syms:
        try:
            series = data[s][USE_FIELD]
        except (KeyError, TypeError):
            missing += 1
            continue
        hit, days_ago = made_recent_high(series, SESSIONS, LOOKBACK)
        if hit:
            hits.append((s, float(series.dropna().iloc[-1]), days_ago))

    hits.sort()
    print(f"No/short data: {missing}")
    print(f"New {LOOKBACK//252 or 1}y high ({USE_FIELD}) in last {SESSIONS} sessions: "
          f"{len(hits)} names\n")
    for s, val, days_ago in hits:
        print(f"  {s:<7} {val:>10.2f}   (newest high {days_ago} session(s) ago)")


if __name__ == "__main__":
    main()
