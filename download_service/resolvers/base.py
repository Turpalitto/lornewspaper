"""Abstract resolver + concrete implementations.

Resolvers turn an Article into a list of ``ContentInfo`` candidates (URLs to
download). Each resolver handles a different identifier/source.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from download_service.models import ContentInfo
from search_service.models import Article


class BaseResolver(ABC):
    """Produce candidate download URLs for an article.

    Implementations should return URLs that the downloader can stream directly.
    """

    name: str

    @abstractmethod
    async def resolve(self, article: Article) -> list[ContentInfo]:
        ...