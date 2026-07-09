"""Job data models."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobProgress(BaseModel):
    current: int = 0
    total: int = 0
    message: str = ""

    @property
    def percent(self) -> float:
        if self.total <= 0:
            return 0.0
        return round((self.current / self.total) * 100, 1)


class Job(BaseModel):
    id: str
    type: str
    status: JobStatus = JobStatus.PENDING
    params: dict[str, Any] = Field(default_factory=dict)
    progress: JobProgress = Field(default_factory=JobProgress)
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    retry_count: int = 0
    max_retries: int = 3


class JobCreate(BaseModel):
    type: str
    params: dict[str, Any] = Field(default_factory=dict)


class JobListResponse(BaseModel):
    items: list[Job] = Field(default_factory=list)
    total: int = 0
