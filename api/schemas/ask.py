from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=1, description="Research question")
    llm_provider: str | None = Field(default=None, description="LLM provider override")
    temperature: float | None = Field(default=None, ge=0.0, le=2.0, description="LLM temperature")
    max_tokens: int | None = Field(default=None, ge=1, le=8192, description="Max tokens in response")


class ChunkInfo(BaseModel):
    document_id: str = ""
    text: str = ""
    score: float = 0.0
    heading: str = ""


class AnswerResponse(BaseModel):
    answer: str = ""
    sources: list[str] = Field(default_factory=list)
    citations: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.0
    llm_model: str = ""
    llm_provider: str = ""
    llm_elapsed_ms: float = 0.0


class AskResponse(BaseModel):
    answer: AnswerResponse
    chunks: list[ChunkInfo] = Field(default_factory=list)
    elapsed_ms: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
