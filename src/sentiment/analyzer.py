"""
Sentiment analysis and impact scoring for Crypto Alert Bot.
Uses VADER for sentiment + keyword/authority scoring for impact.
"""

import re
from dataclasses import dataclass
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from .sources import NewsArticle
from .config import config


# Token/keyword to chain mapping
TOKEN_KEYWORDS = {
    "bitcoin": ["bitcoin", "btc", "satoshi", "₿"],
    "ethereum": ["ethereum", "eth", "vitalik", "ether"],
    "solana": ["solana", "sol", "anatoly", "raj"],
    "binance": ["binance", "bnb", "cz", "changpeng"],
    "cardano": ["cardano", "ada", "hoskinson", "charles"],
    "polygon": ["polygon", "matic", "pol", "jaynti"],
    "avalanche-2": ["avalanche", "avax", "avalanchain"],
    "chainlink": ["chainlink", "link", "smartcon", "nikov"],
    "uniswap": ["uniswap", "uni", "hayden", "v3"],
    "aave": ["aave", "aave"],
}

# Impact keywords with weights
IMPACT_KEYWORDS = {
    # HIGH IMPACT
    "hack": 0.9,
    "exploit": 0.9,
    "SEC": 0.85,
    "regulation": 0.8,
    "ban": 0.8,
    "delist": 0.75,
    "fraud": 0.85,
    "arrest": 0.8,
    "investigation": 0.75,
    "ETF": 0.85,
    "approval": 0.8,
    "reject": 0.75,

    # MEDIUM IMPACT
    "partnership": 0.6,
    "launch": 0.6,
    "upgrade": 0.55,
    "migration": 0.55,
    "audit": 0.6,
    "institution": 0.65,
    "buyback": 0.5,
    "burn": 0.5,
    "mint": 0.4,

    # LOWER IMPACT but still notable
    "listing": 0.45,
    "update": 0.35,
    "announcement": 0.3,
    "conference": 0.25,
    "twitter": 0.25,
    "ama": 0.2,
}

# Source authority weights
SOURCE_AUTHORITY = {
    "cryptopanic": 0.7,
    "coingecko": 0.6,
    "newsapi": 0.5,
    "reddit": 0.4,
    # Known high-authority domains
    "coindesk": 0.9,
    "cointelegraph": 0.9,
    "decrypt": 0.8,
    "theblock": 0.85,
    "blockworks": 0.85,
    "吴": 0.8,
    "finbold": 0.7,
    "bitcoinist": 0.7,
    "nulltx": 0.6,
}


class SentimentAnalyzer:
    """Analyzes sentiment and calculates impact scores for news articles."""

    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        self.monitored_tokens = config.alert.monitored_tokens
        self.monitored_keywords = config.alert.monitored_keywords

    def analyze(self, article: NewsArticle) -> NewsArticle:
        """
        Analyze an article for sentiment and impact.

        Returns the article with updated sentiment_score and impact_score.
        """
        text = self._prepare_text(article)

        # VADER sentiment (-1 to 1)
        sentiment = self.analyzer.polarity_scores(text)
        compound = sentiment["compound"]
        article.sentiment_score = compound

        # Detect tokens
        article.detected_tokens = self._detect_tokens(text)

        # Detect keywords
        article.detected_keywords = self._detect_keywords(text)

        # Calculate impact score
        article.impact_score = self._calculate_impact(article, sentiment)

        return article

    def _prepare_text(self, article: NewsArticle) -> str:
        """Combine title and description for analysis."""
        parts = [article.title]
        if article.description:
            parts.append(article.description)
        return " ".join(parts).lower()

    def _detect_tokens(self, text: str) -> list[str]:
        """Detect which tokens/chains are mentioned."""
        detected = []
        text_lower = text.lower()

        for token, keywords in TOKEN_KEYWORDS.items():
            if token in self.monitored_tokens:
                for keyword in keywords:
                    if keyword.lower() in text_lower:
                        if token not in detected:
                            detected.append(token)
                        break

        return detected

    def _detect_keywords(self, text: str) -> list[str]:
        """Detect impact keywords."""
        detected = []
        text_lower = text.lower()

        for keyword in IMPACT_KEYWORDS.keys():
            if keyword.lower() in text_lower:
                detected.append(keyword)

        # Also check monitored keywords from config
        for keyword in self.monitored_keywords:
            if keyword.lower() in text_lower and keyword not in detected:
                detected.append(keyword)

        return detected

    def _calculate_impact(
        self,
        article: NewsArticle,
        sentiment: dict
    ) -> float:
        """
        Calculate overall impact score (0 to 1).
        Combines: keyword impact + source authority + sentiment + recency.
        """
        score = 0.0

        # Keyword impact (up to 0.4)
        max_keyword_impact = 0.0
        for keyword in article.detected_keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in IMPACT_KEYWORDS:
                max_keyword_impact = max(max_keyword_impact, IMPACT_KEYWORDS[keyword_lower])

        score += max_keyword_impact * 0.4

        # Source authority (up to 0.25)
        source_impact = self._get_source_authority(article.source)
        score += source_impact * 0.25

        # Sentiment contribution (up to 0.2)
        # Extreme sentiment (very positive or very negative) = higher impact
        abs_sentiment = abs(article.sentiment_score)
        score += abs_sentiment * 0.2

        # Token relevance (up to 0.15)
        if article.detected_tokens:
            score += min(len(article.detected_tokens) * 0.05, 0.15)

        return min(score, 1.0)

    def _get_source_authority(self, source: str) -> float:
        """Get authority score for a news source."""
        source_lower = source.lower()

        for domain, weight in SOURCE_AUTHORITY.items():
            if domain.lower() in source_lower:
                return weight

        return 0.5  # Default moderate authority

    def filter_articles(
        self,
        articles: list[NewsArticle],
        min_impact: float = None
    ) -> list[NewsArticle]:
        """
        Filter articles by minimum impact score and sort by impact.
        """
        if min_impact is None:
            min_impact = config.alert.min_impact_score

        # Analyze all articles
        analyzed = [self.analyze(a) for a in articles]

        # Filter and sort
        filtered = [a for a in analyzed if a.impact_score >= min_impact]
        filtered.sort(key=lambda a: (a.impact_score, a.published_at), reverse=True)

        return filtered
