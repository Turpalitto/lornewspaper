"""JobService facade — high-level API for job management."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import structlog

from api.jobs.backends.base import JobBackend
from api.jobs.backends.local import LocalJobBackend
from api.jobs.models import Job, JobCreate, JobProgress, JobStatus

_LOG = structlog.get_logger("api.jobs")

_job_service: JobService | None = None


class JobService:
    def __init__(self, backend: JobBackend | None = None):
        self._backend = backend or LocalJobBackend(worker_concurrency=2)

    @property
    def backend(self) -> JobBackend:
        return self._backend

    async def start(self) -> None:
        if isinstance(self._backend, LocalJobBackend):
            await self._backend.start()

    async def stop(self) -> None:
        if isinstance(self._backend, LocalJobBackend):
            await self._backend.stop()

    async def create_job(self, req: JobCreate) -> Job:
        job = Job(
            id=str(uuid.uuid4()),
            type=req.type,
            params=req.params,
            created_at=datetime.now(UTC),
            status=JobStatus.PENDING,
        )
        await self._backend.enqueue(job)
        _LOG.info("job_created", job_id=job.id, job_type=job.type)
        return job

    async def get_job(self, job_id: str) -> Job | None:
        return await self._backend.get(job_id)

    async def list_jobs(self, limit: int = 50, offset: int = 0) -> list[Job]:
        return await self._backend.list(limit=limit, offset=offset)

    async def cancel_job(self, job_id: str) -> bool:
        return await self._backend.cancel(job_id)

    def register_handler(self, job_type: str, handler: Any) -> None:
        if isinstance(self._backend, LocalJobBackend):
            self._backend.register_handler(job_type, handler)


def get_job_service() -> JobService:
    global _job_service
    if _job_service is None:
        _job_service = JobService()
    return _job_service
