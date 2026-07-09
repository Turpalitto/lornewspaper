"""Data models for ResearchAgent."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from knowledge_base.models import Chunk, KnowledgeDocument, SearchResult


class AgentStatus(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentRequest(BaseModel):
    query: str = ""
    document_id: str = ""
    max_results: int = 10
    score_threshold: float = 0.0
    metadata_filter: dict[str, Any] = Field(default_factory=dict)
    llm_provider: str = ""
    temperature: float = 0.3
    max_tokens: int = 1024
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Citation(BaseModel):
    document_id: str
    title: str
    authors: list[str] = Field(default_factory=list)
    source: str = ""
    year: int | None = None
    doi: str = ""
    pmid: str = ""
    relevant_quote: str = ""


class Answer(BaseModel):
    answer: str = ""
    citations: list[Citation] = Field(default_factory=list)
    chunks: list[Chunk] = Field(default_factory=list)
    confidence: float = 0.0
    sources: list[str] = Field(default_factory=list)
    reasoning_summary: str = ""
    elapsed_ms: float = 0.0
    llm_model: str = ""
    llm_provider: str = ""


class AgentResult(BaseModel):
    status: AgentStatus = AgentStatus.IDLE
    request: AgentRequest = Field(default_factory=AgentRequest)
    documents: list[KnowledgeDocument] = Field(default_factory=list)
    articles: list[dict[str, Any]] = Field(default_factory=list)
    answer: Answer = Field(default_factory=Answer)
    search_result: SearchResult | None = None
    error: str = ""
    elapsed_ms: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
