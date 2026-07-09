from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, description="Search query")
    max_results: int = Field(default=10, ge=1, le=50, description="Maximum articles to return")


class ArticleResponse(BaseModel):
    id: str = ""
    title: str = ""
    doi: str = ""
    pmid: str = ""
    pmcid: str = ""
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    journal: str = ""
    abstract: str = ""


class SearchResponse(BaseModel):
    articles: list[ArticleResponse] = Field(default_factory=list)
    total: int = 0
    elapsed_ms: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
