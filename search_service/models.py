"""Unified article model returned by every provider.

All provider-specific responses are mapped into this single shape so
downstream consumers never depend on a source's schema. ``provenance`` records
which providers contributed to a (possibly merged) record; ``raw_response`` is
optional and only populated when ``include_raw=True``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(UTC)


class Article(BaseModel):
    """A normalized literature record."""

    # Core required-by-contract fields (None when a source lacks them).
    title: str | None = None
    authors: list[str] = Field(default_factory=list)
    journal: str | None = None
    year: int | None = None
    doi: str | None = None
    pmid: str | None = None
    abstract: str | None = None
    keywords: list[str] = Field(default_factory=list)
    mesh_terms: list[str] = Field(default_factory=list)
    url: str | None = None
    pdf_url: str | None = None
    source: str  # provider name that produced this record

    # Optional enrichment fields.
    id: str | None = None
    pmcid: str | None = None
    language: str | None = None
    publication_type: list[str] = Field(default_factory=list)
    publisher: str | None = None
    volume: str | None = None
    issue: str | None = None
    pages: str | None = None
    license: str | None = None
    retrieved_at: datetime = Field(default_factory=_now)

    # Provenance + optional raw payload.
    provenance: list[str] = Field(default_factory=list)
    raw_response: dict[str, Any] | None = None

    def derive_id(self) -> str:
        """Stable identity: prefer DOI, then PMID, then PMCID, then title."""
        if self.doi:
            return self.doi.lower().strip()
        if self.pmid:
            return f"pmid:{self.pmid}"
        if self.pmcid:
            return f"pmcid:{self.pmcid.lower().strip()}"
        return f"title:{(self.title or '').lower().strip()}"
