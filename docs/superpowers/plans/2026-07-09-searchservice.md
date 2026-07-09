# SearchService — Detailed Implementation Plan

**Goal:** Extensible async `SearchService` over PubMed, Europe PMC, OpenAlex returning unified, deduplicated `Article` records.

**Stack:** Python 3.12, asyncio + httpx, tenacity, pydantic v2, structlog, pytest, pytest-asyncio, respx.

**Global Constraints**
- Async only. Retry transient errors only (network, timeout, 429, 5xx); honor `Retry-After`.
- Per-provider configurable rate limit (token bucket) + timeout.
- Structured logging (structlog): provider, endpoint, query, elapsed, retries, status_code, result_count.
- Validate every provider response with Pydantic before mapping.
- `SearchService` depends only on `BaseProvider` ABC (DIP). New provider = new class + registry entry.
- Tests use respx/`MockTransport` — no real network.

---

## Milestone M1 — Project skeleton & cross-cutting infra
**Objective:** Scaffold package and build shared infrastructure (config, logging, http client, rate limiter, retry).
**Files:** `pyproject.toml`, `requirements.txt`, `search_service/__init__.py`, `config.py`, `logging_config.py`, `http_client.py`, `rate_limit.py`, `retry.py`.
**Dependencies:** none.
**Acceptance:** imports succeed; `get_client()` returns pooled client; `AsyncRateLimiter` caps call rate; `async_retry` retries on 5xx/429/timeout and honors `Retry-After`. Unit tests for limiter + retry pass.
**Complexity:** Medium.
**Risks:** token-bucket timing flakiness in CI → use generous windows; `Retry-After` parse edge cases.

## Milestone M2 — Model, BaseProvider, Registry
**Objective:** Define `Article` model, `BaseProvider` ABC with `_request` helper (rate-limit→retry→http→log→validate), and provider registry.
**Files:** `models.py`, `base.py`, `providers/__init__.py`.
**Dependencies:** M1.
**Acceptance:** `Article` serializes all fields; `BaseProvider._request` raises on non-transient 4xx, retries transient, logs structured line, validates via pydantic. Registry resolves enabled providers.
**Complexity:** Medium.
**Risks:** ABC `_request` must be reusable by all providers without leakage.

## Milestone M3 — PubMedProvider
**Objective:** Implement PubMed via E-utilities (esearch+efetch/esummary) with full methods + capabilities + healthcheck.
**Files:** `providers/pubmed.py`, `tests/test_pubmed.py`.
**Dependencies:** M2.
**Acceptance:** search/search_by_date/search_by_pmid/get_metadata/get_abstract/healthcheck work with mocked eutils; mapping to `Article` correct; validation tested with bad payload.
**Complexity:** High (two-step eutils flow).
**Risks:** XML/JSON parsing of eutils; ID list then fetch correlation.

## Milestone M4 — EuropePMCProvider
**Objective:** Implement Europe PMC REST search + single-result endpoints.
**Files:** `providers/europepmc.py`, `tests/test_europepmc.py`.
**Dependencies:** M2.
**Acceptance:** all methods + capabilities + healthcheck with mocked REST; `pmcid`, `pdf_url` mapped.
**Complexity:** Medium.
**Risks:** field naming differences (pmcid vs PMCID), pagination.

## Milestone M5 — OpenAlexProvider
**Objective:** Implement OpenAlex REST with filter syntax, mailto param for politeness.
**Files:** `providers/openalex.py`, `tests/test_openalex.py`.
**Dependencies:** M2.
**Acceptance:** all methods + capabilities + healthcheck with mocked API; doi/pmid mapping.
**Complexity:** Medium.
**Risks:** OpenAlex has no PMID native — derive via `ids.pmid`; date filter syntax.

## Milestone M6 — SearchService + dedupe/merge
**Objective:** `dedupe.py` (dedup by doi/pmid/pmcid/title similarity + merge with provenance) and `service.py` (fan-out with semaphore, partial-failure isolation, concurrency limit).
**Files:** `dedupe.py`, `service.py`, `tests/test_dedupe.py`, `tests/test_search.py`, `tests/test_resilience.py`.
**Dependencies:** M3,M4,M5.
**Acceptance:** search_all/search_by_provider/search_by_date/search_by_pmid work; partial failure isolated; dedupe merges fields + provenance; concurrency limit respected.
**Complexity:** High.
**Risks:** title-similarity false positives; merge field precedence; semaphore starvation.

## Milestone M7 — Integration, perf, docs
**Objective:** End-to-end integration test (mocked all providers), perf/concurrency test, README + final commit.
**Files:** `tests/test_integration.py`, `README.md`.
**Dependencies:** M6.
**Acceptance:** integration test passes; perf test asserts bounded concurrency; README documents usage + extension guide.
**Complexity:** Low-Medium.
**Risks:** none major.

---

## Quality gates (every milestone)
1. `pytest` all pass.
2. `ruff` lint clean (or `flake8`).
3. `mypy` type-check clean.
4. Commit atomic with meaningful message.
5. Update docs continuously.
