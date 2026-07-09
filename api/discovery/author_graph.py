"""Author graph — builds author network, top institutions, collaborations."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from api.discovery.models import Author, DiscoveryItem


class AuthorGraph:
    """Build and analyze the ENT author network."""

    def __init__(self):
        self._authors: dict[str, Author] = {}
        self._institution_counter: Counter = Counter()
        self._country_counter: Counter = Counter()
        self._collaborations: dict[str, set[str]] = defaultdict(set)

    def build(self, items: list[DiscoveryItem]) -> list[Author]:
        """Build author graph from discovery items."""
        self._authors = {}
        self._institution_counter.clear()
        self._country_counter.clear()
        self._collaborations.clear()

        for item in items:
            for author_name in item.authors:
                if not author_name:
                    continue

                if author_name not in self._authors:
                    self._authors[author_name] = Author(
                        name=author_name,
                        recent_papers=[],
                    )

                self._authors[author_name].paper_count += 1
                self._authors[author_name].recent_papers.append(item.title)

            # Track collaborations
            for i in range(len(item.authors)):
                for j in range(i + 1, len(item.authors)):
                    if item.authors[i] and item.authors[j]:
                        self._collaborations[item.authors[i]].add(item.authors[j])

        # Sort authors by paper count
        sorted_authors = sorted(
            self._authors.values(),
            key=lambda a: a.paper_count,
            reverse=True,
        )

        # Assign top topics
        for author in sorted_authors[:20]:
            author.top_topics = self._get_author_topics(author)

        return sorted_authors[:20]

    def get_top_institutions(self, limit: int = 10) -> list[tuple[str, int]]:
        """Get top institutions by publication count."""
        return self._institution_counter.most_common(limit)

    def get_top_countries(self, limit: int = 10) -> list[tuple[str, int]]:
        """Get top countries by publication count."""
        return self._country_counter.most_common(limit)

    def get_collaboration_network(self, author: str) -> list[str]:
        """Get collaborators for a specific author."""
        return list(self._collaborations.get(author, set()))

    def get_emerging_researchers(self, items: list[DiscoveryItem], limit: int = 5) -> list[Author]:
        """Identify researchers with high recent activity."""
        recent_authors: Counter = Counter()
        for item in items:
            for author_name in item.authors:
                if author_name:
                    recent_authors[author_name] += 1

        emerging = []
        for name, count in recent_authors.most_common(30):
            if count >= 2 and name in self._authors:
                emerging.append(self._authors[name])

        return emerging[:limit]

    def _get_author_topics(self, author: Author) -> list[str]:
        """Extract top topics for an author from their papers."""
        topic_counter: Counter = Counter()
        for item_title in author.recent_papers:
            for topic in self._extract_topics(item_title):
                topic_counter[topic] += 1
        return [t for t, _ in topic_counter.most_common(3)]

    def _extract_topics(self, text: str) -> list[str]:
        """Simple topic extraction from text."""
        topics = []
        text_lower = text.lower()
        topic_keywords = {
            "otology": ["otology", "otitis", "cochlear", "hearing", "tinnitus"],
            "rhinology": ["rhinology", "sinus", "nasal", "olfactory"],
            "laryngology": ["laryngology", "voice", "vocal", "dysphonia"],
            "head and neck": ["head and neck", "thyroid", "parotid", "neck dissection"],
            "pediatric": ["pediatric", "children", "child"],
            "sleep": ["sleep apnea", "osa", "cpap"],
            "facial plastics": ["rhinoplasty", "facial", "cosmetic"],
        }
        for topic, keywords in topic_keywords.items():
            if any(kw in text_lower for kw in keywords):
                topics.append(topic)
        return topics
