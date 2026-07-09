"""Content Discovery Engine — continuously discover emerging ENT research."""

from api.discovery.models import (
    DiscoveryResult, DiscoveryItem, Author, JournalInfo, TrendTopic,
    DiscoveryStrategy,
)
from api.discovery.engine import ContentDiscoveryEngine

__all__ = [
    "DiscoveryResult", "DiscoveryItem", "Author", "JournalInfo",
    "TrendTopic", "DiscoveryStrategy",
    "ContentDiscoveryEngine",
]
