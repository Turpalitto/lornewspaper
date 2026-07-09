from __future__ import annotations

import time
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from api.config import APISettings
from api.dependencies import init_agent, set_ready, shutdown_agent
from api.env_validator import validate_env
from api.exception_handlers import (
    http_exception_handler,
    research_agent_exception_handler,
    validation_exception_handler,
)
from api.jobs.handlers import handle_ingest
from api.jobs.service import JobService, get_job_service
from api.middleware import RequestIDMiddleware, StructLogAndErrorMiddleware
from api.routers.ask import router as ask_router
from api.routers.documents import router as documents_router
from api.routers.health import router as health_router
from api.routers.ingest import router as ingest_router
from api.routers.metrics import metrics, record_request
from api.routers.search import router as search_router
from api.routers.jobs import router as jobs_router
from api.routers.telegram import router as telegram_router
from api.routers.pipeline import router as pipeline_router
from api.security import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    TrustedHostMiddleware,
)

_LOG = structlog.get_logger("api")

settings = APISettings.from_env()


@asynccontextmanager
async def lifespan(app: FastAPI):
    issues = validate_env()
    for issue in issues:
        if issue.startswith("WARNING"):
            _LOG.warning("env_issue", detail=issue)
        else:
            _LOG.error("env_issue", detail=issue)

    _LOG.info("api_startup")
    try:
        await init_agent()
        set_ready(True)
        _LOG.info("api_startup_complete")
    except Exception as exc:
        _LOG.error("api_startup_failed", error=str(exc))
        set_ready(False)

    svc = get_job_service()
    svc.register_handler("ingest", handle_ingest)
    await svc.start()
    _LOG.info("job_service_started")

    yield

    _LOG.info("api_shutdown")
    await svc.stop()
    await shutdown_agent()
    _LOG.info("api_shutdown_complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description="Production-grade REST API for the Research Agent platform. "
        "Supports academic literature search, document ingestion, "
        "retrieval-augmented generation (RAG) question answering, "
        "summarization, and similarity analysis.",
        lifespan=lifespan,
        docs_url=f"{settings.api_prefix}/docs",
        redoc_url=f"{settings.api_prefix}/redoc",
        openapi_url=f"{settings.api_prefix}/openapi.json",
        contact={
            "name": "Research Agent Team",
            "url": "https://github.com/anomalyco/lornewspaper",
        },
        license_info={
            "name": "MIT",
        },
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
        allow_credentials=True,
    )

    app.add_middleware(SecurityHeadersMiddleware)

    if "*" not in settings.trusted_hosts:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.trusted_hosts,
        )

    if settings.enable_rate_limit:
        app.add_middleware(
            RateLimitMiddleware,
            max_requests=settings.rate_limit_per_minute,
        )

    if settings.enable_compression:
        app.add_middleware(GZipMiddleware, minimum_size=1000)

    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(StructLogAndErrorMiddleware)

    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    from research_agent.exceptions import ResearchAgentError

    app.add_exception_handler(ResearchAgentError, research_agent_exception_handler)

    app.include_router(health_router, prefix=settings.api_prefix)

    if settings.enable_metrics:
        app.add_route("/metrics", metrics)

    app.include_router(search_router, prefix=settings.api_prefix)
    app.include_router(ingest_router, prefix=settings.api_prefix)
    app.include_router(ask_router, prefix=settings.api_prefix)
    app.include_router(documents_router, prefix=settings.api_prefix)
    app.include_router(jobs_router, prefix=settings.api_prefix)
    app.include_router(telegram_router, prefix=settings.api_prefix)
    app.include_router(pipeline_router, prefix=settings.api_prefix)

    return app


app = create_app()
