"""PMC resolver — uses NCBI / OA API for PDF and XML access.

The OA API returns FTP or HTTPS URLs for full-text articles. The resolver also
constructs URLs directly from the PMCID when the OA API is unreachable.
"""

from __future__ import annotations

import re

import httpx

from download_service.config import Settings
from download_service.models import ContentInfo
from download_service.resolvers.base import BaseResolver
from search_service.models import Article

# Regex to extract pmcid from a string like "PMC1234567" or pmcid="PMC1234567".
_PMCID_RE = re.compile(r"PMC(\d+)", re.IGNORECASE)


class PMCResolver(BaseResolver):
    name = "pmc"

    def __init__(self, client: httpx.AsyncClient, settings: Settings) -> None:
        self._client = client
        self._settings = settings

    async def resolve(self, article: Article) -> list[ContentInfo]:
        candidates: list[ContentInfo] = []
        pmcid = self._extract_pmcid(article)

        if pmcid:
            # Direct NCBI PDF URL (works for open-access articles)
            candidates.append(
                ContentInfo(
                    url=f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/",
                    mime_type="application/pdf",
                    source=self.name,
                )
            )
            candidates.append(
                ContentInfo(
                    url=f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/main.pdf",
                    mime_type="application/pdf",
                    source=self.name,
                )
            )
            # XML (full text) via NCBI ID Converter or direct EUtils retrieval.
            # The most reliable XML path is EFetch:
            candidates.append(
                ContentInfo(
                    url=(
                        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
                        f"?db=pmc&id={pmcid}&rettype=xml&retmode=xml"
                    ),
                    mime_type="application/xml",
                    source=self.name,
                )
            )
        return candidates

    @staticmethod
    def _extract_pmcid(article: Article) -> str | None:
        return article.pmcid or None