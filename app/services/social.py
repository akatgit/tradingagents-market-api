"""Social sentiment service: fetches Reddit posts via public RSS and scores VADER sentiment."""
from __future__ import annotations

import urllib.parse
from typing import List, Optional

import feedparser
import httpx
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()
_REDDIT_RSS = "https://www.reddit.com/search.rss?q={query}&sort=new&limit={limit}&t=week"
_HEADERS = {"User-Agent": "TradingAgents/1.0 (market research bot)"}


def _sentiment_label(compound: float) -> str:
    if compound >= 0.05:
        return "positive"
    if compound <= -0.05:
        return "negative"
    return "neutral"


def _score(text: str) -> dict:
    scores = _analyzer.polarity_scores(text)
    compound = round(scores["compound"], 4)
    return {
        "compound": compound,
        "positive": round(scores["pos"], 4),
        "negative": round(scores["neg"], 4),
        "neutral": round(scores["neu"], 4),
        "label": _sentiment_label(compound),
    }


def _sentiment_summary(posts: List[dict]) -> dict:
    if not posts:
        return _empty_summary()

    compounds = [p["sentiment"]["compound"] for p in posts]
    avg_compound = round(sum(compounds) / len(compounds), 4)
    pos = sum(1 for p in posts if p["sentiment"]["label"] == "positive")
    neg = sum(1 for p in posts if p["sentiment"]["label"] == "negative")
    neu = len(posts) - pos - neg
    n = len(posts)
    bullish_ratio: Optional[float] = round(pos / (pos + neg), 4) if (pos + neg) > 0 else None

    return {
        "avg_compound": avg_compound,
        "positive_count": pos,
        "negative_count": neg,
        "neutral_count": neu,
        "positive_pct": round(pos / n * 100, 2),
        "negative_pct": round(neg / n * 100, 2),
        "bullish_ratio": bullish_ratio,
        "overall_label": _sentiment_label(avg_compound),
    }


def _empty_summary() -> dict:
    return {
        "avg_compound": None,
        "positive_count": 0,
        "negative_count": 0,
        "neutral_count": 0,
        "positive_pct": 0.0,
        "negative_pct": 0.0,
        "bullish_ratio": None,
        "overall_label": "neutral",
    }


def _base_response(symbol: str) -> dict:
    return {
        "symbol": symbol.upper(),
        "source": "reddit",
        "posts_found": 0,
        "posts": [],
        "sentiment_summary": _empty_summary(),
    }


def get_reddit_sentiment(symbol: str, limit: int = 25) -> dict:
    """Fetch Reddit posts via public RSS and return VADER sentiment scores."""
    query = urllib.parse.quote(f"{symbol.upper()} stock")
    url = _REDDIT_RSS.format(query=query, limit=limit)

    try:
        response = httpx.get(url, headers=_HEADERS, timeout=10, follow_redirects=True)

        if response.status_code == 403:
            return {
                **_base_response(symbol),
                "error": "Reddit returned 403 — RSS may be temporarily blocked",
            }

        feed = feedparser.parse(response.text)

        if not feed.entries:
            return {
                **_base_response(symbol),
                "note": "No Reddit posts found for this symbol",
            }

        posts = []
        for entry in feed.entries:
            title = entry.get("title", "").strip()
            if not title:
                continue

            author = entry.get("author", "unknown") or "unknown"
            posts.append(
                {
                    "title": title,
                    "author": author,
                    "published": entry.get("published", ""),
                    "url": entry.get("link", ""),
                    "sentiment": _score(title),
                }
            )

        return {
            "symbol": symbol.upper(),
            "source": "reddit",
            "posts_found": len(posts),
            "posts": posts,
            "sentiment_summary": _sentiment_summary(posts),
        }

    except httpx.TimeoutException:
        return {
            **_base_response(symbol),
            "error": "Reddit request timed out after 10 seconds",
        }
    except Exception as exc:
        return {
            **_base_response(symbol),
            "error": f"Reddit fetch failed: {str(exc)}",
        }
