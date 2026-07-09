# API — Architecture Anchor

## Purpose

Production-grade REST API layer exposing ResearchAgent through FastAPI.

## Files

```
api/
├── __init__.py
├── app.py                  — FastAPI app factory, lifespan, middleware, router registration
├── config.py               — APISettings dataclass (CORS, debug, log level)
├── dependencies.py         — ResearchAgent DI, init/shutdown, health check
├── exception_handlers.py   — Unified ErrorResponse: validation, HTTP, agent, general
├── middleware.py            — Raw ASGI middleware: RequestID, StructLog + error catch
├── schemas/
│   ├── __init__.py
│   ├── common.py           — ErrorResponse, PaginationRequest, PaginatedResponse[T]
│   ├── health.py           — HealthResponse, ReadinessResponse, LivenessResponse
│   ├── search.py           — SearchRequest, ArticleResponse, SearchResponse
│   ├── ingest.py           — IngestRequest, DownloadRequest, IngestResponse, DownloadResponse
│   ├── ask.py              — AskRequest, AskResponse, AnswerResponse, ChunkInfo
│   └── documents.py        — DocumentRecord, ChunkRecord, SummaryResponse, SimilarResponse
├── routers/
│   ├── __init__.py
│   ├── health.py           — GET /health, /liveness, /readiness
│   ├── search.py           — POST /search
│   ├── ingest.py           — POST /ingest, POST /ingest/download
│   ├── ask.py              — POST /ask (reserved: /ask/stream)
│   └── documents.py        — GET /documents, /documents/{id}, /{id}/chunks, /{id}/summary, /{id}/similar
└── auth/
    └── __init__.py          — Placeholder for auth middleware
```

## Endpoints

All under `/api/v1/`.

| Method | Path | Operation ID | Router |
|--------|------|-------------|--------|
| GET | /health | get_health | health |
| GET | /liveness | get_liveness | health |
| GET | /readiness | get_readiness | health |
| POST | /search | search_articles | search |
| POST | /ingest | ingest_articles | ingest |
| POST | /ingest/download | search_and_download | ingest |
| POST | /ask | ask_question | ask |
| GET | /documents | list_documents | documents |
| GET | /documents/{id} | get_document | documents |
| GET | /documents/{id}/chunks | get_document_chunks | documents |
| GET | /documents/{id}/summary | get_document_summary | documents |
| GET | /documents/{id}/similar | get_similar_documents | documents |

## Error Model

```json
{
  "code": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "details": {"body -> query": "Field required"},
  "request_id": "uuid",
  "timestamp": "2026-07-09T12:00:00Z"
}
```

Error codes: `VALIDATION_ERROR`, `AGENT_BUSY` (409), `DOCUMENT_NOT_FOUND` (404), `UNKNOWN_PROVIDER` (400), `INTERNAL_ERROR` (500), `HTTP_*` (mapped from Starlette).

## Middleware Stack

```
RequestIDMiddleware (raw ASGI)
  → StructLogAndErrorMiddleware (raw ASGI)
    → CORSMiddleware (Starlette)
      → ExceptionMiddleware (Starlette — HTTP + ResearchAgent errors)
        → AsyncExitStackMiddleware (FastAPI)
          → Router
```

## DI

- `ResearchAgent` created during lifespan startup
- 1 agent per app process, shared via `dependencies.get_agent()`
- Tests override via `app.dependency_overrides[get_agent]`
- Env config: `LLM_API_KEY`, `LLM_PROVIDER`, `LLM_MODEL`, `LLM_BASE_URL`

## Quality

- ruff: clean
- mypy: clean (api/ only)
- Tests: 33 passed (all API integration)
- Full suite: 247 passed, 7 skipped
