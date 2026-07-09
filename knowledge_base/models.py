"""KnowledgeBase models."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class IndexingStatus(StrEnum):
    PENDING = "pending"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"


class Chunk(BaseModel):
    id: str = ""
    document_id: str
    chunk_index: int = 0
    section: str = ""
    heading: str = ""
    text: str = ""
    markdown: str = ""
    page_start: int = 0
    page_end: int = 0
    token_count: int = 0
    word_count: int = 0
    citations: list[str] = Field(default_factory=list)
    tables: list[dict[str, Any]] = Field(default_factory=list)
    figures: list[dict[str, Any]] = Field(default_factory=list)
    previous_chunk: str = ""
    next_chunk: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChunkEmbedding(BaseModel):
    chunk_id: str
    document_id: str
    embedding: list[float] = Field(default_factory=list)
    model: str = ""
    dimensions: int = 0


class DocumentStatistics(BaseModel):
    total_chunks: int = 0
    total_tokens: int = 0
    total_words: int = 0
    total_tables: int = 0
    total_figures: int = 0
    total_citations: int = 0
    embedding_model: str = ""
    chunking_strategy: str = ""
    chunk_overlap: int = 0


class KnowledgeDocument(BaseModel):
    document_id: str
    status: IndexingStatus = IndexingStatus.PENDING
    metadata: dict[str, Any] = Field(default_factory=dict)
    chunks: list[Chunk] = Field(default_factory=list)
    embeddings: list[ChunkEmbedding] = Field(default_factory=list)
    statistics: DocumentStatistics = Field(default_factory=DocumentStatistics)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    source_file: str = ""


class SearchQuery(BaseModel):
    text: str = ""
    embedding: list[float] = Field(default_factory=list)
    top_k: int = 10
    score_threshold: float = 0.0
    metadata_filter: dict[str, Any] = Field(default_factory=dict)
    section_filter: str | None = None
    document_filter: list[str] = Field(default_factory=list)
    hybrid_weight: float = 0.5


class SearchResultItem(BaseModel):
    chunk: Chunk
    score: float = 0.0
    embedding: list[float] = Field(default_factory=list)
    document_metadata: dict[str, Any] = Field(default_factory=dict)


class SearchResult(BaseModel):
    query: SearchQuery
    items: list[SearchResultItem] = Field(default_factory=list)
    total_found: int = 0
    elapsed_ms: float = 0.0