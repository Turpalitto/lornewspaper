"""Models for DocumentProcessingService."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(UTC)


class ProcessingStatus(StrEnum):
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class PageMapping(BaseModel):
    """Maps a logical element to PDF page number(s)."""

    page_number: int
    text_start: int = 0
    text_end: int | None = None


class DocumentMetadata(BaseModel):
    title: str = ""
    abstract: str = ""
    authors: list[str] = Field(default_factory=list)
    journal: str | None = None
    year: int | None = None
    doi: str | None = None


class ExtractedSection(BaseModel):
    heading: str
    content: str
    level: int = 1
    page_mapping: list[PageMapping] = Field(default_factory=list)


class ExtractedReference(BaseModel):
    raw_text: str
    index: str = ""
    doi: str | None = None
    title: str | None = None
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    source: str | None = None


class ExtractedTable(BaseModel):
    caption: str = ""
    headers: list[str] = Field(default_factory=list)
    rows: list[list[str]] = Field(default_factory=list)
    page_number: int = 0
    markdown: str = ""


class ExtractedFigure(BaseModel):
    caption: str = ""
    alt_text: str = ""
    page_number: int = 0
    image_index: int = 0


class ExtractionStats(BaseModel):
    total_pages: int = 0
    total_characters: int = 0
    sections_found: int = 0
    references_found: int = 0
    tables_found: int = 0
    figures_found: int = 0
    ocr_required: bool = False
    ocr_performed: bool = False
    extraction_time_ms: float = 0.0
    errors: list[str] = Field(default_factory=list)


class ProcessedDocument(BaseModel):
    article_id: str
    status: ProcessingStatus
    markdown: str = ""
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)
    sections: list[ExtractedSection] = Field(default_factory=list)
    references: list[ExtractedReference] = Field(default_factory=list)
    tables: list[ExtractedTable] = Field(default_factory=list)
    figures: list[ExtractedFigure] = Field(default_factory=list)
    page_mappings: list[PageMapping] = Field(default_factory=list)
    stats: ExtractionStats = Field(default_factory=ExtractionStats)
    source_file: str = ""
    processing_started_at: datetime | None = None
    processing_completed_at: datetime | None = None
    raw_text: str = ""