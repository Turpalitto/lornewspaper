from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    title: str = ""
    authors: list[str] = Field(default_factory=list)
    source: str = ""
    year: int | None = None
    doi: str = ""


class DocumentRecord(BaseModel):
    document_id: str = ""
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)
    chunk_count: int = 0
    created_at: str = ""


class DocumentListResponse(BaseModel):
    items: list[DocumentRecord] = Field(default_factory=list)
    next_cursor: str | None = None
    has_more: bool = False
    limit: int = 20


class DocumentDetailResponse(BaseModel):
    document_id: str = ""
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)
    chunks: list[dict[str, Any]] = Field(default_factory=list)
    created_at: str = ""


class ChunkRecord(BaseModel):
    chunk_id: str = ""
    text: str = ""
    heading: str = ""
    chunk_index: int = 0


class ChunkListResponse(BaseModel):
    items: list[ChunkRecord] = Field(default_factory=list)
    next_cursor: str | None = None
    has_more: bool = False
    limit: int = 20


class SummaryResponse(BaseModel):
    document_id: str = ""
    summary: str = ""
    llm_model: str = ""
    llm_provider: str = ""
    elapsed_ms: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SimilarResponse(BaseModel):
    document_id: str = ""
    analysis: str = ""
    related_documents: list[str] = Field(default_factory=list)
    llm_model: str = ""
    llm_provider: str = ""
    elapsed_ms: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
