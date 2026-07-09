# SearchService — Architecture Review Report

**Reviewer role:** Staff Engineer / Production Readiness
**Date:** 2026-07-09
**Scope:** `search_service/` (M1–M7) + tests
**Verdict:** Production-ready after the fixes below were applied. 62 tests pass; `ruff` and `mypy` clean.

---

## Strengths

- Clean **DIP**: `SearchService` depends only on `BaseProvider`; concrete providers are resolved via a registry and never imported by the orchestrator.
- **SRP**: cross-cutting concerns (HTTP pool, rate limiting, retry, logging, validation) live in dedicated modules and are composed into `BaseProvider._fetch`.
- **OCP**: adding a source = new class + one registry entry + one config row; core untouched.
- Transient-only retry with `Retry-After` honouring, per-provider token-bucket limiter, structured logging, and partial-failure isolation are all implemented correctly.
- Strong test coverage with no real network (respx / MockTransport).

---

## Findings & resolutions

### 1. Architecture
| Sev | Issue | Resolution |
|-----|-------|------------|
| — | SOLID / SoC / DIP | Sound (see Strengths). No change. |
| Low | `Article.raw_response` declared but never populated | Left unpopulated by design (spec: optional, avoids memory bloat). Opt-in if needed later. |

### 2. Async implementation
| Sev | Issue | Resolution |
|-----|-------|------------|
| **High** | `SearchService` advertised `async with` in README but `__aenter__/__aexit__` were never implemented → `async with SearchService()` raised `AttributeError`. | Implemented `__aenter__/__aexit__` (aclose on exit). Added regression test. |
| **High** | `retries` contextvar set in `before_sleep` but never reset → a prior call's retry count leaked into the next call's log line. | Reset `set_retries(0)` at the start of every `_fetch`. |
| Medium | Cancellation safety: `_fetch` caught only `Exception`, so on `CancelledError` the `RequestLog.__exit__` (final log line) was skipped. | Changed to `except BaseException`, always emit log line, re-raise without suppressing. |
| Low | `create_client` opens a pool; if `aclose` forgotten the client leaks. | Mitigated via the new context manager; documented. (No `__del__`—avoids gc-timeout pitfalls.) |
| — | Connection lifecycle / semaphore / race conditions | Semaphore guards provider concurrency; shared client owned solely by `SearchService` (providers get it injected, so they don't double-close). Correct. |

### 3. API design
| Sev | Issue | Resolution |
|-----|-------|------------|
| Low | Inconsistent error type (`ValueError` for unknown provider). | Introduced `SearchServiceError`/`UnknownProviderError` hierarchy; `search_by_provider` raises `UnknownProviderError` (still a `ValueError` subclass → backward compatible). |
| — | Ergonomics / future compatibility | `search_all/search_by_provider/search_by_date/search_by_pmid` are consistent; keyword args stable. Good. |

### 4. Error handling
| Sev | Issue | Resolution |
|-----|-------|------------|
| Medium | **Double backoff on 429**: limiter `pause(Retry-After)` AND tenacity also slept `Retry-After` → ~2× wait. | tenacity now uses exponential jitter only; the rate limiter owns `Retry-After` enforcement. |
| — | Retry policy (transient-only), timeout handling, partial failures | Correct as designed; verified by tests. |
| Low | Thin exception hierarchy | Added `exceptions` module (see API design). |

### 5. Performance
| Sev | Issue | Resolution |
|-----|-------|------------|
| Low | `limit` not validated → could send oversized page sizes to APIs (errors / memory). | Per-provider cap: PubMed 100, Europe PMC 100, OpenAlex 200 (`_MAX_LIMIT` + clamp). |
| — | Allocations / duplicate work / batching | PubMed already batches PMID→efetch in one request. No redundant work found. `deduplicate` is O(n²) (fine for typical n). No change. |

### 6. Security
| Sev | Issue | Resolution |
|-----|-------|------------|
| Low | SSRF surface: providers fetch `config.base_url`. | `base_url` is trusted configuration (not user input); user `query` is URL-encoded by httpx. No user-controlled URL is ever fetched. Acceptable; documented. (A URL allowlist would be overengineering for trusted-config deployments.) |
| Low | Logging of `query` (potential PII). | `query` is the search term by design; no secrets/API keys are logged (OpenAlex `mailto` stays in params, not logs). Acceptable. |

### 7. Testing
| Sev | Issue | Resolution |
|-----|-------|------------|
| Low | No property/edge tests for dedupe; deprecated `event_loop` fixture. | Added: idempotence, order-independence, anagram non-merge, single-bound date filter, async-context-manager test. Removed deprecated `event_loop`/`anyio_backend` fixtures. |
| Low | Rate-limiter test uses timing threshold (minor flake risk). | Generous margin (0.15s vs ~0.25s wait); stable in practice. |
| — | Stress / concurrency | Covered: `test_performance_concurrency_bounded` asserts max in-flight ≤ limit. |

### 8. Documentation
| Sev | Issue | Resolution |
|-----|-------|------------|
| Low | Errors/async-with not documented. | README updated with Errors section + confirmed async-context-manager usage. |

### 9. Technical debt
| Sev | Issue | Resolution |
|-----|-------|------------|
| Low | `map_fn`/`_fetch` return types loose (`list[Any] | Any`). | Acceptable given provider mapping variety; not worth stricter generics that would complicate the ABC. |
| — | Overengineering | Deliberately avoided: global search deadline, response URL allowlist, populating `raw_response`, extra exception types. Each would add complexity without proportional value for the stated requirements. |

---

## What was implemented this review
- `search_service/exceptions.py` (new) + `UnknownProviderError` used by `SearchService`.
- `SearchService.__aenter__/__aexit__`.
- `set_retries(0)` reset in `BaseProvider._fetch`; `except BaseException` cancellation-safe logging.
- Removed 429 double-backoff in `retry.py`.
- Title-dedup now requires both token-set Jaccard **and** sequence ratio ≥ 0.9 (fixes anagram + templated-title false merges).
- Date-range single-bound support (Europe PMC `>=`/`<=`; PubMed full `YYYY-MM-DD` dates).
- Per-provider `limit` clamping.
- Tests: async-context-manager, single-bound dates, dedupe idempotence/order/anagram; removed deprecated fixtures.

## Verification
```
pytest  -> 62 passed
ruff    -> All checks passed
mypy    -> Success: no issues found in 15 source files
```
