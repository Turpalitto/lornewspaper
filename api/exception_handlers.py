from __future__ import annotations

import structlog
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.schemas.common import ErrorResponse

_LOG = structlog.get_logger("api")


def _error_response(
    request: Request,
    code: str,
    message: str,
    status: int,
    details: dict | None = None,
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "")
    resp = ErrorResponse(
        code=code,
        message=message,
        details=details or {},
        request_id=request_id,
    )
    return JSONResponse(content=resp.model_dump(mode="json"), status_code=status)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    _LOG.warning("validation_error", errors=exc.errors())
    details = {}
    for err in exc.errors():
        loc = " -> ".join(str(part) for part in err.get("loc", []))
        details[loc] = err.get("msg", "validation error")
    return _error_response(
        request=request,
        code="VALIDATION_ERROR",
        message="Request validation failed",
        status=422,
        details=details,
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return _error_response(
        request=request,
        code=f"HTTP_{exc.status_code}",
        message=str(exc.detail),
        status=exc.status_code,
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    _LOG.exception("unhandled_error", error=str(exc))
    return _error_response(
        request=request,
        code="INTERNAL_ERROR",
        message="An internal error occurred",
        status=500,
    )


async def research_agent_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    from research_agent.exceptions import (
        AgentBusyError,
        DocumentNotFoundError,
        UnknownProviderError,
    )

    if isinstance(exc, AgentBusyError):
        return _error_response(
            request=request,
            code="AGENT_BUSY",
            message=str(exc),
            status=409,
        )
    if isinstance(exc, DocumentNotFoundError):
        return _error_response(
            request=request,
            code="DOCUMENT_NOT_FOUND",
            message=str(exc),
            status=404,
        )
    if isinstance(exc, UnknownProviderError):
        return _error_response(
            request=request,
            code="UNKNOWN_PROVIDER",
            message=str(exc),
            status=400,
        )

    return _error_response(
        request=request,
        code="AGENT_ERROR",
        message=str(exc),
        status=500,
    )
