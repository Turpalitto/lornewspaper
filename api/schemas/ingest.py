from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    query: str = Field(min_length=1, description="Search and ingest query")
    max_results: int = Field(default=5, ge=1, le=20, description="Maximum articles to ingest")
    download_dir: str | None = Field(default=None, description="Custom download directory")


class DownloadRequest(BaseModel):
    query: str = Field(min_length=1, description="Search and download query")
    max_results: int = Field(default=5, ge=1, le=20, description="Maximum articles to download")


class IngestDocumentResponse(BaseModel):
    document_id: str = ""
    status: str = ""
    chunks: int = 0


class IngestResponse(BaseModel):
    documents: list[IngestDocumentResponse] = Field(default_factory=list)
    total: int = 0
    elapsed_ms: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DownloadResponse(BaseModel):
    articles: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0
    elapsed_ms: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
