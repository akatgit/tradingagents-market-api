# API Reference

## Endpoints

| Endpoint | External API | AV Calls/request | Response |
|---|---|---|---|
| `GET /quote/{symbol}` | Alpha Vantage `GLOBAL_QUOTE` | **1** | Price, change, change%, open, high, low, volume, prev close |
| `GET /candles/{symbol}?days=N` | Alpha Vantage `TIME_SERIES_DAILY` (compact) | **1** (or 0 if cached) | Last N daily OHLCV candles, sorted oldest→newest |
| `GET /indicators/{symbol}?tail=N` | Alpha Vantage `TIME_SERIES_DAILY` (shared cache) + `ta` lib locally | **0** if called after `/candles` within 5 min, else **1** | 11 indicators: RSI-14, MACD, Bollinger-20, ADX-14, ATR-14, SMA-50, CCI-20, Stochastic-14, OBV, VWAP, EMA-20 |
| `GET /news/{symbol}?limit=N` | Google News RSS via `feedparser` | **0** (no API key) | Headlines + summary + source + per-article VADER sentiment + overall sentiment summary |
| `GET /buzz/{symbol}` | Google News RSS + Reddit RSS (calls both internally) | **0** (no API key) | Combined news + Reddit count → attention level: `high` / `moderate` / `low` + interpretation |
| `GET /social/reddit/{symbol}?limit=N` | Reddit public RSS (`reddit.com/search.rss`) | **0** (no API key) | Per-post VADER sentiment on titles + aggregated sentiment summary |

## Alpha Vantage Budget

| Scenario | AV Calls |
|---|---|
| `/quote` only | 1 |
| `/candles` only | 1 |
| `/indicators` only | 1 |
| `/candles` then `/indicators` within 5 min | 1 (cache hit) |
| `/quote` + `/candles` + `/indicators` (full analysis) | **2** |
| `/news`, `/buzz`, or `/social/reddit` (any) | 0 |

**Free tier:** 25 calls/day · 5 calls/min → ~12 full ticker analyses per day.

## Caching

Daily price data (`TIME_SERIES_DAILY`) is cached in-process for **5 minutes** per symbol.  
Both `/candles` and `/indicators` share this cache — back-to-back calls for the same ticker cost 1 call, not 2.

## Data Sources

| Data | Source |
|---|---|
| Price quote | Alpha Vantage (requires `ALPHA_VANTAGE_API_KEY`) |
| OHLCV candles | Alpha Vantage (requires `ALPHA_VANTAGE_API_KEY`) |
| Technical indicators | Computed locally using the `ta` library — no extra API calls |
| News headlines | Google News RSS — no API key, no rate limits |
| Reddit social sentiment | Reddit public RSS — no API key, no rate limits |
| Buzz / attention level | Derived from news + Reddit post count — no API key, no rate limits |
