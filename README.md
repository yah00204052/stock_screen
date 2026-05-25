# Stock Screener

A CLI-based stock screener to identify stocks based on technical and fundamental criteria.

## Installation

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Screen specific stocks:
```bash
cd src
python cli.py --tickers AAPL,GOOGL,MSFT --min-cap 100 --ma-bullish
```

Screen with multiple filters:
```bash
python cli.py --tickers AAPL,MSFT,GOOGL,AMZN,NVDA --sector Technology --above-resistance --high-volume
```

Screen S&P 500 sample:
```bash
python cli.py --tickers sp500 --ma-bullish
```

## Options

- `--tickers, -t` (required): Comma-separated list of stock tickers, or `sp500` for S&P 500 sample
- `--min-cap`: Minimum market cap in billions (e.g., `10` for $10B)
- `--sector`: Filter by sector (partial match, case-insensitive)
- `--ma-bullish`: Require 20-day MA above 50-day MA
- `--above-resistance`: Require price above 20-day resistance level
- `--high-volume`: Require current volume above 20-day average

## Output

Results are displayed in a table showing:
- **Ticker**: Stock symbol
- **Name**: Company name
- **Sector**: Industry sector
- **Price**: Current stock price
- **Market Cap**: Company market capitalization
- **MA20>50**: ✓/✗ for bullish moving average
- **Res**: ✓/✗ for above resistance
- **Vol**: ✓/✗ for high volume

## How It Works

### Technical Indicators

- **Moving Averages**: 20-day and 50-day simple moving averages (bullish if 20-MA > 50-MA)
- **Resistance**: Highest price in the last 20 days
- **Volume**: Current volume vs. 20-day average

### Data Source

Uses Yahoo Finance via `yfinance` library. No API key required.

## Future Enhancements

- Web dashboard
- Save/load filter profiles
- Scheduled screening runs
- Email alerts
- More indicators (RSI, MACD, Bollinger Bands)
- Real S&P 500 list support
