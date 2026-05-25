# Stock Screener

A tool to identify stocks based on technical and fundamental criteria.

## Overview

Stock screener that filters stocks by:
- **Technical indicators**: moving averages (20, 50, 200), resistance levels, volume trends
- **Fundamental criteria**: market cap, sector
- **User-defined filters**: extensible to additional criteria

## Project Phases

**Phase 1 (Current)**: CLI-based screener
- Interactive filtering via command-line arguments
- Data from yfinance (daily/historical, no API key required)
- Results as formatted table output

**Phase 2 (Future)**: Web dashboard
- FastAPI backend wrapping screening logic
- React frontend with saved filters, results grid, charts

## Tech Stack

- **Backend**: Python 3.9+
- **Data**: yfinance
- **CLI**: Click (for interactive argument parsing)
- **Indicators**: pandas-ta, TA-Lib (TBD)
- **Future Web**: FastAPI, React

## Project Structure

```
stock_screen/
├── src/
│   ├── screener.py         # Core screening logic
│   ├── indicators.py       # Technical indicator calculations
│   ├── data_source.py      # yfinance wrapper
│   └── cli.py              # CLI interface (Click)
├── tests/
├── requirements.txt
└── README.md
```

## Key Design Decisions

- **Start with CLI**: Lets us validate screening logic quickly before building web layer
- **Interactive filters**: Users specify criteria at runtime (e.g., `--sector tech --min-cap 10B`)
- **yfinance**: Free, no authentication, sufficient for daily/historical data
- **Extensible**: New filters and indicators can be added incrementally

## Development Flow

1. Build core screener with basic filters
2. Add technical indicators (MA crossovers, resistance)
3. CLI with interactive argument parsing
4. Test with real stock data
5. Transition to API + web later
