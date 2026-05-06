from dataclasses import dataclass
from typing import Optional

@dataclass
class KeywordFilter:
    """A keyword filter for alert matching."""
    keywords: list[str]  # All keywords must be present in the alert
    exclude: list[str] = None  # Any of these keywords exclude the alert
    label: str = ""  # Optional label for the filter

    def matches(self, text: str) -> bool:
        text_lower = text.lower()
        # All required keywords must be present
        if not all(k.lower() in text_lower for k in self.keywords):
            return False
        # No excluded keywords
        if self.exclude:
            if any(k.lower() in text_lower for k in self.exclude):
                return False
        return True

class FilterEngine:
    def __init__(self):
        self.filters = []
        self._load_filters()
    
    def _load_filters(self):
        """Load filters from environment variable or use defaults."""
        # Default filters (can be overridden by FILTER_CONFIG env var)
        self.filters = [
            KeywordFilter(
                keywords=["solana", "launch"],
                exclude=["bug", "hack", "scam"],
                label="Solana Launches"
            ),
            KeywordFilter(
                keywords=["airdrop"],
                exclude=["ended", "expired"],
                label="Active Airdrops"
            ),
            KeywordFilter(
                keywords=["token", "listing"],
                exclude=["delist"],
                label="New Listings"
            ),
        ]
    
    def load_from_env(self):
        """Load from FILTER_CONFIG env var: JSON array of filter objects."""
        import os, json
        config = os.getenv("FILTER_CONFIG")
        if config:
            try:
                self.filters = [
                    KeywordFilter(**f) for f in json.loads(config)
                ]
            except Exception:
                pass
    
    def match(self, text: str) -> list[KeywordFilter]:
        """Return all filters that match the given text."""
        return [f for f in self.filters if f.matches(text)]
    
    def should_dispatch(self, text: str) -> bool:
        """Return True if any filter matches the text."""
        return len(self.match(text)) > 0