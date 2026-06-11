"""Market data service: wraps Alpha Vantage REST API for price quotes and OHLCV candles."""
from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Optional

import httpx
import pandas as pd

_AV_BASE = "https://www.alphavantage.co/query"
_CACHE_TTL = 300  # 5 minutes

_cache: dict = {}


def _api_key() -> str:
    key = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    if not key:
        raise ValueError("ALPHA_VANTAGE_API_KEY environment variable is not set")
    return key


def _safe_float(value) -> Optional[float]:
    try:
        if value is None:
            return None
        return round(float(value), 4)
    except (TypeError, ValueError):
        return None


def _safe_int(value) -> Optional[int]:
    try:
        if value is None:
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _check_av_errors(data: dict, symbol: str) -> None:
    """Raise ValueError for known Alpha Vantage error/limit responses."""
    if "Error Message" in data:
        raise ValueError(f"Symbol not found: '{symbol}'")
    if "Note" in data:
        raise ValueError(
            "Alpha Vantage rate limit reached (5 req/min or 25 req/day). Try again later."
        )
    if "Information" in data:
        raise ValueError(
            "Alpha Vantage daily limit reached (25 calls/day). Try again tomorrow or upgrade."
        )


def _get_daily_data(symbol: str) -> dict:
    """Fetch TIME_SERIES_DAILY (compact) with a 5-minute in-process cache.

    Both get_candles() and get_history_df() call this so one ticker
    analysis costs exactly 1 daily call instead of 2.
    """
    cache_key = f"{symbol.upper()}_daily"
    now = time.time()
    entry = _cache.get(cache_key)
    if entry and (now - entry["time"]) < _CACHE_TTL:
        return entry["data"]

    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol.upper(),
        "outputsize": "compact",
        "apikey": _api_key(),
    }
    response = httpx.get(_AV_BASE, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    _check_av_errors(data, symbol)

    _cache[cache_key] = {"data": data, "time": now}
    return data


def get_quote(symbol: str) -> dict:
    """Return the latest quote for a symbol using Alpha Vantage GLOBAL_QUOTE."""
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol.upper(),
        "apikey": _api_key(),
    }
    response = httpx.get(_AV_BASE, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    _check_av_errors(data, symbol)

    quote = data.get("Global Quote", {})
    if not quote or not quote.get("05. price"):
        raise ValueError(f"No price data found for symbol '{symbol}'")

    change_pct_raw = quote.get("10. change percent", "").replace("%", "")

    return {
        "symbol": symbol.upper(),
        "price": _safe_float(quote.get("05. price")),
        "previous_close": _safe_float(quote.get("08. previous close")),
        "change": _safe_float(quote.get("09. change")),
        "change_pct": _safe_float(change_pct_raw),
        "day_high": _safe_float(quote.get("03. high")),
        "day_low": _safe_float(quote.get("04. low")),
        "day_open": _safe_float(quote.get("02. open")),
        "volume": _safe_int(quote.get("06. volume")),
        "currency": "USD",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def get_candles(symbol: str, days: int = 60) -> dict:
    """Return daily OHLCV candles for the last N trading days."""
    data = _get_daily_data(symbol)
    time_series = data.get("Time Series (Daily)", {})
    if not time_series:
        raise ValueError(f"No price data found for symbol '{symbol}'")

    sorted_dates = sorted(time_series.keys())
    recent_dates = sorted_dates[-days:]

    candles = []
    for date_str in recent_dates:
        row = time_series[date_str]
        candles.append(
            {
                "date": date_str,
                "open": _safe_float(row.get("1. open")),
                "high": _safe_float(row.get("2. high")),
                "low": _safe_float(row.get("3. low")),
                "close": _safe_float(row.get("4. close")),
                "volume": _safe_int(row.get("5. volume")) or 0,
            }
        )

    return {
        "symbol": symbol.upper(),
        "resolution": "1d",
        "count": len(candles),
        "candles": candles,
    }


def get_history_df(symbol: str, days: int = 120) -> pd.DataFrame:
    """Return a raw OHLCV DataFrame for indicator computation.

    Uses compact output (last 100 trading days) — sufficient warm-up
    for all indicators (SMA-50, ADX-14, RSI-14, etc.).
    Columns are capitalized (Open, High, Low, Close, Volume) to match
    the ta library's expected input format.
    """
    data = _get_daily_data(symbol)
    time_series = data.get("Time Series (Daily)", {})
    if not time_series:
        raise ValueError(f"No price data found for symbol '{symbol}'")

    records = [
        {
            "Date": pd.Timestamp(date_str),
            "Open": float(row.get("1. open", 0)),
            "High": float(row.get("2. high", 0)),
            "Low": float(row.get("3. low", 0)),
            "Close": float(row.get("4. close", 0)),
            "Volume": float(row.get("5. volume", 0)),
        }
        for date_str, row in time_series.items()
    ]

    df = pd.DataFrame(records).set_index("Date").sort_index()
    return df
