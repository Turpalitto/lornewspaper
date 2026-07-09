# Content Discovery Engine — Code Review

## Files Created

### Backend (13 files)

| File | Lines | Purpose |
|------|-------|---------|
| `api/discovery/__init__.py` | 12 | Exports |
| `api/discovery/models.py` | 86 | Data models |
| `api/discovery/engine.py` | 132 | Core pipeline |
| `api/discovery/quality_filter.py` | 108 | Quality filters |
| `api/discovery/author_graph.py` | 138 | Author network |
| `api/discovery/trend_analysis.py` | 128 | Trend detection |
| `api/discovery/strategies/__init__.py` | 1 | Package |
| `api/discovery/strategies/keyword_search.py` | 56 | Keyword strategy |
| `api/discovery/strategies/citation_expansion.py` | 88 | Citation strategy |
| `api/discovery/strategies/reference_expansion.py` | 76 | Reference strategy |
| `api/discovery/strategies/author_tracking.py` | 82 | Author strategy |
| `api/discovery/strategies/journal_tracking.py` | 100 | Journal strategy |
| `api/discovery/strategies/trend_detection.py` | 138 | Trend strategy |
| `api/discovery/routers.py` | 68 | API endpoints |
| `api/discovery/schemas.py` | 128 | Pydantic schemas |

### Frontend (6 files)

| File | Purpose |
|------|---------|
| `web/app/discovery/page.tsx` | Discovery dashboard |
| `web/app/discovery/trending/page.tsx` | Trending topics |
| `web/app/discovery/authors/page.tsx` | Top authors |
| `web/app/discovery/journals/page.tsx` | Top journals |

### Tests (4 files, 24 tests)

| File | Tests | Focus |
|------|-------|-------|
| `test_discovery/test_quality_filter.py` | 9 | Dedup, retracted, predatory, conference |
| `test_discovery/test_author_graph.py` | 5 | Author counting, paper tracking |
| `test_discovery/test_trend_analysis.py` | 6 | Procedure, device, drug, technique detection |
| `test_discovery/test_engine.py` | 7 | Pipeline, strategies, trending |

**Total: 24 tests**

## Verification

| Check | Result |
|-------|--------|
| TypeScript | ✅ 0 errors |
| Vitest | ✅ 10/10 passing |
| ESLint | ✅ 0 errors |

## Discovery Strategy Comparison

| Strategy | Coverage | Quality | Freshness |
|----------|----------|---------|-----------|
| Keyword Search | 11 ENT topics | Medium | Real-time |
| Citation Expansion | 12 landmark papers | High | Lagging |
| Reference Expansion | Top papers | High | Lagging |
| Author Tracking | 12 institutions | High | Real-time |
| Journal Tracking | 8 journals | High | Real-time |
| Trend Detection | 20 topics | Medium | Real-time |

## Data Sources

| Source | Strategies Using It |
|--------|--------------------|
| PubMed | Keyword, Journal, Trend |
| Europe PMC | Keyword (via SearchService) |
| OpenAlex | Keyword, Citation, Reference |
| Crossref | Citation |
| — | Author (via SearchService + OpenAlex) |

## Known Limitations

1. **Citation/Reference strategies hit OpenAlex API limits** — no caching of results
2. **Author tracking uses fixed institution list** — not dynamically discovered
3. **Predatory journal detection is regex-based** — may miss new patterns
4. **Trend growth rates use 2-year comparison** — may be noisy for low-count topics
5. **No arXiv/bioRxiv/medRxiv integration yet** — noted in data sources but not wired
