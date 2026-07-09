"""Keyword search strategy — existing ENT queries from Digest Engine."""

from __future__ import annotations

from api.discovery.models import DiscoveryItem, DiscoveryStrategy

try:
    from api.digest.search_queries import TOPIC_QUERIES
    HAS_QUERIES = True
except ImportError:
    HAS_QUERIES = False
    TOPIC_QUERIES = {}


class KeywordSearchStrategy:
    """Search using fixed ENT topic queries from the Digest Engine."""

    async def discover(self) -> list[DiscoveryItem]:
        """Run keyword searches across all ENT topics."""
        items: list[DiscoveryItem] = []

        if not HAS_QUERIES:
            return items

        for topic, queries in TOPIC_QUERIES.items():
            for query in queries[:2]:
                topic_items = await self._search_query(query, topic.value)
                items.extend(topic_items)

        return items

    async def _search_query(self, query: str, topic: str) -> list[DiscoveryItem]:
        """Execute a single search query via LORNEWS SearchService."""
        try:
            from search_service.config import Settings
            from search_service.service import SearchService

            svc = SearchService()
            results = await svc.search_all(query, limit=10)

            items = []
            for article in results:
                item = DiscoveryItem(
                    id=f"kw-{getattr(article, 'id', '') or getattr(article, 'doi', '')}",
                    title=getattr(article, "title", "") or "",
                    authors=getattr(article, "authors", []) or [],
                    journal=getattr(article, "journal", "") or "",
                    doi=getattr(article, "doi", "") or "",
                    pmid=getattr(article, "pmid", "") or "",
                    abstract=getattr(article, "abstract", "") or "",
                    source="PubMed",
                    discovery_strategy=DiscoveryStrategy.KEYWORD_SEARCH,
                    topics=[topic],
                )
                items.append(item)

            await svc.aclose()
            return items
        except ImportError:
            return []
