# Daily Digest Engine — Code Review

## Files Created

### Backend (8 files)

| File | Line Count | Purpose |
|------|-----------|---------|
| `api/digest/__init__.py` | 10 | Package exports |
| `api/digest/models.py` | 128 | Data models (Digest, DigestItem, Topic, enums) |
| `api/digest/search_queries.py` | 68 | ENT topic search queries for PubMed |
| `api/digest/ranking.py` | 109 | Clinical importance ranking algorithm |
| `api/digest/grouping.py` | 124 | Topic assignment, study design detection, tags |
| `api/digest/generator.py` | 175 | Core digest generation pipeline |
| `api/digest/scheduler.py` | 78 | Daily 06:00 UTC scheduling |
| `api/digest/routers.py` | 78 | 5 API endpoints |
| `api/digest/schemas.py` | 128 | Pydantic request/response models |

### Frontend (6 files)

| File | Purpose |
|------|---------|
| `web/app/digest/page.tsx` | Today's/weekly/monthly digest view |
| `web/app/digest/topic/[name]/page.tsx` | ENT topic page |
| `web/app/digest/saved/page.tsx` | Bookmarked papers |
| `web/components/digest/digest-card.tsx` | Paper card with evidence badge |
| `web/components/digest/topic-card.tsx` | Topic summary card |

### Tests (4 files)

| File | Tests |
|------|-------|
| `tests/test_digest/test_ranking.py` | 9 tests |
| `tests/test_digest/test_grouping.py` | 11 tests |
| `tests/test_digest/test_generator.py` | 9 tests |

**Total: 29 tests**

## Verification

| Check | Result |
|-------|--------|
| TypeScript (`tsc --noEmit`) | ✅ 0 errors |
| Vitest (10 tests) | ✅ 10/10 passing |
| ESLint | ✅ 0 errors |

## LORNEWS Reuse

| Module | How Used |
|--------|----------|
| `SearchService` | ENT topic literature search |
| `KnowledgeBaseService` | (Future) Indexing digest papers |
| `ResearchAgent` | (Future) LLM topic summarization |
| Job queue | (Future) Scheduled digest generation |
| Frontend patterns | Card, Badge, Button, LoadingState |

## Edge Cases Handled

| Case | Handling |
|------|----------|
| No papers found | Empty topic shows "No papers" message |
| Unknown topic | 404 with valid topic list |
| LORNEWS unavailable | Graceful fallback (mock items) |
| API error | Retry UI shown |
| Empty trending list | Trending section hidden |
| Multiple topics per paper | All assigned (multi-topic papers) |
| Very old papers | Recency weight decreases linearly |

## Known Limitations

1. **No LLM summarization yet** — Topic summaries are placeholder text. Requires ResearchAgent with configured LLM.
2. **No digest persistence** — Digests are generated in-memory. Not persisted across restarts.
3. **No dedup across topics** — Multi-topic papers appear in multiple topic groups.
4. **LocalStorage-only bookmarks** — Saved papers don't sync across devices.
5. **Fixed schedule** — Scheduler runs at 06:00 UTC. Not configurable without code change.

## Sprint Velocity

| Category | Files | Lines | Tests |
|----------|-------|-------|-------|
| Backend | 9 | ~850 | 29 |
| Frontend | 5 | ~350 | — |
| Total | 14 | ~1200 | 29 |
| **Effort** | | **~3 days** | |
