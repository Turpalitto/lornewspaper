# SearchService — Design Spec

**Date:** 2026-07-09
**Status:** Approved (with additions)
**Stack:** Python 3.11+, asyncio + httpx, tenacity, pydantic v2, structlog

## 1. Goal

A backend module that searches multiple academic literature sources (PubMed,
Europe PMC, OpenAlex) through a unified interface and returns normalized,
deduplicated `Article` records with provenance preserved.

## 2. Principles (SOLID + DIP)

- **SRP:** Each provider owns one source. Cross-cutting concerns (retry, rate
  limit, logging, HTTP) live in separate modules.
- **OCP:** New source = new provider class + register in config. `SearchService`
  untouched.
- **LSP:** All providers are interchangeable via `BaseProvider`.
- **ISP:** `BaseProvider` exposes only what every source supports; capabilities
  flag optional features.
- **DIP:** `SearchService` depends on `BaseProvider` ABC, never concrete classes.

## 3. Package Layout

```
search_service/
├── __init__.py
├── models.py          # Article + provider capability enums
├── config.py          # Settings, ProviderConfig dataclasses
├── base.py            # BaseProvider ABC
├── http_client.py     # shared httpx.AsyncClient (pool, UA, timeout)
├── rate_limit.py      # AsyncRateLimiter (token bucket, Retry-After aware)
├── retry.py           # async_retry (tenacity) for transient errors
├── logging_config.py  # structlog setup + contextvars
├── dedupe.py          # dedup + merge logic
├── service.py         # SearchService orchestrator
├── providers/
│   ├── __init__.py    # registry
│   ├── pubmed.py      # PubMedProvider
│   ├── europepmc.py   # EuropePMCProvider
│   └── openalex.py    # OpenAlexProvider
└── tests/
    ├── conftest.py
    ├── test_search.py
    ├── test_providers.py
    ├── test_dedupe.py
    └── test_resilience.py
```

## 4. Unified Model — `Article` (pydantic v2)

Required:
- `title`, `authors: list[str]`, `journal: str | None`, `year: int | None`,
  `doi: str | None`, `pmid: str | None`, `abstract: str | None`,
  `keywords: list[str]`, `mesh_terms: list[str]`, `url: str | None`,
  `pdf_url: str | None`, `source: str` (provider name).

Optional (added):
- `id: str | None` — stable hash of doi/pmid/title
- `pmcid: str | None`
- `language: str | None`
- `publication_type: list[str]`
- `publisher: str | None`
- `volume: str | None`
- `issue: str | None`
- `pages: str | None`
- `license: str | None`
- `retrieved_at: datetime`
- `raw_response: dict | None` (optional, off by default)

Provenance: `source` records which provider produced each record. On merge,
`provenance: list[str]` accumulates contributing providers.

## 5. Provider Interface — `BaseProvider` (ABC)

Every provider MUST implement:

```python
class BaseProvider(ABC):
    name: str
    capabilities: ProviderCapabilities   # which ops supported

    @abstractmethod
    async def search(self, query: str, limit: int = 20) -> list[Article]: ...
    @abstractmethod
    async def search_by_date(self, query: str, from_year: int | None,
                             to_year: int | None, limit: int = 20) -> list[Article]: ...
    @abstractmethod
    async def search_by_pmid(self, pmid: str) -> Article | None: ...
    @abstractmethod
    async def get_metadata(self, identifier: str) -> Article | None: ...
    @abstractmethod
    async def get_abstract(self, identifier: str) -> str | None: ...
    @abstractmethod
    async def healthcheck(self) -> bool: ...
```

- **Capabilities:** dataclass `ProviderCapabilities` flagging
  `supports_search`, `supports_date`, `supports_pmid`, `supports_metadata`,
  `supports_abstract`, `supports_healthcheck`.
- **Configurable rate limits** per provider (requests/sec, burst).
- **Configurable timeout** per provider.

Cross-cutting applied via composition, not inheritance sprawl:
each concrete provider calls `self._request(...)` which runs through
`rate_limiter` → `async_retry` → `http_client` and emits structured logs.

