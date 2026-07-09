"""Job handlers — connect job queue to business logic."""

from __future__ import annotations

import os

import structlog

from api.dependencies import get_agent
from api.jobs.models import Job, JobProgress
from research_agent.agent import ResearchAgent

_LOG = structlog.get_logger("api.jobs")


async def handle_ingest(job: Job) -> None:
    """Handle an ingest job: search -> download -> process -> index.

    Runs the full pipeline asynchronously in the background.
    Progress is reported through the job's progress field.
    """
    agent: ResearchAgent | None = None
    try:
        params = job.params
        query = params.get("query", "")
        max_results = int(params.get("max_results", 5))
        download_dir = params.get("download_dir", os.environ.get("DOWNLOAD_DIR", "./downloads"))

        _LOG.info("ingest_job_started", job_id=job.id, query=query, max_results=max_results)

        from api.jobs.service import get_job_service
        svc = get_job_service()

        await svc.backend.update_progress(job.id, JobProgress(
            current=0, total=max_results, message="Starting ingest..."
        ))

        agent = get_agent()

        await svc.backend.update_progress(job.id, JobProgress(
            current=0, total=max_results, message="Searching articles..."
        ))

        from research_agent.workflow import full_ingest_pipeline

        docs = await full_ingest_pipeline(
            query=query,
            max_results=max_results,
            download_dir=download_dir,
        )

        for i, _ in enumerate(docs):
            await svc.backend.update_progress(job.id, JobProgress(
                current=i + 1,
                total=len(docs),
                message=f"Indexed {i + 1}/{len(docs)} documents",
            ))

        await svc.backend.set_result(job.id, {
            "documents": docs,
            "total": len(docs),
        })

        _LOG.info("ingest_job_completed", job_id=job.id, total=len(docs))

    except Exception as exc:
        _LOG.error("ingest_job_failed", job_id=job.id, error=str(exc))
        from api.jobs.service import get_job_service
        svc = get_job_service()
        await svc.backend.set_error(job.id, str(exc))
    finally:
        pass
