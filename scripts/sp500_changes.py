"""
Scrape historical S&P 500 addition/deletion dates from Wikipedia.

Usage:
    python scripts/sp500_changes.py                  # print recent changes
    python scripts/sp500_changes.py --ticker NVDA    # filter to a specific ticker
    python scripts/sp500_changes.py --out changes.csv
"""
import argparse
import io
import sys
import pandas as pd
import requests


WIKI_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
HEADERS = {"User-Agent": "sp500-screener/1.0 (research tool; contact yah00204052@yahoo.com)"}


def fetch_sp500_changes() -> pd.DataFrame:
    """
    Pull the 'Selected changes' table from the S&P 500 Wikipedia page.
    Returns a DataFrame with columns: date, added_ticker, added_name,
    removed_ticker, removed_name, reason.
    """
    resp = requests.get(WIKI_URL, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    tables = pd.read_html(io.StringIO(resp.text), attrs={"id": "changes"})
    if not tables:
        raise RuntimeError("Could not find the changes table on the Wikipedia page.")

    raw = tables[0]

    # Wikipedia table has a two-level header; flatten it
    raw.columns = ["_".join(str(c).strip() for c in col if c != "nan").lower()
                   for col in raw.columns]

    # Normalise to consistent column names regardless of Wikipedia layout changes
    col_map = {}
    for col in raw.columns:
        if "date" in col:
            col_map[col] = "date"
        elif "added" in col and "ticker" in col:
            col_map[col] = "added_ticker"
        elif "added" in col and ("security" in col or "name" in col or "company" in col):
            col_map[col] = "added_name"
        elif "removed" in col and "ticker" in col:
            col_map[col] = "removed_ticker"
        elif "removed" in col and ("security" in col or "name" in col or "company" in col):
            col_map[col] = "removed_name"
        elif "reason" in col:
            col_map[col] = "reason"

    df = raw.rename(columns=col_map)

    # Keep only the columns we care about (some may be missing)
    keep = [c for c in ["date", "added_ticker", "added_name",
                         "removed_ticker", "removed_name", "reason"]
            if c in df.columns]
    df = df[keep].copy()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date", ascending=False).reset_index(drop=True)

    return df


def main():
    parser = argparse.ArgumentParser(description="S&P 500 index change history from Wikipedia")
    parser.add_argument("--ticker", help="Filter to a specific ticker (added or removed)")
    parser.add_argument("--out", help="Save results to a CSV file")
    parser.add_argument("--additions-only", action="store_true", help="Show only additions")
    parser.add_argument("--removals-only", action="store_true", help="Show only removals")
    args = parser.parse_args()

    print("Fetching S&P 500 change history from Wikipedia...", file=sys.stderr)
    df = fetch_sp500_changes()

    if args.ticker:
        ticker = args.ticker.upper()
        mask = (
            df.get("added_ticker", pd.Series(dtype=str)).str.upper().eq(ticker) |
            df.get("removed_ticker", pd.Series(dtype=str)).str.upper().eq(ticker)
        )
        df = df[mask]

    if args.additions_only:
        df = df[df.get("added_ticker", pd.Series(dtype=str)).notna() &
                df.get("added_ticker", pd.Series(dtype=str)).ne("")]

    if args.removals_only:
        df = df[df.get("removed_ticker", pd.Series(dtype=str)).notna() &
                df.get("removed_ticker", pd.Series(dtype=str)).ne("")]

    if df.empty:
        print("No matching records found.")
        return

    if args.out:
        df.to_csv(args.out, index=False)
        print(f"Saved {len(df)} rows to {args.out}")
    else:
        pd.set_option("display.max_rows", 100)
        pd.set_option("display.max_columns", 10)
        pd.set_option("display.width", 120)
        print(df.to_string(index=False))


if __name__ == "__main__":
    main()
