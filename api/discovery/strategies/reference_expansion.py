"""Reference expansion strategy — follows references of highly ranked papers.

Uses OpenAlex and Europe PMC to extract reference lists from recent papers.
"""

from __future__ import annotations

from api.discovery.models import DiscoveryItem, DiscoveryStrategy


class ReferenceExpansionStrategy:
    """Discover papers by following references of highly ranked papers."""

    async def discover(self) -> list[DiscoveryItem]:
        items: list[DiscoveryItem] = []

        try:
            from api.digest.generator import DigestGenerator

            gen = DigestGenerator()
            recent_papers = gen.get_trending_papers(limit=10)

            for paper in recent_papers:
                if paper.doi:
                    refs = await self._get_references(paper.doi)
                    items.extend(refs)
        except ImportError:
            pass

        return items

    async def _get_references(self, doi: str) -> list[DiscoveryItem]:
        """Get references of a paper via OpenAlex."""
        try:
            import httpx

            url = f"https://api.openalex.org/works/doi:{doi}"
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return []

                data = resp.json()
                items = []
                for ref in data.get("referenced_works", [])[:10]:
                    ref_id = ref.split("/")[-1]
                    ref_url = f"https://api.openalex.org/works/{ref_id}"
                    ref_resp = await client.get(ref_url)
                    if ref_resp.status_code != 200:
                        continue
                    ref_data = ref_resp.json()

                    item = DiscoveryItem(
                        id=f"ref-{ref_id}",
                        title=ref_data.get("title", "") or "",
                        authors=[a.get("author", {}).get("display_name", "")
                                 for a in ref_data.get("authorships", [])],
                        journal=ref_data.get("host_venue", {}).get("display_name", "") or "",
                        doi=ref_data.get("doi", "").replace("https://doi.org/", ""),
                        abstract=ref_data.get("abstract_inverted_index", ""),
                        source="OpenAlex",
                        discovery_strategy=DiscoveryStrategy.REFERENCE_EXPANSION,
                        citation_count=ref_data.get("cited_by_count", 0),
                    )
                    items.append(item)
                return items
        except Exception:
            return []
