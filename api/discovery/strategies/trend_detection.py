"""Trend detection strategy — identify rapidly growing ENT topics.

Uses PubMed trend analysis to detect:
  - Emerging topics (rapid growth in recent publications)
  - New diseases, procedures, devices, drugs, surgical techniques
"""

from __future__ import annotations

from api.discovery.models import DiscoveryItem, DiscoveryStrategy, TrendTopic

# Topics to monitor for growth
_MONITORED_TOPICS = [
    ("artificial intelligence", "AI"),
    ("machine learning", "AI"),
    ("deep learning", "AI"),
    ("endoscopic surgery", "endoscopic"),
    ("robotic surgery", "robotic"),
    ("gene therapy", "gene therapy"),
    ("hearing restoration", "hearing"),
    ("regenerative medicine", "regenerative"),
    ("microbiome", "microbiome"),
    ("3d printing", "3d printing"),
    ("telemedicine", "telemedicine"),
    ("augmented reality", "AR/VR"),
    ("artificial cochlea", "hearing"),
    ("bioprinting", "bioprinting"),
    ("nanoparticle", "nanotechnology"),
    ("immunotherapy", "immunotherapy"),
    ("precision medicine", "precision medicine"),
    ("wearable device", "wearable"),
    ("single-cell", "genomics"),
    ("crispr", "gene therapy"),
]

# Novelty detection keywords
_NEW_PROCEDURES = [
    "novel technique", "new approach", "innovative procedure",
    "first-in-human", "first-in-man", "new surgical technique",
    "новая методика", "новый подход",
]

_NEW_DEVICES = [
    "novel device", "new device", "implantable",
    "wearable sensor", "smart", "новое устройство",
]

_NEW_DRUGS = [
    "novel therapeutic", "new drug", "first-in-class",
    "новый препарат", "новая терапия",
]


class TrendDetectionStrategy:
    """Detect rapidly growing ENT research topics."""

    async def discover(self) -> tuple[list[DiscoveryItem], list[TrendTopic], list[TrendTopic]]:
        items: list[DiscoveryItem] = []
        trending: list[TrendTopic] = []
        emerging: list[TrendTopic] = []

        for topic_query, category in _MONITORED_TOPICS:
            topic, is_emerging = await self._analyze_topic(topic_query, category)
            if topic:
                if is_emerging:
                    emerging.append(topic)
                else:
                    trending.append(topic)

            # Also try to find papers on this topic
            topic_papers = await self._search_topic(topic_query)
            items.extend(topic_papers)

        # Sort by growth rate
        trending.sort(key=lambda t: t.growth_rate, reverse=True)
        emerging.sort(key=lambda t: t.growth_rate, reverse=True)

        return items, trending, emerging

    async def _analyze_topic(self, query: str, category: str) -> tuple[TrendTopic | None, bool]:
        """Analyze a topic's growth trend via PubMed."""
        try:
            import httpx
            from datetime import date, timedelta

            today = date.today()
            this_year = today.year

            # Get publication counts for current year
            this_count = await self._pubmed_count(query, this_year)
            last_count = await self._pubmed_count(query, this_year - 1)

            if this_count == 0 and last_count == 0:
                return None, False

            growth = ((this_count - last_count) / max(last_count, 1)) * 100
            is_emerging = growth > 50 and this_count > 5

            return TrendTopic(
                name=query,
                description=f"Recent publications on {query} in ENT: {this_count} papers",
                growth_rate=round(growth, 1),
                paper_count=this_count + last_count,
                momentum="exploding" if growth > 100 else "growing" if growth > 20 else "stable",
                related_terms=[category, query],
                emerging=is_emerging,
            ), is_emerging

        except Exception:
            return None, False

    async def _pubmed_count(self, query: str, year: int) -> int:
        """Get publication count for a query in a specific year via PubMed."""
        import httpx

        url = (
            f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            f"?db=pubmed&term={query}+AND+{year}[pdat]&retmax=0&format=json"
        )
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return 0
            data = resp.json()
            return int(data.get("esearchresult", {}).get("count", "0"))

    async def _search_topic(self, query: str) -> list[DiscoveryItem]:
        """Search for recent papers on a topic."""
        try:
            from search_service.config import Settings
            from search_service.service import SearchService

            ent_query = f"({query}) AND (otolaryngology OR ENT)"
            svc = SearchService()
            results = await svc.search_all(ent_query, limit=5)

            items = []
            for article in results:
                item = DiscoveryItem(
                    id=f"trend-{getattr(article, 'id', '') or getattr(article, 'doi', '')}",
                    title=getattr(article, "title", "") or "",
                    authors=getattr(article, "authors", []) or [],
                    journal=getattr(article, "journal", "") or "",
                    doi=getattr(article, "doi", "") or "",
                    abstract=getattr(article, "abstract", "") or "",
                    source="PubMed",
                    discovery_strategy=DiscoveryStrategy.TREND_DETECTION,
                )
                items.append(item)

            await svc.aclose()
            return items
        except ImportError:
            return []
