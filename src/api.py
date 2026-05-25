import os
import sys
import json
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from screener import StockScreener
from data_source import YahooFinanceSource
from indicators import moving_average

app = FastAPI(title="Stock Screener API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

screener = StockScreener()
data_source = YahooFinanceSource()

SAVED_FILTERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "saved_filters.json")


class ScreenRequest(BaseModel):
    tickers: List[str]
    min_cap: Optional[float] = None  # billions
    sector: Optional[str] = None
    require_ma_bullish: bool = False
    require_above_resistance: bool = False
    require_high_volume: bool = False


class SavedFilter(BaseModel):
    name: str
    tickers: List[str]
    min_cap: Optional[float] = None
    sector: Optional[str] = None
    require_ma_bullish: bool = False
    require_above_resistance: bool = False
    require_high_volume: bool = False


def _load_saved() -> dict:
    if os.path.exists(SAVED_FILTERS_FILE):
        with open(SAVED_FILTERS_FILE) as f:
            return json.load(f)
    return {}


def _write_saved(data: dict):
    with open(SAVED_FILTERS_FILE, "w") as f:
        json.dump(data, f, indent=2)


@app.post("/api/screen")
def run_screen(req: ScreenRequest):
    min_cap_value = req.min_cap * 1e9 if req.min_cap else None
    results = screener.screen(
        tickers=req.tickers,
        min_market_cap=min_cap_value,
        sector=req.sector,
        require_ma_bullish=req.require_ma_bullish,
        require_above_resistance=req.require_above_resistance,
        require_high_volume=req.require_high_volume,
    )
    return [
        {
            "ticker": r.ticker,
            "name": r.name,
            "sector": r.sector,
            "market_cap": r.market_cap,
            "price": r.price,
            "ma_bullish": r.ma_bullish,
            "above_resistance": r.above_resistance,
            "high_volume": r.high_volume,
            "ma_20": r.ma_20,
            "ma_50": r.ma_50,
            "resistance": r.resistance,
            "current_volume": r.current_volume,
            "avg_volume": r.avg_volume,
        }
        for r in results
    ]


@app.get("/api/stock/{ticker}/history")
def get_stock_history(ticker: str):
    data = data_source.fetch_stock_data(ticker.upper())
    if data is None or len(data) < 2:
        raise HTTPException(status_code=404, detail=f"No data for {ticker}")

    close = data["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    ma20 = moving_average(close, 20)
    ma50 = moving_average(close, 50)

    dates = [d.strftime("%Y-%m-%d") for d in data.index]
    return {
        "dates": dates,
        "close": [round(float(v), 2) for v in close],
        "ma20": [None if pd.isna(v) else round(float(v), 2) for v in ma20],
        "ma50": [None if pd.isna(v) else round(float(v), 2) for v in ma50],
    }


@app.get("/api/saved-filters")
def list_saved_filters():
    return _load_saved()


@app.post("/api/saved-filters")
def save_filter(f: SavedFilter):
    saved = _load_saved()
    saved[f.name] = f.model_dump()
    _write_saved(saved)
    return {"ok": True}


@app.delete("/api/saved-filters/{name}")
def delete_filter(name: str):
    saved = _load_saved()
    saved.pop(name, None)
    _write_saved(saved)
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
