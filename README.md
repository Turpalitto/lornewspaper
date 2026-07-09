# SearchService

Extensible async literature search over multiple academic sources through a
single unified interface.

Supported providers:

- **PubMed** — NCBI E-utilities (esearch + efetch)
- **Europe PMC** — REST API
- **OpenAlex** — REST API

## Features

- Unified `Article` model for every source.
- One provider per source, behind a `BaseProvider` ABC (SOLID / DIP).
- Transient-only retry (network, timeout, HTTP 429, 5xx) with `Retry-After`.
- Per-provider token-bucket rate limiting.
- Structured logging (structlog): provider, endpoint, query, elapsed, retries,
  status_code, result_count.
- Shared `httpx.AsyncClient` (connection pooling, keep-alive, User-Agent).
- Concurrent fan-out with a configurable semaphore and **partial-failure
  isolation** — one broken source never sinks the whole search.
- Deduplication (DOI → PMID → PMCID → title similarity) with metadata merge
  and provenance tracking.

## Install

```bash
pip install -r requirements.txt
# dev tooling (lint/type/tests):
pip install -e ".[test,dev]"
```

## Usage

```python
import asyncio
from search_service import SearchService


async def main():
    svc = SearchService()  # reads default settings (3 providers enabled)
    try:
        # Search everywhere, deduplicated + merged:
        articles = await svc.search_all("CRISPR cancer therapy", limit=20)
        for a in articles:
            print(a.title, a.year, a.doi, a.provenance)

        # Single provider:
        pm = await svc.search_by_provider("p53", "pubmed", limit=5)

        # Date scoped:
        recent = await svc.search_by_date("long covid", 2021, 2023, limit=10)

        # By PubMed ID (merged across sources):
        by_pmid = await svc.search_by_pmid("32972414")
    finally:
        await svc.aclose()


asyncio.run(main())
```

`SearchService` is an async context manager alternative:

```python
async with SearchService() as svc:
    ...
```

## Configuration

`search_service/config.py` exposes `Settings` and `ProviderConfig`. Override
defaults (timeouts, rate limits, concurrency, log level) and pass to
`SearchService(settings=...)`.

## Structured logging

```python
from search_service.logging_config import configure_logging

configure_logging("INFO", json_logs=True)
```

## Adding a new provider

1. Create `search_service/providers/<name>.py` with a class subclassing
   `BaseProvider` and implementing `search`, `search_by_date`,
   `search_by_pmid`, `get_metadata`, `get_abstract`, `healthcheck`, plus a
   `capabilities` instance of `ProviderCapabilities`.
2. Register it in `PROVIDER_CLASSES` in `search_service/providers/__init__.py`.
3. Add its `ProviderConfig` to `default_settings()` in
   `search_service/config.py`.

`SearchService` is never modified — it depends only on the `BaseProvider` ABC.

## Testing

```bash
pytest
```

All tests use `respx` / `httpx.MockTransport` — no real network access.
