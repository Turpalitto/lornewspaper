"""Author tracking strategy — find new papers from top ENT researchers.

Tracks known ENT researchers and discovers new ones.
"""

from __future__ import annotations

from api.discovery.models import Author, DiscoveryItem, DiscoveryStrategy

# Known top ENT researchers (OpenAlex IDs)
_KNOWN_ENT_RESEARCHERS = [
    # Add known researchers here when identified
]

# ENT institutions to track
_ENT_INSTITUTIONS = [
    "Harvard Medical School",
    "Johns Hopkins University",
    "Stanford University",
    "University of California San Francisco",
    "University of Pennsylvania",
    "Mayo Clinic",
    "Massachusetts Eye and Ear",
    "University of Texas MD Anderson",
    "Cleveland Clinic",
    "University College London",
    "Karolinska Institutet",
    "University of Toronto",
]


class AuthorTrackingStrategy:
    """Discover new papers from top ENT researchers and institutions."""

    def __init__(self):
        self._known_authors: list[Author] = []

    async def discover(self) -> tuple[list[DiscoveryItem], list[Author]]:
        items: list[DiscoveryItem] = []
        authors: list[Author] = []

        for institution in _ENT_INSTITUTIONS:
            inst_items, inst_authors = await self._search_institution(institution)
            items.extend(inst_items)
            authors.extend(inst_authors)

        return items, authors

    async def _search_institution(self, institution: str) -> tuple[list[DiscoveryItem], list[Author]]:
        """Search for recent ENT papers from a specific institution."""
        items: list[DiscoveryItem] = []
        authors: list[Author] = []

        try:
            from search_service.config import Settings
            from search_service.service import SearchService

            query = f"({institution}) AND (otolaryngology OR ENT OR otology OR rhinology)"
            svc = SearchService()
            results = await svc.search_all(query, limit=5)

            seen = set()
            for article in results:
                doi = getattr(article, "doi", "") or ""
                if doi in seen:
                    continue
                seen.add(doi)

                item = DiscoveryItem(
                    id=f"auth-{doi or getattr(article, 'id', '')}",
                    title=getattr(article, "title", "") or "",
                    authors=getattr(article, "authors", []) or [],
                    journal=getattr(article, "journal", "") or "",
                    doi=doi,
                    source="PubMed",
                    discovery_strategy=DiscoveryStrategy.AUTHOR_TRACKING,
                )
                items.append(item)

                for author_name in getattr(article, "authors", []) or []:
                    authors.append(Author(name=author_name, institutions=[institution]))

            await svc.aclose()
        except ImportError:
            pass

        return items, authors
