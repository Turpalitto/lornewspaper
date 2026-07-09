"""DOI resolver — resolves DOIs to their landing page (possible PDF).

Uses doi.org to follow the redirect chain and detect the final Content-Type.
When the DOI resolves directly to a PDF the ``ContentInfo`` carries ``application/pdf``;
otherwise only the landing page URL is returned (the publisher resolver or PMC may
provide the actual download).
"""

from __future__ import annotations

import httpx

from download_service.config import Settings
from download_service.models import ContentInfo
from download_service.resolvers.base import BaseResolver
from search_service.models import Article


class DOIResolver(BaseResolver):
    name = "doi"

    def __init__(self, client: httpx.AsyncClient, settings: Settings) -> None:
        self._client = client
        self._settings = settings

    async def resolve(self, article: Article) -> list[ContentInfo]:
        doi = article.doi
        if not doi:
            return []

        url = f"https://doi.org/{doi.lstrip('doi:').lstrip('/')}"
        try:
            resp = await self._client.head(url, follow_redirects=True)
            final_url = str(resp.url)
            content_type = resp.headers.get("content-type", "")
            # Detect PDF even through redirects (some servers serve PDF at the DOI).
            if "pdf" in content_type.lower():
                return [
                    ContentInfo(
                        url=final_url,
                        mime_type="application/pdf",
                        source=self.name,
                        resolved_redirect=True,
                    )
                ]
            # The landing page is the best we have.
            return [
                ContentInfo(
                    url=final_url,
                    mime_type="text/html",
                    source=self.name,
                    resolved_redirect=True,
                )
            ]
        except Exception:
            return []