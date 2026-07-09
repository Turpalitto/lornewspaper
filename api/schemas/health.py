from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    uptime_seconds: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ReadinessResponse(BaseModel):
    status: str = "ok"
    agent_ready: bool = False
    knowledge_base_ready: bool = False
    cache_ready: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class LivenessResponse(BaseModel):
    status: str = "alive"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
