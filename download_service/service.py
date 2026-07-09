"""DownloadService orchestrator.

Resolves an Article to candidate URLs, downloads the best match, and returns
a unified ``DownloadResult``.
"""

from __future__ import annotations

import httpx
import structlog

from download_service.config import Settings, default_settings
from download_service.downloaders.base import BaseDownloader
from download_service.downloaders.pdf import PdfDownloader
from download_service.downloaders.xml import XmlDownloader
from download_service.http_client import create_client
from download_service.logging_config import get_logger
from download_service.models import ContentInfo, DownloadResult, DownloadStatus
from download_service.resolvers.base import BaseResolver
from download_service.resolvers.doi import DOIResolver
from download_service.resolvers.pmc import PMCResolver
from download_service.resolvers.publisher import PublisherResolver
from search_service.models import Article

_LOG = get_logger(__name__)

_PROVIDER_TRIAGE = (
    "pmc",
    "doi",
    "publisher",
)


class DownloadService:
    def __init__(
        self,
        settings: Settings | None = None,
        *,
        client: httpx.AsyncClient | None = None,
        resolvers: list[BaseResolver] | None = None,
        downloaders: dict[str, BaseDownloader] | None = None,
        logger: structlog.stdlib.BoundLogger | None = None,
    ) -> None:
        self._settings = settings or default_settings()
        self._client = client or create_client(self._settings)
        self._logger = logger or _LOG
        self._resolvers: dict[str, BaseResolver] = {}
        self._downloaders: dict[str, BaseDownloader] = {}

        if resolvers is not None:
            for r in resolvers:
                self._resolvers[r.name] = r
        else:
            for klass in (PMCResolver, DOIResolver, PublisherResolver):
                inst = klass(self._client, self._settings)
                self._resolvers[inst.name] = inst

        if downloaders is not None:
            self._downloaders = downloaders
        else:
            self._downloaders = {
                "pdf": PdfDownloader(self._client, self._settings),
                "xml": XmlDownloader(self._client, self._settings),
            }

    @property
    def available_resolvers(self) -> list[str]:
        return list(self._resolvers)

    @property
    def available_downloaders(self) -> list[str]:
        return list(self._downloaders)

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()

    async def __aenter__(self) -> DownloadService:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    # ---- public API -------------------------------------------------------
    async def resolve(self, article: Article) -> list[ContentInfo]:
        """Return all candidate URLs from all resolvers."""
        results: list[ContentInfo] = []
        for resolver in self._resolvers.values():
            try:
                candidates = await resolver.resolve(article)
                results.extend(candidates)
            except Exception:
                self._logger.warning("resolver_failed", resolver=resolver.name)
        return results

    async def download(
        self,
        article: Article,
        download_type: str = "pdf",
    ) -> DownloadResult:
        """Resolve and download the best match for ``article``.

        Iterates resolvers in a defined priority, tries each candidate URL
        through the matching downloader, and returns the first successful
        result.
        """
        article_id = article.derive_id()

        downloader = self._downloaders.get(download_type)
        if downloader is None:
            raise ValueError(f"Unknown download_type: {download_type}")

        candidates = await self.resolve(article)

        # Prefer resolvers in priority order.
        seen = set()
        ordered = []
        for source_name in _PROVIDER_TRIAGE:
            for c in candidates:
                if c.source == source_name and c.url not in seen:
                    ordered.append(c)
                    seen.add(c.url)
        # Append any extras not yet seen.
        for c in candidates:
            if c.url not in seen:
                ordered.append(c)
                seen.add(c.url)

        if not ordered:
            return DownloadResult(
                article_id=article_id,
                source="none",
                download_type=download_type,
                status=DownloadStatus.FAILED,
                metadata={"error": "no_content"},
            )

        for candidate in ordered:
            result = await downloader.download(
                candidate.url,
                article_id,
                source=candidate.source,
                license_str=candidate.license,
            )
            if result.status == DownloadStatus.COMPLETED:
                return result
        # All candidates failed. Return the last failure.
        return result
