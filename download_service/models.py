"""Download result model.

Unified response from every download operation. Callers receive this instead of
raw files or error tuples, so every download (successful, partial, failed) has
the same shape.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(UTC)


class DownloadStatus(StrEnum):
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class ContentInfo(BaseModel):
    """A candidate resource returned by a resolver (one possible download target)."""

    url: str
    mime_type: str | None = None
    license: str | None = None
    source: str  # resolver name, e.g. "pmc", "doi", "publisher"
    resolved_redirect: bool = False  # True if the URL was reached via redirect


class DownloadResult(BaseModel):
    """Unified result for a single download attempt."""

    article_id: str
    source: str  # resolver name that provided the URL
    download_type: str  # "pdf" or "xml"
    status: DownloadStatus
    file_path: str | None = None
    mime_type: str | None = None
    size: int | None = None
    sha256: str | None = None
    license: str | None = None
    downloaded_at: datetime | None = None
    elapsed: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)