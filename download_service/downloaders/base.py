"""Base downloader — streaming HTTP download with resume, retry, rate limit,
SHA256 checksumming, content-type and magic-byte validation.

Subclasses configure ``download_type`` and ``expected_content_type``.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import time
from collections.abc import Set as AbstractSet
from datetime import UTC
from typing import Any

import httpx

from download_service.cache import cache_path, resolve_cache_path
from download_service.config import DownloaderConfig, Settings
from download_service.exceptions import (
    ContentTypeMismatchError,
    DownloadValidationError,
)
from download_service.models import DownloadResult, DownloadStatus
from search_service.rate_limit import AsyncRateLimiter
from search_service.retry import async_retry

_CHUNK = 256 * 1024

# MIME types considered valid for each content category.
_PDF_MIMES: frozenset[str] = frozenset({"application/pdf"})
_XML_MIMES: frozenset[str] = frozenset({
    "application/xml",
    "text/xml",
    "application/xhtml+xml",
})
_HTML_MIMES: frozenset[str] = frozenset({"text/html"})
_LANDING_PAGE_MIMES: frozenset[str] = _HTML_MIMES

_PDF_MAGIC = b"%PDF-"

# HTML error pages often start with <!DOCTYPE html>, <html>, or <!DOCTYPE HTML>.
_HTML_PREFIXES = (b"<!DOCTYPE", b"<html", b"<HTML")

# Additional MIME types accepted when resume is in progress (already validated
# earlier content, no need to re-check on subsequent chunks).
_RESUME_SKIP_MIMES: frozenset[str] = frozenset()


class BaseDownloader:
    """Stream a file to disk, verify SHA256, move to cache.

    Subclasses override ``download_type``, ``expected_content_type``, and
    ``valid_mime_types`` (set of accepted MIME types).
    """

    download_type: str
    expected_content_type: str
    valid_mime_types: AbstractSet[str] = frozenset()
    """Set of MIME types accepted by this downloader."""

    _host_limiters: dict[str, AsyncRateLimiter] = {}

    def __init__(self, client: httpx.AsyncClient, settings: Settings) -> None:
        self._client = client
        self._settings = settings
        self._cfg = settings.downloaders.get(self.download_type) or DownloaderConfig()

    # ---- public -----------------------------------------------------------
    async def download(
        self,
        url: str,
        identifier: str,
        *,
        source: str = "",
        license_str: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DownloadResult:
        start = time.perf_counter()
        result = DownloadResult(
            article_id=identifier,
            source=source or "unknown",
            download_type=self.download_type,
            status=DownloadStatus.FAILED,
            metadata=metadata or {},
        )

        limiter = self._host_limiter(url)

        try:
            file_path, size, sha256_hex, mime_type = await self._stream(url, limiter, identifier)
            elapsed = time.perf_counter() - start
            result.file_path = file_path
            result.size = size
            result.sha256 = sha256_hex
            result.mime_type = mime_type
            result.downloaded_at = _now()
            result.elapsed = round(elapsed, 3)
            result.license = license_str
            result.status = DownloadStatus.COMPLETED
        except (ContentTypeMismatchError, DownloadValidationError) as exc:
            result.metadata["error"] = type(exc).__name__
            result.elapsed = round(time.perf_counter() - start, 3)
        except Exception as exc:
            result.metadata["error"] = type(exc).__name__
            result.elapsed = round(time.perf_counter() - start, 3)
        return result

    # ---- internals --------------------------------------------------------
    async def _stream(
        self,
        url: str,
        limiter: AsyncRateLimiter,
        identifier: str,
    ) -> tuple[str, int, str, str]:
        """Download, compute sha256 + size, then move file to cache."""

        partial = resolve_cache_path(self._settings.cache_dir, identifier, self.download_type)

        @async_retry(max_attempts=self._cfg.retry_attempts)
        async def _do() -> tuple[str, int, str, str]:
            await limiter.acquire()

            resume_at = _file_size(partial)
            headers = {"Range": f"bytes={resume_at}-"} if resume_at else {}

            async with self._client.stream(
                "GET", url, headers=headers, timeout=self._cfg.timeout
            ) as resp:
                raw_mime = resp.headers.get("content-type", "")
                mime = (
                    raw_mime.split(";")[0].strip().lower()
                    if raw_mime
                    else self.expected_content_type
                )

                if resp.status_code == 416:
                    # Range unsatisfiable – re-read partial as-is (already validated).
                    mode = "rb"
                elif resp.status_code in (200, 206):
                    self._assert_mime_type(mime, url, resume_at)
                    mode = "ab" if (resp.status_code == 206 or resume_at > 0) else "wb"
                elif resp.status_code in (429, *range(500, 512)):
                    from search_service.retry import TransientHTTPError
                    raise TransientHTTPError(response=resp, request=resp.request)
                else:
                    resp.raise_for_status()
                    return "", 0, "", ""

                sha = hashlib.sha256()
                file_size = resume_at
                loop = asyncio.get_running_loop()
                magic_checked = False

                with open(partial, mode) as f:
                    if resp.status_code != 416:
                        async for chunk in resp.aiter_bytes(chunk_size=_CHUNK):
                            if not magic_checked and self.download_type == "pdf":
                                self._assert_magic(chunk)
                                magic_checked = True
                            await loop.run_in_executor(None, f.write, chunk)
                            file_size += len(chunk)
                            await loop.run_in_executor(None, sha.update, chunk)

            sha256_hex = sha.hexdigest()
            ext = self.download_type
            final = cache_path(sha256_hex, ext, self._settings)

            if os.path.isfile(final):
                _cleanup(partial)
                return final, file_size, sha256_hex, mime

            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, os.renames, partial, final)
            return final, file_size, sha256_hex, mime

        return await _do()

    # ---- validation -------------------------------------------------------
    def _assert_mime_type(self, mime: str, url: str, resume_at: int) -> None:
        # Skipped if valid MIMEs not configured (some implementations may run validation
        # differently).
        if not self.valid_mime_types:
            return

        if mime not in self.valid_mime_types:
            raise ContentTypeMismatchError(
                f"Expected one of {sorted(self.valid_mime_types)}, got '{mime}' for {url}"
            )

        # Reject HTML pages when PDF is expected (HTML is often a search-engine
        # result page or a "404" page served with text/html).
        if self.download_type == "pdf" and mime in _HTML_MIMES:
            raise ContentTypeMismatchError(
                f"Expected PDF but server returned HTML page ({url})"
            )

    # ---- magic bytes -------------------------------------------------------
    def _assert_magic(self, chunk: bytes) -> None:
        if not chunk.startswith(_PDF_MAGIC):
            raise DownloadValidationError(
                f"Expected PDF magic bytes {_PDF_MAGIC!r}, "
                f"got {chunk[:8]!r}"
            )

    def _host_limiter(self, url: str) -> AsyncRateLimiter:
        host = httpx.URL(url).host
        if host not in self._host_limiters:
            self._host_limiters[host] = AsyncRateLimiter(
                rate=self._cfg.rate, burst=self._cfg.burst
            )
        return self._host_limiters[host]


def _now():
    from datetime import datetime
    return datetime.now(UTC)


def _file_size(path: str) -> int:
    try:
        return os.path.getsize(path)
    except FileNotFoundError:
        return 0


def _cleanup(path: str) -> None:
    try:
        if os.path.isfile(path):
            os.remove(path)
    except OSError:
        pass