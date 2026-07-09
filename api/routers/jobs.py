"""Job queue API router — async background processing."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.jobs.models import Job, JobCreate, JobListResponse
from api.jobs.service import JobService, get_job_service

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=Job, operation_id="create_job")
async def create_job(
    body: JobCreate,
    svc: JobService = Depends(get_job_service),
):
    return await svc.create_job(body)


@router.get("", response_model=JobListResponse, operation_id="list_jobs")
async def list_jobs(
    limit: int = 50,
    offset: int = 0,
    svc: JobService = Depends(get_job_service),
):
    items = await svc.list_jobs(limit=limit, offset=offset)
    return JobListResponse(items=items, total=len(items))


@router.get("/{job_id}", response_model=Job, operation_id="get_job")
async def get_job(
    job_id: str,
    svc: JobService = Depends(get_job_service),
):
    job = await svc.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return job


@router.post("/{job_id}/cancel", response_model=Job, operation_id="cancel_job")
async def cancel_job(
    job_id: str,
    svc: JobService = Depends(get_job_service),
):
    cancelled = await svc.cancel_job(job_id)
    if not cancelled:
        raise HTTPException(status_code=409, detail=f"Job '{job_id}' cannot be cancelled")
    job = await svc.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return job
