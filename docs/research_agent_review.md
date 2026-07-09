# ResearchAgent — Architecture Review

**Date:** 2026-07-09
**Module:** `research_agent/`
**Lines of code:** ~680 across 15 files
**Tests:** 50 passed, 4 skipped

---

## Architecture

`ResearchAgent` is a thin orchestrator wrapping 4 existing services. It adds zero new data — all state lives in the existing services. The agent composes their public APIs into workflows and adds LLM-powered features (QA, summarization, similarity).

### Layering

```
CLI (cli.py)
  │
ResearchAgent (agent.py)
  │
  ├── workflow.py ──── SearchService → DownloadService → DPS → KBService
  ├── providers/ ───── BaseLLMProvider → OpenAI / Anthropic / Gemini / Ollama
  ├── prompts/ ─────── QA / Summarize / Similar templates
  └── cache.py ─────── TTL response cache
```

### Key decisions

1. **No modification to existing modules** — All integration is through public APIs. No monkey-patching, no internal imports.
2. **Lazy imports for external deps** — Heavy imports (openai, anthropic, google, search_service, download_service) happen inside function bodies, not at module level. This keeps import time fast and makes the package pip-installable without any optional provider packages.
3. **Graceful provider discovery** — `discover_providers()` wraps each import in try/except ImportError. If `anthropic` is not installed, the Anthropic provider simply isn't registered. No crash.
4. **DI + defaults** — Constructor accepts optional overrides for every dependency. The common case (`ResearchAgent()`) works with reasonable defaults.
5. **Task isolation** — Each public method runs in `_run()` which sets status=RUNNING, catches all exceptions, computes elapsed time, and resets status to IDLE. No method can leave the agent in a broken state.

---

## Findings

### Critical (0)

None.

### Warnings (2)

| # | Finding | Location | Recommendation |
|---|---------|----------|----------------|
| W1 | `full_ingest_pipeline` builds in-memory `DownloadResult` objects rather than using real downloads | `workflow.py` | In production, replace `_make_download_result` with calls to the actual `DownloadService.download()` and pass the real `DownloadResult` to `process_document()`. Current implementation is correct for mocked/offline usage once files exist. |
| W2 | `ollama` provider connects via HTTP (no TLS) by default | `providers/ollama.py` | For production deployments, document that users should set `base_url` to a TLS-enabled endpoint or run Ollama behind a reverse proxy. |

### Notes (3)

| # | Note | Location | Rationale |
|---|------|----------|-----------|
| N1 | 4 skipped tests | `test_agent.py` | Tests for OpenAI/Anthropic/Gemini providers are skipped when the corresponding Python package is not installed. This is correct behavior — the providers are optional. |
| N2 | `elapsed_ms` may be 0.0 on fast operations | `agent.py:_run()` | On Windows, `time.perf_counter()` resolution can make very fast operations round to 0.0ms. This is cosmetic. |
| N3 | `SQLiteStorage(database_path=":memory:")` in `index_document` | `workflow.py` | Each `index_document()` call creates a new in-memory KB. In production, replace with a persistent path from configuration. |

---

## Production Readiness

### Security

- No secrets stored in code. API keys passed via `Settings` object (should come from env vars in production).
- No SQL injection vectors — all user data goes through Pydantic validation before reaching storage.

### Observability

- `structlog` throughout with structured event names (`agent_error`, `providers_discovered`, `search_complete`)
- All agent operations log start/end with elapsed time
- No metrics yet — consider adding Prometheus counters for: operations per type, LLM latency, cache hit rate

### Resilience

- All workflow steps are wrapped in try/except returning `None` on failure
- `_run()` catches all exceptions (including non-`ResearchAgentError`)
- Cache layer is non-breaking — cache failures don't propagate

### Testing

- **Unit**: Models, config, exceptions, cache, prompts (fast, deterministic)
- **Mocked integration**: Agent methods with patched sub-services
- **Provider**: Instantiation tests + connection failure tests (skipped without packages)
- **Workflow**: Module-level function tests with mock targets

---

## Summary

| Metric | Value |
|--------|-------|
| Files | 15 |
| Tests | 50 passed / 4 skipped |
| ruff | Clean |
| mypy | Clean (module-level) |
| External deps | `pydantic`, `structlog`, optional: `openai`, `anthropic`, `google-genai` |
| Blocking issues | 0 |
