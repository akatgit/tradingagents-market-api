"""News service: fetches company news via Google News RSS and scores VADER sentiment.

Uses feedparser to parse the Google News RSS feed — no API key, no rate limits.
Sentiment is computed with VADER on the headline + summary text.
"""
from __future__ import annotations

import urllib.parse
from typing import List, Optional

import feedparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()
_GOOGLE_NEWS_RSS = (
    "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
)


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


def _sentiment_summary(articles: List[dict]) -> dict:
    if not articles:
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

    compounds = [a["sentiment"]["compound"] for a in articles]
    avg_compound = round(sum(compounds) / len(compounds), 4)
    pos = sum(1 for a in articles if a["sentiment"]["label"] == "positive")
    neg = sum(1 for a in articles if a["sentiment"]["label"] == "negative")
    neu = len(articles) - pos - neg
    n = len(articles)
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


def get_news(symbol: str, limit: int = 30) -> dict:
    """Return recent news articles with VADER sentiment scores for a symbol."""
    query = urllib.parse.quote(f"{symbol.upper()} stock")
    url = _GOOGLE_NEWS_RSS.format(query=query)

    feed = feedparser.parse(url)

    articles: List[dict] = []
    for entry in feed.entries[:limit]:
        headline = entry.get("title", "")
        if not headline:
            continue

        summary = entry.get("summary", "")
        link = entry.get("link", "")
        published = entry.get("published", "")

        # feedparser returns source as a FeedParserDict with a 'title' key
        source_obj = entry.get("source", {})
        source = source_obj.get("title", "") if hasattr(source_obj, "get") else ""

        text = f"{headline}. {summary}".strip()
        articles.append(
            {
                "headline": headline,
                "summary": summary,
                "source": source or "",
                "published": published,
                "url": link,
                "sentiment": _score(text),
            }
        )

    return {
        "symbol": symbol.upper(),
        "count": len(articles),
        "sentiment_summary": _sentiment_summary(articles),
        "articles": articles,
    }
