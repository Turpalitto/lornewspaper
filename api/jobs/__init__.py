"""Background job queue for async ingestion and processing."""

from api.jobs.service import JobService, get_job_service

__all__ = ["JobService", "get_job_service"]
