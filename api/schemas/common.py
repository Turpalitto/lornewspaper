from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    request_id: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PaginationRequest(BaseModel):
    cursor: str | None = Field(default=None, description="Opaque cursor for pagination")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T] = Field(default_factory=list)
    next_cursor: str | None = Field(default=None, description="Cursor for next page")
    has_more: bool = Field(default=False)
    limit: int = Field(default=20)