## 6. HTTP Layer — `http_client.py`

- Single shared `httpx.AsyncClient` with `limits` (connection pool, keep-alive),
  default `timeout`, and `headers={"User-Agent": ...}`.
- Client built from `Settings`, reused across all providers (one pool).
- Context manager `async with` for lifecycle; `SearchService` owns it.

## 7. Rate Limiting — `rate_limit.py`

- `AsyncRateLimiter`: async token-bucket per provider.
- Reads `Retry-After` header on 429 and pauses the bucket accordingly.
- Config: `rate` (req/s), `burst` (max tokens).

## 8. Retry — `retry.py`

- `async_retry` decorator built on `tenacity.AsyncRetrying`.
- Retries ONLY transient errors:
  - `httpx.TransportError` / `httpx.TimeoutException` (network, timeout)
  - `httpx.ResponseStatusError` with status 429 or 5xx
- Uses exponential backoff + jitter.
- Honors `Retry-After` (parses header, sets wait).
- Does NOT retry 4xx except 429.
- Retry count surfaced in logs via contextvar.

## 9. Logging — `logging_config.py`

- `structlog` with structured processors (timestamp, level, JSON or console).
- Binds context per request: `provider`, `endpoint`, `query`, `elapsed`,
  `retries`, `status_code`, `result_count`.
- One log line per provider call on completion.

## 10. Deduplication & Merge — `dedupe.py`

Priority order for identity match between two records:
1. `doi` (normalized, lowercased)
2. `pmid`
3. `pmcid`
4. Normalized title similarity (fallback) — token-set ratio > threshold.

Merge rule:
- Pick best non-null value per field across sources.
- Union `keywords`, `mesh_terms`, `authors`, `publication_type`.
- Append provider to `provenance`.
- Keep earliest `retrieved_at` or latest—documented as latest wins for fields.

## 11. SearchService — `service.py`

Orchestrator, depends only on `BaseProvider`.

Methods:
- `search_all(query, limit, from_year=None, to_year=None)` — fan out to all
  capable providers, aggregate + dedupe + merge.
- `search_by_provider(query, provider_name, ...)` — single provider.
- `search_by_date(query, from_year, to_year, limit)` — date-scoped fan-out.
- `search_by_pmid(pmid)` — query all providers for a PMID, merge.

Concurrency:
- `concurrency_limit` (asyncio.Semaphore) bounds parallel provider calls.

Resilience:
- Partial failures isolated: a provider exception is caught, logged, and the
  remaining providers still return. Failed provider contributes empty result.

## 12. Config — `config.py`

- `Settings`: http timeout, user_agent, concurrency_limit, log level.
- `ProviderConfig`: name, enabled, base_url, rate, burst, timeout.
- Providers registered in a `REGISTRY` dict; `SearchService` iterates enabled.

## 13. Adding a new provider (OCP proof)

1. Create `providers/<name>.py` with a class implementing `BaseProvider`.
2. Register it in `providers/__init__.py` `REGISTRY`.
3. Add its `ProviderConfig`.

No change to `SearchService`, `dedupe`, `http_client`, or `service.py`.

## 14. Testing — pytest (pytest-asyncio)

- `test_search.py`: successful `search_all` returns normalized `Article`s.
- `test_resilience.py`: timeout triggers retry; retry succeeds after N fails
  (mock transport); rate limiting caps calls; one provider failing does not
  fail whole `search_all`.
- `test_dedupe.py`: dedupe by doi/pmid/pmcid/title; metadata merge unions
  fields and preserves provenance.
- `test_providers.py`: each provider `healthcheck`; response validation with
  pydantic (bad payload raises); mapping correctness with mocked JSON.

Use `httpx.MockTransport` / `respx` for HTTP mocking — no real network.

## 15. Dependencies

`httpx`, `tenacity`, `pydantic>=2`, `structlog`, `pytest`, `pytest-asyncio`,
`respx`.
