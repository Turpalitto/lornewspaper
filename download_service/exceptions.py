"""DownloadService exception hierarchy."""

from __future__ import annotations


class DownloadServiceError(Exception):
    """Base for all DownloadService errors."""


class NoContentFoundError(DownloadServiceError, ValueError):
    """A resolver found no downloadable content for the given identifier."""


class DownloadFailedError(DownloadServiceError, RuntimeError):
    """A downloader failed after exhausting retries."""


class ContentTypeMismatchError(DownloadServiceError, ValueError):
    """Downloaded content MIME type does not match the expected type."""


class DownloadValidationError(DownloadServiceError, ValueError):
    """Content failed validation (MIME type or magic bytes)."""


class IntegrityError(DownloadServiceError, RuntimeError):
    """SHA256 checksum verification failed."""