"""FastAPI application factory for Clinical Guideline Assistant.

Extends LORNEWS FastAPI app with clinical-specific routes.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from clinical_assistant.config import Settings
from clinical_assistant.routers.guidelines import router as guidelines_router

_LOG = structlog.get_logger("clinical_assistant")

settings = Settings.from_env()


@asynccontextmanager
async def lifespan(app: FastAPI):
    _LOG.info("clinical_assistant_startup")
    yield
    _LOG.info("clinical_assistant_shutdown")


def create_app() -> FastAPI:
    """Create FastAPI application with clinical endpoints.

    Can be mounted under LORNEWS's app or run standalone.
    """
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description="AI-powered evidence-based medicine platform. "
        "Search clinical guidelines, get citation-backed recommendations.",
        lifespan=lifespan,
        docs_url=f"{settings.api_prefix}/docs",
        openapi_url=f"{settings.api_prefix}/openapi.json",
        contact={"name": "Clinical Guideline Assistant Team"},
        license_info={"name": "MIT"},
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    app.include_router(guidelines_router, prefix=settings.api_prefix)

    @app.get(f"{settings.api_prefix}/health", tags=["health"])
    async def health():
        return {"status": "ok", "version": settings.version}

    return app


app = create_app()
