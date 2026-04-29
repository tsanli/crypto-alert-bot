"""
News source integrations for Crypto Alert Bot.
Fetches news from multiple sources: NewsAPI, CryptoPanic, Reddit RSS, CoinGecko.
"""

import httpx
import feedparser
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from .config import config


@dataclass
class NewsArticle:
    """Represents a news article from any source."""
    title: str
    description: Optional[str]
    url: str
    source: str
    published_at: datetime
    author: Optional[str] = None
    image_url: Optional[str] = None
    sentiment_score: float = 0.0
    impact_score: float = 0.0
    detected_tokens: list[str] = field(default_factory=list)
    detected_keywords: list[str] = field(default_factory=list)


from collections import defaultdict


class NewsAPISource:
    """NewsAPI.org integration for general news."""

    BASE_URL = "https://newsapi.org/v2"

    async def fetch(self, query: str = "crypto", limit: int = 20) -> list[NewsArticle]:
        """Fetch news from NewsAPI."""
        if not config.news_sources.newsapi_key:
            return []

        articles = []
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/everything",
                    params={
                        "q": query,
                        "apiKey": config.news_sources.newsapi_key,
                        "language": "en",
                        "sortBy": "publishedAt",
                        "pageSize": limit,
                    }
                )
                response.raise_for_status()
                data = response.json()

                for item in data.get("articles", []):
                    try:
                        published = datetime.fromisoformat(
                            item["publishedAt"].replace("Z", "+00:00")
                        )
                    except (ValueError, TypeError):
                        published = datetime.now()

                    articles.append(NewsArticle(
                        title=item.get("title", ""),
                        description=item.get("description"),
                        url=item.get("url", ""),
                        source=f"NewsAPI/{item.get('source', {}).get('name', 'Unknown')}",
                        published_at=published,
                        author=item.get("author"),
                        image_url=item.get("urlToImage"),
                    ))

        except Exception as e:
            print(f"NewsAPI error: {e}")

        return articles


class CryptoPanicSource:
    """CryptoPanic.com aggregation source."""

    BASE_URL = "https://cryptopanic.com/api/v1/posts/"

    async def fetch(self, limit: int = 30) -> list[NewsArticle]:
        """Fetch news from CryptoPanic."""
        articles = []
        try:
            params = {
                "auth_token": config.news_sources.cryptopanic_key or "free",
                "public": "true",
                "kind": "news",
                "currencies": "BTC,ETH,SOL,BNB,ADA,MATIC,AVAX,LINK,UNI",
                "filter": "hot",
            }

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()

                for item in data.get("results", []):
                    try:
                        published = datetime.fromisoformat(
                            item["published_at"].replace("Z", "+00:00")
                        )
                    except (ValueError, TypeError):
                        published = datetime.now()

                    title = item.get("title", "")
                    domain = item.get("domain", "")

                    articles.append(NewsArticle(
                        title=title,
                        description=item.get("metadata", {}).get("description"),
                        url=item.get("url", ""),
                        source=f"CryptoPanic/{domain}",
                        published_at=published,
                        author=item.get("user", {}).get("username"),
                    ))

        except Exception as e:
            print(f"CryptoPanic error: {e}")

        return articles


class RedditRSSSource:
    """Reddit RSS feeds for crypto subreddits."""

    SUBREDDITS = [
        "r/CryptoCurrency",
        "r/Bitcoin",
        "r/ethereum",
        "r/Solana",
        "r/CoinBase",
        "r/defi",
    ]

    async def fetch(self, limit_per_sub: int = 10) -> list[NewsArticle]:
        """Fetch hot posts from crypto subreddits."""
        articles = []

        for subreddit in self.SUBREDDITS:
            try:
                feed_url = f"https://www.reddit.com/{subreddit}/hot.rss?limit={limit_per_sub}"
                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await client.get(
                        feed_url,
                        headers={"User-Agent": "CryptoAlertBot/1.0"}
                    )
                    response.raise_for_status()

                feed = feedparser.parse(response.text)

                for entry in feed.entries[:limit_per_sub]:
                    try:
                        published = datetime.fromisoformat(
                            entry.published.replace("Z", "+00:00")
                        )
                    except (ValueError, TypeError):
                        published = datetime.now()

                    articles.append(NewsArticle(
                        title=entry.title,
                        description=entry.get("summary", "")[:200],
                        url=entry.link,
                        source=f"Reddit/{subreddit}",
                        published_at=published,
                    ))

            except Exception as e:
                print(f"Reddit RSS error ({subreddit}): {e}")

        return articles


class CoinGeckoNewsSource:
    """CoinGecko news integration."""

    BASE_URL = "https://api.coingecko.com/api/v3"

    async def fetch(self, limit: int = 20) -> list[NewsArticle]:
        """Fetch news from CoinGecko."""
        articles = []

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/news/crypto",
                    params={"per_page": limit}
                )
                response.raise_for_status()
                data = response.json()

                for item in data.get("data", []):
                    try:
                        published = datetime.fromisoformat(
                            item["updated_at"].replace("Z", "+00:00")
                        )
                    except (ValueError, TypeError):
                        published = datetime.now()

                    articles.append(NewsArticle(
                        title=item.get("title", ""),
                        description=item.get("description", "")[:200],
                        url=item.get("url", ""),
                        source=f"CoinGecko/{item.get('feed_date', 'news')}",
                        published_at=published,
                        image_url=item.get("thumb_2x"),
                    ))

        except Exception as e:
            print(f"CoinGecko news error: {e}")

        return articles


class NewsAggregator:
    """Aggregates news from all configured sources."""

    def __init__(self):
        self.sources = []

        if config.news_sources.enable_newsapi:
            self.sources.append(NewsAPISource())

        if config.news_sources.enable_cryptopanic:
            self.sources.append(CryptoPanicSource())

        if config.news_sources.enable_reddit:
            self.sources.append(RedditRSSSource())

        if config.news_sources.enable_coingecko:
            self.sources.append(CoinGeckoNewsSource())

    async def fetch_all(self) -> list[NewsArticle]:
        """Fetch and aggregate news from all sources."""
        all_articles = []

        for source in self.sources:
            try:
                articles = await source.fetch()
                all_articles.extend(articles)
            except Exception as e:
                print(f"Source fetch error: {e}")

        # Deduplicate by URL
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            if article.url not in seen_urls:
                seen_urls.add(article.url)
                unique_articles.append(article)

        # Sort by publication time (newest first)
        unique_articles.sort(key=lambda a: a.published_at, reverse=True)

        return unique_articles
