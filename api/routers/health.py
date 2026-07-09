from __future__ import annotations

import time

from fastapi import APIRouter

from api.dependencies import health_check_deps, is_ready
from api.schemas.health import HealthResponse, LivenessResponse, ReadinessResponse

router = ARouter = APIRouter(tags=["health"])

_start_time = time.monotonic()


@router.get(
    "/health",
    response_model=HealthResponse,
    operation_id="get_health",
    summary="Overall system health",
    description="Returns overall system status including uptime and version.",
)
async def get_health():
    return HealthResponse(
        uptime_seconds=round(time.monotonic() - _start_time, 2),
    )


@router.get(
    "/liveness",
    response_model=LivenessResponse,
    operation_id="get_liveness",
    summary="Liveness probe",
    description="Returns alive status for container orchestrators.",
)
async def get_liveness():
    return LivenessResponse()


@router.get(
    "/readiness",
    response_model=ReadinessResponse,
    operation_id="get_readiness",
    summary="Readiness probe",
    description="Returns whether all dependencies are initialized and ready.",
)
async def get_readiness():
    deps = await health_check_deps()
    ready = all(deps.values()) and is_ready()
    return ReadinessResponse(
        status="ok" if ready else "degraded",
        agent_ready=deps["agent"],
        knowledge_base_ready=deps["knowledge_base"],
        cache_ready=deps["cache"],
    )
