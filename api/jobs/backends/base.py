"""Abstract job queue backend."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from api.jobs.models import Job, JobProgress, JobStatus


class JobBackend(ABC):
    @abstractmethod
    async def enqueue(self, job: Job) -> None:
        ...

    @abstractmethod
    async def dequeue(self, job_type: str | None = None) -> Job | None:
        ...

    @abstractmethod
    async def get(self, job_id: str) -> Job | None:
        ...

    @abstractmethod
    async def list(self, limit: int = 50, offset: int = 0) -> list[Job]:
        ...

    @abstractmethod
    async def update_status(self, job_id: str, status: JobStatus) -> None:
        ...

    @abstractmethod
    async def update_progress(self, job_id: str, progress: JobProgress) -> None:
        ...

    @abstractmethod
    async def set_result(self, job_id: str, result: dict[str, Any]) -> None:
        ...

    @abstractmethod
    async def set_error(self, job_id: str, error: str) -> None:
        ...

    @abstractmethod
    async def cancel(self, job_id: str) -> bool:
        ...
