"""Publisher resolver — extracts direct URLs from Article metadata fields.

This is a catch-all fallback: if the article carries a ``url`` or ``pdf_url``
from the original provider, those are returned as download candidates.
"""

from __future__ import annotations

import httpx

from download_service.config import Settings
from download_service.models import ContentInfo
from download_service.resolvers.base import BaseResolver
from search_service.models import Article


class PublisherResolver(BaseResolver):
    name = "publisher"

    def __init__(self, client: httpx.AsyncClient, settings: Settings) -> None:
        self._client = client
        self._settings = settings

    async def resolve(self, article: Article) -> list[ContentInfo]:
        candidates: list[ContentInfo] = []

        if article.pdf_url:
            candidates.append(
                ContentInfo(url=article.pdf_url, mime_type="application/pdf", source=self.name)
            )
        if article.url and article.url != article.pdf_url:
            candidates.append(
                ContentInfo(url=article.url, mime_type="text/html", source=self.name)
            )
        return candidates