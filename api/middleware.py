from __future__ import annotations

import time
import uuid

import structlog
from starlette.datastructures import MutableHeaders
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from api.routers.metrics import record_request
from api.schemas.common import ErrorResponse

_LOG = structlog.get_logger("api")


class RequestIDMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = ""
        for key, value in scope.get("headers", []):
            if key.lower() == b"x-request-id":
                request_id = value.decode()
                break
        if not request_id:
            request_id = str(uuid.uuid4())

        async def send_with_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(raw=message.get("headers", []))
                headers["X-Request-ID"] = request_id
                message["headers"] = headers.raw
            await send(message)

        scope["state"] = {**scope.get("state", {}), "request_id": request_id}
        await self.app(scope, receive, send_with_id)


class StructLogAndErrorMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        state = scope.get("state", {})
        request_id = state.get("request_id", "")
        _LOG.info(
            "request_start",
            method=scope["method"],
            path=scope["path"],
            query_string=scope.get("query_string", b"").decode(),
            request_id=request_id,
        )

        status_code = [200]
        response_sent = [False]
        start_time = time.monotonic()

        async def send_with_log(message: Message) -> None:
            if message["type"] == "http.response.start":
                status_code[0] = message["status"]
                response_sent[0] = True
            await send(message)

        try:
            await self.app(scope, receive, send_with_log)
        except BaseExceptionGroup:
            raise
        except Exception as exc:
            if not response_sent[0]:
                resp = ErrorResponse(
                    code="INTERNAL_ERROR",
                    message="An internal error occurred",
                    details={},
                    request_id=request_id,
                )
                json_resp = JSONResponse(
                    content=resp.model_dump(mode="json"),
                    status_code=500,
                )
                await json_resp(scope, receive, send)
                status_code[0] = 500
            _LOG.exception("request_error", request_id=request_id, error=str(exc))
        finally:
            duration = time.monotonic() - start_time
            record_request(duration)
            _LOG.info(
                "request_end",
                method=scope["method"],
                path=scope["path"],
                status_code=status_code[0],
                duration_seconds=round(duration, 4),
                request_id=request_id,
            )
