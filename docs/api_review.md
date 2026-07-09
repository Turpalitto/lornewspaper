# API — Architecture Review

**Date:** 2026-07-09
**Module:** `api/`
**Lines of code:** ~450 across 18 files
**Tests:** 33 passed

---

## Architecture

The API is a thin FastAPI layer over the existing ResearchAgent orchestrator. It adds zero business logic — all orchestration lives in `research_agent/`. The API translates HTTP ↔ Python types, manages request lifecycle, and provides OpenAPI documentation.

### Dependency Graph

```
FastAPI app (app.py)
  ├── Lifespan → init_agent() → ResearchAgent + KB + cache
  ├── Middleware → RequestID → StructLog → CORS
  ├── Exception handlers → ErrorResponse (unified format)
  └── Routers
       ├── health → (no agent dependency)
       ├── search → ResearchAgent.search()
       ├── ingest → ResearchAgent.ingest() / search_and_download()
       ├── ask → ResearchAgent.ask()
       └── documents → ResearchAgent.search_documents() / _load_doc() / summarize() / similar()
```

### Request Lifecycle

```
1. Request enters ASGI
2. RequestIDMiddleware: generates/extracts X-Request-ID, injects into scope state + response headers
3. StructLogAndErrorMiddleware: logs start/end, catches unhandled exceptions → ErrorResponse 500
4. CORSMiddleware: handles CORS preflight + headers
5. ExceptionMiddleware: routes known exceptions to handlers (ResearchAgentError → typed status codes)
6. Router → Route → Handler:
   a. Pydantic v2 validation of path/query/body params
   b. Calls ResearchAgent method via Depends(get_agent)
   c. Maps AgentResult to response schema
   d. Returns Pydantic model → FastAPI serializes to JSON
7. Response walks back through middleware stack with headers
```

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| API versioning | `/api/v1/` prefix | Backward compat, path for v2 |
| Routing | Flat routers, not nested | 10 endpoints, no deep nesting needed |
| ASGI middleware (not BaseHTTPMiddleware) | Raw ASGI | Starlette 1.3.1 wraps exceptions in TaskGroup → ExceptionGroup; raw ASGI avoids this |
| Error handling | Middleware catches leaks → ErrorResponse; ExceptionMiddleware handles typed exceptions | Double-handling in `wrap_app_handling_exceptions` required removing blanket `Exception` handler from FastAPI |
| Schema structure | One file per domain | The project has grown; single file would be unwieldy |
| Pagination | Cursor-based | Avoids offset perf issues; opaque cursor = chunk index for now |
| Streaming | `/ask/stream` reserved, not implemented | Architecture doesn't prevent it — future: replace `return AnswerResponse` with `StreamingResponse` |
| Auth | Placeholder `api/auth/` | YAGNI — no auth requirements specified |

---

## Findings

### Critical (0)

None.

### Warnings (2)

| # | Finding | Location | Recommendation |
|---|---------|----------|----------------|
| W1 | No rate limiting | `api/middleware.py` | Add `slowapi` or nginx-level rate limiting before production. |
| W2 | Chunk cursor pagination is O(n) scan | `api/routers/documents.py:111-116` | For large doc collections, add offset-based or DB-native cursor. Current impl scans chunk list to find cursor position. Acceptable at current scale. |

### Notes (3)

| # | Note | Location | Rationale |
|---|------|----------|-----------|
| N1 | `Depends()` flagged by ruff B008 | All routers | Known FastAPI/ruff clash. Suppressed via `pyproject.toml` per-file-ignores. |
| N2 | `add_exception_handler` type mismatch in mypy | `api/app.py` | Starlette's `add_exception_handler` signature is generic; our handlers are covariant. Suppressed with `# type: ignore`. |
| N3 | No request size limits | `api/app.py` | FastAPI defaults apply. Consider `max_request_size` middleware for production. |

---

## OpenAPI

Generated automatically from Pydantic schemas + route decorators. Available at:
- Swagger UI: `/api/v1/docs`
- ReDoc: `/api/v1/redoc`
- OpenAPI JSON: `/api/v1/openapi.json`

Every endpoint has:
- `operation_id` — unique identifier for codegen
- `summary` — short description
- `description` — detailed explanation
- `tags` — organized by domain
- `response_model` — typed Pydantic response
- Error responses documented where non-obvious (409, 404)

---

## Production Readiness

### Security

| Check | Status | Notes |
|-------|--------|-------|
| CORS | Configured | Wildcard by default (env-configurable) |
| Request ID | Implemented | Set from `X-Request-ID` header or generated |
| Auth | Not implemented | Placeholder directory only |
| Input validation | Pydantic v2 | Type coercion + constraints |
| Error disclosure | Safe | Unified ErrorResponse, no stack traces in responses |
| Rate limiting | Missing | Needs nginx/slowapi |

### Observability

| Check | Status | Notes |
|-------|--------|-------|
| Structured logging | Implemented | structlog, request-scoped |
| Request/response logging | End-to-end | Start/end with status, method, path |
| Error logging | All paths | Exception handlers + middleware |
| Metrics | Missing | Add Prometheus counters |
| Health probes | 3 endpoints | health, liveness, readiness |
| Trace IDs | X-Request-ID | Per-request, propagated to logs + response |

### Resilience

| Check | Status | Notes |
|-------|--------|-------|
| Startup health check | Implemented | Agent init wraps in try/except, sets ready=false on failure |
| Graceful shutdown | Implemented | Agent.close() releases KB resources |
| Error recovery | Per-endpoint | Agent returns AgentResult with status=FAILED, never crashes |
| Circuit breaker | Missing | ResearchAgent has no circuit breaker for LLM calls |

### Testing

| Area | Status | Coverage |
|------|--------|----------|
| Health endpoints | 3 tests | health, liveness, readiness |
| Search | 6 tests | success, empty query, validation, busy→409, error→500 |
| Ingest | 3 tests | success, download, validation |
| Ask | 4 tests | answer, empty, provider override, validation |
| Documents | 10 tests | list, empty, pagination, get, not-found, chunks, cursor, summary, similar |
| Common | 7 tests | request ID, CORS, 404 format, OpenAPI spec, error format |
| **Total** | **33 tests** | All passing |

---

## Summary

| Metric | Value |
|--------|-------|
| Files | 18 |
| Endpoints | 12 |
| Tests | 33 passed |
| ruff | Clean |
| mypy | Clean (module-level) |
| External deps | `fastapi`, `uvicorn`, `starlette`, `python-multipart` |
| Blocking issues | 0 |
