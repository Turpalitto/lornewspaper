# v1.0 Known Limitations

## 1. Single ResearchAgent Instance

**Issue:** The `ResearchAgent` uses a singleton pattern with `AGENT_BUSY` mutex. Only one `ask`/`summarize`/`similar` operation can run at a time.

**Impact:** Under concurrent user load, parallel RAG queries return 409 Conflict.

**Recommended fix:** Replace with per-request agent or connection pool (q2).

## 2. In-Memory Rate Limiter

**Issue:** `InMemoryRateLimiter` lives per-worker-process. Behind a load balancer with multiple uvicorn workers, each worker has its own counter — effective rate limit is `N * 60/min`.

**Impact:** Rate limiting is less effective with multiple workers.

**Recommended fix:** Replace with Redis-based rate limiter using `arq` or `redis-py` (q1).

## 3. No Frontend Healthcheck

**Issue:** The frontend Docker HEALTHCHECK proxies to the backend's `/api/v1/health`. If the backend is down, the frontend container is also killed.

**Impact:** Unnecessary container restart during backend deployments.

**Recommended fix:** Add `GET /api/health` route to the Next.js app that returns 200 independently (30m effort).

## 4. Minimal PDF Test Fixtures

**Issue:** The e2e test PDF is a minimal 150KB document with one page. Production PDFs are 200KB-2MB with complex layouts, figures, and tables.

**Impact:** The text extraction, table parsing, and figure detection pipelines are not exercised against real-world PDFs.

**Recommended fix:** Add a corpus of real (open-access) PDFs to the test fixtures.

## 5. No Authentication

**Issue:** All API endpoints are public. There is no user authentication, authorization, or API key validation.

**Impact:** Anyone who can reach the API can search, ingest, and query documents.

**Recommended fix:** Add API key or OAuth2 authentication. The `AuthProvider` in the frontend is already scaffolded (no-op by default) — just needs the backend middleware.

## 6. No Background Task Queue for Production

**Issue:** The local in-memory job queue (TASK 2) doesn't survive process restarts. Jobs are lost on crash.

**Impact:** Long-running ingest jobs are at risk of data loss.

**Recommended fix:** Swap the `LocalJobBackend` for `arq` (Redis-based). The ABC interface is already designed for this — implement `arq.ArqJobBackend(JobBackend)`.

## 7. No Staging Environment

**Issue:** There is no documented staging or preview environment. All changes go directly to production.

**Impact:** High risk of regressions reaching users.

**Recommended fix:** Add a staging deployment to the CD workflow (e.g., Railway staging service).

## 8. Python Environment Not Frozen

**Issue:** `requirements.txt` uses loose version pins (`>=`). No lockfile.

**Impact:** Non-deterministic builds — different dependency versions may produce different behavior.

**Recommended fix:** Add `pip freeze > requirements.lock` or migrate to Poetry/Poetry lockfile.

## 9. Frontend Type Drift

**Issue:** `web/openapi.json` is a static snapshot. If the backend changes, types can drift until `npm run api:sync` is run.

**Impact:** Frontend compilation errors or runtime API mismatches.

**Recommended fix:** Add a CI step that validates `web/openapi.json` matches the backend schema.

## 10. No Database Migrations

**Issue:** SQLite schema is created via `CREATE TABLE IF NOT EXISTS` in code. There's no migration system for schema changes.

**Impact:** Schema changes require manual intervention.

**Recommended fix:** Add Alembic for SQLite/PostgreSQL migration management.
