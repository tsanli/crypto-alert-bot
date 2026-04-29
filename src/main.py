"""
Crypto Alert Bot - Main Entry Point.

AI-powered crypto news alerting via Telegram with Shelby Protocol storage.
Monitors multiple news sources, analyzes sentiment/impact, and sends alerts.
"""

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import config
from src.news.sources import NewsAggregator, NewsArticle
from src.sentiment.analyzer import SentimentAnalyzer
from src.alerts.dispatcher import AlertDispatcher
from src.storage.shelby_store import ShelbyStorage, AlertRecord


DATA_DIR = Path(__file__).parent.parent / "data"
STATE_FILE = DATA_DIR / "state.json"
ALERT_LOG_FILE = DATA_DIR / "alert_log.json"


def save_state(state: dict) -> None:
    """Save bot state to local file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def load_state() -> dict:
    """Load bot state from local file."""
    if STATE_FILE.exists():
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"last_run": None, "total_alerts": 0, "start_time": datetime.now(timezone.utc).isoformat()}


def append_alert_log(alert_data: dict) -> None:
    """Append to alert log file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    logs = []
    if ALERT_LOG_FILE.exists():
        with open(ALERT_LOG_FILE, "r") as f:
            logs = json.load(f)

    logs.append(alert_data)

    # Keep last 1000 entries
    logs = logs[-1000:]

    with open(ALERT_LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)


async def run_alert_cycle() -> int:
    """
    Run one alert cycle:
    1. Fetch news from all sources
    2. Analyze sentiment and impact
    3. Send alerts to Telegram
    4. Store alerts on Shelby

    Returns number of alerts sent.
    """
    print(f"[{datetime.now(timezone.utc).isoformat()}] Starting alert cycle...")

    # Initialize components
    aggregator = NewsAggregator()
    analyzer = SentimentAnalyzer()
    dispatcher = AlertDispatcher(config.telegram.bot_token, config.telegram.chat_id)
    storage = ShelbyStorage()

    try:
        # Fetch all news
        print("Fetching news from all sources...")
        articles = await aggregator.fetch_all()
        print(f"Fetched {len(articles)} articles")

        if not articles:
            print("No articles fetched")
            return 0

        # Filter by impact
        filtered_articles = analyzer.filter_articles(
            articles,
            min_impact=config.alert.min_impact_score
        )
        print(f"Filtered to {len(filtered_articles)} high-impact articles")

        if not filtered_articles:
            print("No articles meet impact threshold")
            return 0

        # Send alerts
        alerts_sent = 0
        alerts_stored = 0

        for article in filtered_articles[:10]:  # Max 10 per cycle
            # Send to Telegram
            sent = await dispatcher.send_alert(article)

            if sent:
                alerts_sent += 1

                # Store on Shelby
                alert_record = AlertRecord(
                    id=f"alert_{datetime.now(timezone.utc).timestamp()}",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    article_title=article.title,
                    article_url=article.url,
                    source=article.source,
                    sentiment=article.sentiment_score,
                    impact_score=article.impact_score,
                    detected_tokens=article.detected_tokens,
                    detected_keywords=article.detected_keywords,
                    message_sent=True,
                )

                # Log locally
                append_alert_log({
                    "timestamp": alert_record.timestamp,
                    "title": alert_record.article_title,
                    "source": alert_record.source,
                    "impact": alert_record.impact_score,
                    "sentiment": alert_record.sentiment_score,
                    "tokens": alert_record.detected_tokens,
                })

                # Store on Shelby if enabled
                if storage.enabled:
                    blob_id = await storage.store_alert(alert_record)
                    if blob_id:
                        alerts_stored += 1
                        print(f"  Stored on Shelby: {blob_id}")

                print(f"  Alert sent: {article.title[:50]}...")

            # Rate limit delay
            await asyncio.sleep(1)

        # Update state
        state = load_state()
        state["last_run"] = datetime.now(timezone.utc).isoformat()
        state["total_alerts"] = state.get("total_alerts", 0) + alerts_sent
        save_state(state)

        print(f"Cycle complete: {alerts_sent} alerts sent, {alerts_stored} stored on Shelby")
        return alerts_sent

    except Exception as e:
        print(f"Alert cycle error: {e}")
        return 0


async def run_scheduled(interval_minutes: int = 5):
    """
    Run the bot on a scheduled interval.
    """
    print("=" * 50)
    print("Crypto Alert Bot v1.0.0")
    print("=" * 50)

    try:
        config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Copy .env.example to .env and fill in your credentials.")
        sys.exit(1)

    print(f"Telegram: Configured")
    print(f"Shelby: {'Enabled' if config.shelby.enabled else 'Disabled'}")
    print(f"Interval: {interval_minutes} minutes")
    print(f"Min Impact: {config.alert.min_impact_score}")
    print(f"Max Alerts/Hour: {config.alert.max_alerts_per_hour}")
    print(f"Monitored Tokens: {', '.join(config.alert.monitored_tokens[:5])}...")
    print("-" * 50)

    print(f"Starting scheduled alerts every {interval_minutes} minutes...")
    print("Press Ctrl+C to stop")

    while True:
        await run_alert_cycle()
        await asyncio.sleep(interval_minutes * 60)


async def run_once():
    """Run a single alert cycle (for testing)."""
    print("=" * 50)
    print("Crypto Alert Bot v1.0.0 - Single Run Mode")
    print("=" * 50)

    try:
        config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)

    await run_alert_cycle()


def main():
    """Main entry point with CLI argument support."""
    import argparse

    parser = argparse.ArgumentParser(description="Crypto Alert Bot")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single cycle instead of scheduled"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=config.alert.interval_minutes,
        help="Minutes between alert cycles (default: from config)"
    )

    args = parser.parse_args()

    if args.once:
        asyncio.run(run_once())
    else:
        asyncio.run(run_scheduled(args.interval))


if __name__ == "__main__":
    main()
