"""Quality filter — removes duplicates, retracted papers, low-quality journals, predatory journals, conference abstracts."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from api.discovery.models import DiscoveryItem

# Known predatory journal name patterns
_PREDATORY_PATTERNS = [
    r"international\s+journal\s+of\s+(?:scientific|advanced|current|latest)",
    r"journal\s+of\s+(?:pharmacy|chemical|biology|physics)\s+and\s+(?:pharmaceutical|medical)",
    r"european\s+journal\s+of\s+(?:academic|scientific|research)",
    r"american\s+journal\s+of\s+(?:current|modern|advanced|latest)",
    r"open\s+access\s+(?:journal|research)",
    r"advances\s+in\s+(?:natural|applied|basic)\s+sciences",
    r"journal\s+of\s+(?:engineering|technology|computer)\s+and\s+(?:science|research)",
]

# Conference abstract indicators
_CONFERENCE_PATTERNS = [
    r"conference\s+(?:abstract|proceeding|paper)",
    r"presented\s+at\s+the",
    r"annual\s+(?:meeting|congress|conference)",
    r"abstract\s+(?:number|#)",
]

# Retracted paper indicators
_RETRACTED_PATTERNS = [
    r"retracted",
    r"retraction",
    r"withdrawn",
    r"отозвано",
    r"изъято",
]

# Low-quality journal keywords
_LOW_QUALITY_KEYWORDS = [
    "journal of", "archives of", "annals of", "international journal of",
    "asian", "african", "middle east",
]


class QualityFilter:
    """Filter discovery results for quality and relevance."""

    def __init__(self):
        self._seen_dois: set[str] = set()
        self._seen_titles: set[str] = set()

    def filter(self, items: list[DiscoveryItem]) -> list[DiscoveryItem]:
        """Apply all quality filters. Returns deduplicated, high-quality items."""
        filtered: list[DiscoveryItem] = []

        for item in items:
            if not self._passes_filters(item):
                continue
            filtered.append(item)

        return filtered

    def _passes_filters(self, item: DiscoveryItem) -> bool:
        """Check if a single item passes all quality filters."""
        if not self._passes_dedup(item):
            return False
        if self._is_retracted(item):
            return False
        if self._is_predatory(item):
            return False
        if self._is_conference_abstract(item):
            return False
        if self._is_low_quality(item):
            return False

        return True

    def _passes_dedup(self, item: DiscoveryItem) -> bool:
        """Remove duplicates by DOI or title hash."""
        if item.doi:
            if item.doi in self._seen_dois:
                return False
            self._seen_dois.add(item.doi)

        title_key = self._title_hash(item.title)
        if title_key in self._seen_titles:
            return False
        self._seen_titles.add(title_key)

        return True

    def _is_retracted(self, item: DiscoveryItem) -> bool:
        """Check if paper is retracted."""
        text = f"{item.title} {item.abstract}".lower()
        for pattern in _RETRACTED_PATTERNS:
            if pattern in text:
                item.is_retracted = True
                return True
        return False

    def _is_predatory(self, item: DiscoveryItem) -> bool:
        """Check if journal is known as predatory."""
        journal_lower = item.journal.lower()
        for pattern in _PREDATORY_PATTERNS:
            if re.search(pattern, journal_lower):
                item.is_predatory = True
                return True
        return False

    def _is_conference_abstract(self, item: DiscoveryItem) -> bool:
        """Check if item is a conference abstract rather than full paper."""
        text = f"{item.title} {item.abstract}".lower()
        for pattern in _CONFERENCE_PATTERNS:
            if re.search(pattern, text):
                item.is_conference_abstract = True
                return True
        return False

    def _is_low_quality(self, item: DiscoveryItem) -> bool:
        """Check for low-quality indicators."""
        # Papers with no abstract are considered low quality
        if not item.abstract or len(item.abstract) < 50:
            return True
        return False

    def _title_hash(self, title: str) -> str:
        return hashlib.md5(title.lower().strip().encode()).hexdigest()[:16]
