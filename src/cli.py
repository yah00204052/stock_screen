import click
from screener import StockScreener
from pathlib import Path
import json


def format_market_cap(cap: float) -> str:
    """Format market cap as human-readable string."""
    if cap >= 1e9:
        return f"${cap / 1e9:.1f}B"
    elif cap >= 1e6:
        return f"${cap / 1e6:.1f}M"
    else:
        return f"${cap:,.0f}"


def format_currency(value: float) -> str:
    """Format currency value."""
    return f"${value:.2f}"


@click.command()
@click.option('--tickers', '-t', required=True, help='Comma-separated list of tickers (or "sp500" for S&P 500)')
@click.option('--min-cap', type=float, default=None, help='Minimum market cap in billions (e.g., 10 for 10B)')
@click.option('--sector', type=str, default=None, help='Filter by sector (partial match)')
@click.option('--ma-bullish', is_flag=True, help='Require 20-MA above 50-MA')
@click.option('--above-resistance', is_flag=True, help='Require price above 20-day resistance')
@click.option('--high-volume', is_flag=True, help='Require volume above 20-day average')
@click.option('--new-high', is_flag=True, help='Require a new ~1-year high in the last N sessions')
@click.option('--high-sessions', type=int, default=5, show_default=True, help='Sessions to check for a new high')
def screen(tickers, min_cap, sector, ma_bullish, above_resistance, high_volume, new_high, high_sessions):
    """
    Screen stocks based on technical and fundamental criteria.

    Examples:
      python cli.py --tickers AAPL,GOOGL,MSFT --min-cap 100 --ma-bullish
      python cli.py --tickers sp500 --sector Technology --above-resistance
    """
    screener = StockScreener()

    # Parse tickers
    if tickers.lower() == 'sp500':
        # For now, just use a small sample. Later could fetch real S&P 500 list
        ticker_list = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK.B', 'JNJ', 'V']
        click.echo(f"Screening S&P 500 (sample of {len(ticker_list)} tickers)...")
    else:
        ticker_list = [t.strip().upper() for t in tickers.split(',')]

    # Convert min_cap from billions to actual value
    min_cap_value = min_cap * 1e9 if min_cap else None

    click.echo(f"\nFilters:")
    if min_cap_value:
        click.echo(f"  - Min market cap: {format_market_cap(min_cap_value)}")
    if sector:
        click.echo(f"  - Sector: {sector}")
    if ma_bullish:
        click.echo(f"  - MA bullish (20 > 50)")
    if above_resistance:
        click.echo(f"  - Price above 20-day resistance")
    if high_volume:
        click.echo(f"  - Volume above 20-day average")
    if new_high:
        click.echo(f"  - New 1-year high in last {high_sessions} sessions")

    click.echo(f"\nScreening {len(ticker_list)} tickers...\n")

    results = screener.screen(
        tickers=ticker_list,
        min_market_cap=min_cap_value,
        sector=sector,
        require_ma_bullish=ma_bullish,
        require_above_resistance=above_resistance,
        require_high_volume=high_volume,
        require_new_high=new_high,
        new_high_sessions=high_sessions,
    )

    if not results:
        click.echo("No stocks matched the criteria.")
        return

    click.echo(f"Found {len(results)} matching stocks:\n")

    # Print table header
    click.echo(f"{'Ticker':<8} {'Name':<20} {'Sector':<15} {'Price':<10} {'Market Cap':<12} {'MA20>50':<8} {'Res':<8} {'Vol':<8} {'NewHigh':<8}")
    click.echo("-" * 120)

    for result in results:
        ma_str = "✓" if result.ma_bullish else "✗"
        res_str = "✓" if result.above_resistance else "✗"
        vol_str = "✓" if result.high_volume else "✗"
        nh_str = "✓" if result.made_recent_high else "✗"

        name_short = result.name[:20] if result.name else "N/A"
        sector_short = result.sector[:15] if result.sector else "N/A"

        click.echo(
            f"{result.ticker:<8} {name_short:<20} {sector_short:<15} "
            f"{format_currency(result.price):<10} {format_market_cap(result.market_cap):<12} "
            f"{ma_str:<8} {res_str:<8} {vol_str:<8} {nh_str:<8}"
        )


if __name__ == '__main__':
    screen()
