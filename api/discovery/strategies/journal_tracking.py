"""Journal tracking strategy — monitors 8 key ENT journals for new publications."""

from __future__ import annotations

from api.discovery.models import DiscoveryItem, DiscoveryStrategy, JournalInfo

_TRACKED_JOURNALS = [
    "The Laryngoscope",
    "Otolaryngology-Head and Neck Surgery",
    "Rhinology",
    "Clinical Otolaryngology",
    "JAMA Otolaryngology-Head & Neck Surgery",
    "European Archives of Oto-Rhino-Laryngology",
    "International Journal of Pediatric Otorhinolaryngology",
    "Otology & Neurotology",
]

_JOURNAL_ISSN: dict[str, str] = {
    "The Laryngoscope": "0023-852X",
    "Otolaryngology-Head and Neck Surgery": "0194-5998",
    "Rhinology": "0300-0729",
    "Clinical Otolaryngology": "1749-4478",
    "JAMA Otolaryngology-Head & Neck Surgery": "2168-6181",
    "European Archives of Oto-Rhino-Laryngology": "0937-4477",
    "International Journal of Pediatric Otorhinolaryngology": "0165-5876",
    "Otology & Neurotology": "1531-7129",
}

_JOURNAL_IF: dict[str, float] = {
    "The Laryngoscope": 2.970,
    "Otolaryngology-Head and Neck Surgery": 3.984,
    "Rhinology": 4.657,
    "Clinical Otolaryngology": 3.446,
    "JAMA Otolaryngology-Head & Neck Surgery": 6.223,
    "European Archives of Oto-Rhino-Laryngology": 2.503,
    "International Journal of Pediatric Otorhinolaryngology": 1.530,
    "Otology & Neurotology": 2.344,
}


class JournalTrackingStrategy:
    """Discover new papers from 8 key ENT journals."""

    async def discover(self) -> tuple[list[DiscoveryItem], list[JournalInfo]]:
        items: list[DiscoveryItem] = []
        journals: list[JournalInfo] = []

        for journal_name in _TRACKED_JOURNALS:
            journal_items = await self._search_journal(journal_name)
            items.extend(journal_items)

            journals.append(JournalInfo(
                name=journal_name,
                issn=_JOURNAL_ISSN.get(journal_name, ""),
                impact_factor=_JOURNAL_IF.get(journal_name, 0),
                papers_this_period=len(journal_items),
            ))

        return items, journals

    async def _search_journal(self, journal_name: str) -> list[DiscoveryItem]:
        """Search for recent papers from a specific journal."""
        items: list[DiscoveryItem] = []

        try:
            import httpx

            encoded = journal_name.replace(" ", "+")
            url = (
                f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
                f"?db=pubmed&term={encoded}[jour]+AND+2025[pdat]&retmax=10&format=json"
            )

            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return items

                data = resp.json()
                ids = data.get("esearchresult", {}).get("idlist", [])

                if not ids:
                    return items

                fetch_url = (
                    f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
                    f"?db=pubmed&id={','.join(ids)}&retmode=json&rettype=abstract"
                )
                fetch_resp = await client.get(fetch_url)
                if fetch_resp.status_code != 200:
                    return items

                fetch_data = fetch_resp.json()
                for uid, article_data in fetch_data.get("result", {}).items():
                    if uid == "uids":
                        continue

                    item = DiscoveryItem(
                        id=f"jour-{uid}",
                        title=article_data.get("title", "") or "",
                        authors=[a.get("name", "") for a in article_data.get("authors", [])],
                        journal=journal_name,
                        pmid=str(uid),
                        abstract=article_data.get("abstract", "") or "",
                        source="PubMed",
                        discovery_strategy=DiscoveryStrategy.JOURNAL_TRACKING,
                    )
                    items.append(item)

        except Exception:
            pass

        return items
