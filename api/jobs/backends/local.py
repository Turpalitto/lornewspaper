"""In-memory job queue backend with asyncio worker.

Supports:
  - Enqueue/dequeue
  - Status tracking
  - Progress updates
  - Cancellation
  - Retries
  - Persistence via list[Job] (in-memory)

Architecture allows swapping for arq/Redis, Celery/RabbitMQ, or Dramatiq
by implementing the JobBackend ABC.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from typing import Any

import structlog

from api.jobs.backends.base import JobBackend
from api.jobs.models import Job, JobProgress, JobStatus

_LOG = structlog.get_logger("api.jobs")


class LocalJobBackend(JobBackend):
    """In-memory job queue with asyncio-based worker pool."""

    def __init__(self, worker_concurrency: int = 2):
        self._jobs: dict[str, Job] = {}
        self._queue: asyncio.Queue[Job] = asyncio.Queue()
        self._worker_concurrency = worker_concurrency
        self._workers: list[asyncio.Task] = []
        self._running = False
        self._handlers: dict[str, Any] = {}

    def register_handler(self, job_type: str, handler: Any) -> None:
        self._handlers[job_type] = handler

    async def start(self) -> None:
        self._running = True
        self._workers = [
            asyncio.create_task(self._worker_loop(i))
            for i in range(self._worker_concurrency)
        ]
        _LOG.info("job_workers_started", count=self._worker_concurrency)

    async def stop(self) -> None:
        self._running = False
        for w in self._workers:
            w.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        _LOG.info("job_workers_stopped")

    async def enqueue(self, job: Job) -> None:
        job.status = JobStatus.PENDING
        self._jobs[job.id] = job
        await self._queue.put(job)

    async def dequeue(self, job_type: str | None = None) -> Job | None:
        try:
            while self._running:
                job = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                if job_type and job.type != job_type:
                    await self._queue.put(job)
                    continue
                return job
        except asyncio.TimeoutError:
            return None
        return None

    async def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    async def list(self, limit: int = 50, offset: int = 0) -> list[Job]:
        all_jobs = sorted(
            self._jobs.values(),
            key=lambda j: j.created_at,
            reverse=True,
        )
        return all_jobs[offset:offset + limit]

    async def update_status(self, job_id: str, status: JobStatus) -> None:
        if job := self._jobs.get(job_id):
            job.status = status
            if status == JobStatus.RUNNING:
                job.started_at = datetime.now(UTC)
            elif status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
                job.completed_at = datetime.now(UTC)

    async def update_progress(self, job_id: str, progress: JobProgress) -> None:
        if job := self._jobs.get(job_id):
            job.progress = progress

    async def set_result(self, job_id: str, result: dict[str, Any]) -> None:
        if job := self._jobs.get(job_id):
            job.result = result
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now(UTC)

    async def set_error(self, job_id: str, error: str) -> None:
        if job := self._jobs.get(job_id):
            job.error = error
            job.status = JobStatus.FAILED
            job.completed_at = datetime.now(UTC)

    async def cancel(self, job_id: str) -> bool:
        if job := self._jobs.get(job_id):
            if job.status in (JobStatus.PENDING, JobStatus.RUNNING):
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.now(UTC)
                return True
        return False

    async def _worker_loop(self, worker_id: int) -> None:
        _LOG.debug("worker_started", worker_id=worker_id)
        while self._running:
            try:
                job = await asyncio.wait_for(self._queue.get(), timeout=2.0)
            except asyncio.TimeoutError:
                continue

            handler = self._handlers.get(job.type)
            if handler is None:
                _LOG.error("no_handler_for_job", job_type=job.type, job_id=job.id)
                await self.set_error(job.id, f"No handler registered for job type: {job.type}")
                continue

            try:
                await self.update_status(job.id, JobStatus.RUNNING)
                await handler(job)
            except asyncio.CancelledError:
                await self.update_status(job.id, JobStatus.CANCELLED)
                break
            except Exception as exc:
                job.retry_count += 1
                if job.retry_count < job.max_retries:
                    _LOG.warning("job_retry", job_id=job.id, attempt=job.retry_count, error=str(exc))
                    job.status = JobStatus.PENDING
                    await self._queue.put(job)
                else:
                    await self.set_error(job.id, str(exc))
                    _LOG.error("job_failed", job_id=job.id, error=str(exc))
