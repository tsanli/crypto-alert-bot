"""
Shelby Protocol integration for Crypto Alert Bot.
Stores alerts as immutable blobs for audit trail and history.
"""

import json
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional
from .config import config


# Placeholder for Shelby SDK integration
# In production, use: from shelby import Shelby
SHELBY_AVAILABLE = False

try:
    from shelby import Shelby
    SHELBY_AVAILABLE = True
except ImportError:
    pass


@dataclass
class AlertRecord:
    """A single alert record stored on Shelby."""
    id: str
    timestamp: str
    article_title: str
    article_url: str
    source: str
    sentiment: float
    impact_score: float
    detected_tokens: list[str]
    detected_keywords: list[str]
    message_sent: bool
    shelby_blob_id: Optional[str] = None


class ShelbyStorage:
    """Manages alert storage on Shelby Protocol."""

    def __init__(self):
        self.enabled = config.shelby.enabled
        self.api_key = config.shelby.api_key
        self.client = None

        if self.enabled and SHELBY_AVAILABLE and self.api_key:
            try:
                self.client = Shelby(apiKey=self.api_key)
            except Exception as e:
                print(f"Shelby initialization failed: {e}")
                self.enabled = False

    async def store_alert(self, alert: AlertRecord) -> Optional[str]:
        """
        Store an alert record as a blob on Shelby.

        Returns the blob ID if successful, None otherwise.
        """
        if not self.enabled or not self.client:
            print("Shelby storage disabled or not initialized")
            return None

        try:
            blob_data = json.dumps({
                "id": alert.id,
                "timestamp": alert.timestamp,
                "article_title": alert.article_title,
                "article_url": alert.article_url,
                "source": alert.source,
                "sentiment": alert.sentiment,
                "impact_score": alert.impact_score,
                "detected_tokens": alert.detected_tokens,
                "detected_keywords": alert.detected_keywords,
                "message_sent": alert.message_sent,
            }, indent=2)

            metadata = {
                "type": "crypto_alert",
                "agent": "crypto-alert-bot",
                "version": "1.0.0",
                "tokens": ",".join(alert.detected_tokens),
                "source": alert.source.split("/")[0].lower() if "/" in alert.source else alert.source,
            }

            blob = await self.client.blobs.upload(
                data=blob_data,
                metadata=metadata,
                owner=config.telegram.chat_id,
            )

            return blob.id

        except Exception as e:
            print(f"Failed to store alert on Shelby: {e}")
            return None

    async def store_alert_batch(self, alerts: list[AlertRecord]) -> list[str]:
        """
        Store multiple alerts as blobs.

        Returns list of blob IDs.
        """
        blob_ids = []

        for alert in alerts:
            blob_id = await self.store_alert(alert)
            if blob_id:
                blob_ids.append(blob_id)

        return blob_ids

    async def list_alerts(self, limit: int = 50) -> list[dict]:
        """
        List stored alerts from Shelby.

        Returns list of alert blobs.
        """
        if not self.enabled or not self.client:
            return []

        try:
            blobs = await self.client.blobs.list(
                owner=config.telegram.chat_id,
                limit=limit,
            )

            alerts = []
            for blob in blobs:
                try:
                    alerts.append(json.loads(blob.data))
                except json.JSONDecodeError:
                    alerts.append({"raw": blob.data})

            return alerts

        except Exception as e:
            print(f"Failed to list alerts from Shelby: {e}")
            return []

    async def verify_alert(self, blob_id: str) -> bool:
        """
        Verify an alert blob exists on Shelby.

        Returns True if blob exists.
        """
        if not self.enabled or not self.client:
            return False

        try:
            blob = await self.client.blobs.get(blob_id)
            return blob is not None
        except Exception:
            return False
