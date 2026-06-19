"""
Compare neocloud stocks vs the sector/industry they belong to.

For each ticker: total return over several trailing windows, the matching
sector ETF's return, and the stock's relative out/under-performance.
Benchmarks shown for context: SPY (market), SMH (semis/AI hardware).

Run: venv/bin/python3 scripts/neocloud_vs_sector.py
"""
import warnings
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")

NEOCLOUD = ["CRWV", "NBIS", "IREN", "APLD", "CIFR", "WULF",
            "CORZ", "HUT", "BTDR", "HIVE", "RIOT", "MARA", "GLXY"]

# GICS sector -> SPDR sector ETF
SECTOR_ETF = {
    "Technology": "XLK",
    "Information Technology": "XLK",
    "Financials": "XLF",
    "Financial Services": "XLF",
    "Communication Services": "XLC",
    "Energy": "XLE",
    "Industrials": "XLI",
    "Consumer Cyclical": "XLY",
    "Healthcare": "XLV",
    "Utilities": "XLU",
}
CONTEXT = ["SPY", "SMH"]                 # always-shown benchmarks
WINDOWS = {"6M": 126, "1Y": 252, "2Y": 504}
PERIOD = "2y"


def total_return(series, days):
    """Return (pct_return, is_full_window). Falls back to since-inception when
    history is shorter than the window, flagged with is_full_window=False."""
    s = series.dropna()
    if len(s) < 2:
        return None, True
    full = len(s) >= days + 1
    if not full:
        days = len(s) - 1                # since inception
    return s.iloc[-1] / s.iloc[-days - 1] - 1, full


def main():
    sectors = {}
    for t in NEOCLOUD:
        try:
            sectors[t] = yf.Ticker(t).info.get("sector") or "?"
        except Exception:
            sectors[t] = "?"

    etfs = sorted({SECTOR_ETF.get(s) for s in sectors.values() if SECTOR_ETF.get(s)})
    universe = list(dict.fromkeys(NEOCLOUD + etfs + CONTEXT))
    px = yf.download(universe, period=PERIOD, interval="1d",
                     group_by="ticker", progress=False, threads=True)

    def close(t):
        try:
            return px[t]["Close"]
        except (KeyError, TypeError):
            return pd.Series(dtype=float)

    def pct(pair):
        if pair is None:
            return "   n/a"
        x, full = pair
        if x is None:
            return "   n/a"
        return f"{x*100:+6.1f}%" + (" " if full else "*")

    # ---- context benchmarks
    print("Benchmarks (total return):")
    print("  {:<6}".format("") + "".join(f"{w:>9}" for w in WINDOWS))
    for b in CONTEXT:
        c = close(b)
        print(f"  {b:<6}" + "".join(f"{pct(total_return(c, d)):>9}" for d in WINDOWS.values()))

    # ---- per stock vs its sector ETF
    print("\nNeocloud stocks vs their sector ETF  ( * = since inception, < full window ):")
    print(f"  {'Tick':<6}{'Sector':<16}{'ETF':<5}" + "".join(f"{w:>9}" for w in WINDOWS)
          + "   | rel 1Y   rel 2Y")
    for t in NEOCLOUD:
        sec = sectors[t]
        etf = SECTOR_ETF.get(sec, "-")
        sc, ec = close(t), (close(etf) if etf != "-" else pd.Series(dtype=float))
        rets = [total_return(sc, d) for d in WINDOWS.values()]
        row = f"  {t:<6}{(sec or '?')[:15]:<16}{etf:<5}" + "".join(f"{pct(r):>9}" for r in rets)
        rel = []
        for key in ("1Y", "2Y"):
            d = WINDOWS[key]
            s_pair, e_pair = total_return(sc, d), total_return(ec, d)
            if s_pair is None or e_pair is None or s_pair[0] is None or e_pair[0] is None:
                rel.append(None)
            else:
                # align: compare stock vs ETF over the same realized span
                full = s_pair[1] and e_pair[1]
                rel.append((s_pair[0] - e_pair[0], full))
        row += "   | " + "".join(f"{pct(r):>9}" for r in rel)
        print(row)


if __name__ == "__main__":
    main()
