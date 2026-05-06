"""
Telegram alert formatting and delivery for Crypto Alert Bot.
Creates beautiful, informative alert messages.
"""

import asyncio
from datetime import datetime
from typing import Optional
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

from .news.sources import NewsArticle
from .sentiment.analyzer import SentimentAnalyzer
from .config import config
from .filters import FilterEngine


# Emoji mappings for sentiment
SENTIMENT_EMOJI = {
    "positive": "🟢",
    "negative": "🔴",
    "neutral": "⚪️",
}

# Emoji mappings for impact levels
IMPACT_EMOJI = {
    "extreme": "🚨",
    "high": "⚠️",
    "medium": "📊",
    "low": "ℹ️",
}

# Token emojis
TOKEN_EMOJI = {
    "bitcoin": "₿",
    "ethereum": "Ξ",
    "solana": "◎",
    "binance": "🔶",
    "cardano": "₳",
    "polygon": "⬡",
    "avalanche-2": "🔺",
    "chainlink": "🔗",
    "uniswap": "🦄",
    "aave": "👻",
}


class AlertFormatter:
    """Formats news articles into beautiful Telegram messages."""

    def __init__(self):
        self.analyzer = SentimentAnalyzer()

    def get_sentiment_label(self, score: float) -> tuple[str, str]:
        """Get sentiment label and emoji from score (-1 to 1)."""
        if score >= 0.3:
            return "POSITIVE", SENTIMENT_EMOJI["positive"]
        elif score <= -0.3:
            return "NEGATIVE", SENTIMENT_EMOJI["negative"]
        else:
            return "NEUTRAL", SENTIMENT_EMOJI["neutral"]

    def get_impact_label(self, score: float) -> tuple[str, str]:
        """Get impact label and emoji from score (0 to 1)."""
        if score >= 0.75:
            return "EXTREME", IMPACT_EMOJI["extreme"]
        elif score >= 0.6:
            return "HIGH", IMPACT_EMOJI["high"]
        elif score >= 0.4:
            return "MEDIUM", IMPACT_EMOJI["medium"]
        else:
            return "LOW", IMPACT_EMOJI["low"]

    def format_alert(self, article: NewsArticle) -> str:
        """
        Format a news article as a Telegram message.

        Returns formatted HTML string.
        """
        # Analyze article
        article = self.analyzer.analyze(article)

        sentiment_label, sentiment_emoji = self.get_sentiment_label(article.sentiment_score)
        impact_label, impact_emoji = self.get_impact_label(article.impact_score)

        # Build tokens string
        tokens_str = ""
        if article.detected_tokens:
            token_icons = [TOKEN_EMOJI.get(t, "🪙") for t in article.detected_tokens[:3]]
            tokens_str = " ".join(token_icons) + " " + ", ".join(article.detected_tokens[:3]).upper()
            if len(article.detected_tokens) > 3:
                tokens_str += f" +{len(article.detected_tokens) - 3} more"

        # Build keywords string
        keywords_str = ""
        if article.detected_keywords:
            keywords_str = " ".join([f"#{kw}" for kw in article.detected_keywords[:5]])

        # Format time
        time_str = article.published_at.strftime("%H:%M UTC")
        date_str = article.published_at.strftime("%b %d")

        # Build message
        lines = [
            f"{impact_emoji} <b>{impact_label} IMPACT</b> {sentiment_emoji} {sentiment_label}",
            "",
            f"<a href='{article.url}'><b>{article.title}</b></a>",
            "",
        ]

        if article.description:
            desc = article.description[:200] + "..." if len(article.description) > 200 else article.description
            lines.append(f"<i>{desc}</i>")
            lines.append("")

        lines.append("━━━━━━━━━━━━━━━")
        lines.append(f"📰 Source: {article.source}")
        lines.append(f"⏰ {date_str} at {time_str}")

        if tokens_str:
            lines.append(f"💰 {tokens_str}")

        if keywords_str:
            lines.append(f"🏷️ {keywords_str}")

        lines.append("")
        lines.append(f"<code>Impact: {article.impact_score:.2f} | Sentiment: {article.sentiment_score:.2f}</code>")

        return "\n".join(lines)

    def format_summary(self, articles: list[NewsArticle], period: str = "last hour") -> str:
        """
        Format a summary of multiple articles.

        Returns formatted HTML string.
        """
        if not articles:
            return "No significant news in the last period."

        # Sort by impact
        sorted_articles = sorted(articles, key=lambda a: a.impact_score, reverse=True)[:5]

        lines = [
            f"📬 <b>Crypto News Summary</b> ({period})",
            "",
            f"<i>{len(articles)} alerts sent</i>",
            "",
        ]

        for i, article in enumerate(sorted_articles, 1):
            article = self.analyzer.analyze(article)
            impact_label, impact_emoji = self.get_impact_label(article.impact_score)

            title = article.title[:60] + "..." if len(article.title) > 60 else article.title

            lines.append(f"{i}. {impact_emoji} <b>[{impact_label}]</b> {title}")
            lines.append(f"   📰 {article.source}")
            lines.append("")

        return "\n".join(lines)


class AlertDispatcher:
    """Dispatches alerts to Telegram with rate limiting."""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot = Bot(token=bot_token)
        self.chat_id = chat_id
        self.formatter = AlertFormatter()
        self.filter_engine = FilterEngine()
        self.filter_engine.load_from_env()
        self.sent_count = 0
        self.last_reset = datetime.now()
        self.max_per_hour = config.alert.max_alerts_per_hour

    async def send_alert(self, article: NewsArticle) -> bool:
        """
        Send a single alert to Telegram.

        Returns True if sent successfully.
        """
        # Rate limiting
        self._check_rate_limit()

        if self.sent_count >= self.max_per_hour:
            print(f"Rate limit reached ({self.max_per_hour}/hour), skipping alert")
            return False

        # Build text from article for filtering
        alert_text = f"{article.title} {article.description or ''}"
        
        # Check keyword filters before sending
        if not self.filter_engine.should_dispatch(alert_text):
            print(f"Filtered out: {article.title[:50]}...")
            return False

        try:
            message = self.formatter.format_alert(article)
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=False,
            )

            self.sent_count += 1
            return True

        except TelegramError as e:
            print(f"Telegram send failed: {e}")
            return False

    async def send_summary(self, articles: list[NewsArticle]) -> bool:
        """Send a summary of multiple articles."""
        self._check_rate_limit()

        try:
            message = self.formatter.format_summary(articles)
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=ParseMode.HTML,
            )
            return True

        except TelegramError as e:
            print(f"Telegram summary send failed: {e}")
            return False

    def _check_rate_limit(self):
        """Reset counter if hour has passed."""
        now = datetime.now()
        if (now - self.last_reset).total_seconds() >= 3600:
            self.sent_count = 0
            self.last_reset = now
