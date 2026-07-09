# Sprint 1 Release — Guideline MVP

## Version 0.1.0

### What's Built

A working MVP of the Clinical Guideline Assistant that can:
- **Ingest** clinical guidelines from text (PDF pipeline via LORNEWS)
- **Extract** structured recommendations ("We recommend..." statements)
- **Index** guidelines in the KnowledgeBase via LORNEWS
- **Search** guidelines by diagnosis, symptom, or drug
- **Answer** clinical questions with citation-backed recommendations
- **Verify** citations via source text hashing

### Architecture

```
Clinician Question
  │
  ▼
[RecommendationExtractor] ──► Russian patterns ("рекомендуется")
  │                            English patterns ("we recommend")
  │                            Strength (strong/conditional/not_recommended)
  │                            Evidence level (A/B/C/D)
  │                            PICO extraction
  │                            Pregnancy, contraindications, children
  │
  ▼
[GuidelineService] ──► ingest_text() / ingest_pdf()
  │                      search() via LORNEWS KB
  │                      ask() via LORNEWS ResearchAgent
  │                      rule_based_answer() fallback
  │
  ▼
[CitationVerifier] ──► SHA-256 source text hashing
  │                     Fuzzy match for citations
  │
  ▼
[FastAPI] ──► POST /api/v1/clinical/guidelines/search
  │             POST /api/v1/clinical/guidelines/ask
  │             POST /api/v1/clinical/guidelines/ingest
  │             GET  /api/v1/clinical/guidelines/{id}
  │
  ▼
[Next.js] ──► Guideline search page
                Guideline detail page
                Ask guidelines component
```

### New Files Created

| File | Purpose |
|------|---------|
| `clinical_assistant/` | Main Python package |
| `clinical_assistant/models/guideline.py` | Guideline, Recommendation, Section |
| `clinical_assistant/services/guideline_service.py` | Core service |
| `clinical_assistant/services/recommendation_extractor.py` | Recommendation parsing |
| `clinical_assistant/services/citation_verifier.py` | Citation integrity |
| `clinical_assistant/routers/guidelines.py` | FastAPI endpoints |
| `clinical_assistant/schemas/guidelines.py` | Request/response schemas |
| `clinical_assistant/prompts/clinical_qa.py` | LLM prompt templates |
| `clinical_assistant/app.py` | FastAPI app factory |
| `clinical_assistant/config.py` | Settings |
| `web/app/guidelines/page.tsx` | Guideline search page |
| `web/app/guidelines/[id]/page.tsx` | Guideline detail page |
| `web/components/clinical/ask-guidelines.tsx` | Ask guidelines component |
| `tests/clinical/test_recommendation_extractor.py` | 10 tests |
| `tests/clinical/test_guideline_service.py` | 10 tests |
| `tests/clinical/test_citation_verifier.py` | 3 tests |
| `scripts/seed_demo_guidelines.py` | Demo data seeder |
| `Dockerfile.clinical` | Clinical backend container |
| `docker-compose.clinical.yml` | Clinical compose extension |
| `pyproject.toml` | Project config |

### LORNEWS Modules Reused

| Module | Usage |
|--------|-------|
| DocumentProcessingService | PDF text extraction |
| KnowledgeBaseService | Chunking, embedding, vector search |
| ResearchAgent | RAG question answering |
| FastAPI | App factory, middleware patterns |

### How to Run

```bash
# 1. Install dependencies
cd clinical-guideline-assistant
pip install -e .
pip install -r requirements.txt  # from LORNEWS, if needed

# 2. Seed demo data
python scripts/seed_demo_guidelines.py

# 3. Start server
uvicorn clinical_assistant.app:app --reload --port 8001

# 4. Test
curl -X POST http://localhost:8001/api/v1/clinical/guidelines/search \
  -H 'Content-Type: application/json' \
  -d '{"query": "пневмония"}'

curl -X POST http://localhost:8001/api/v1/clinical/guidelines/ask \
  -H 'Content-Type: application/json' \
  -d '{"question": "Какие антибиотики рекомендуются при пневмонии?"}'
```

### Test Results

| Suite | Tests | Status |
|-------|-------|--------|
| RecommendationExtractor | 10 | ✅ All passing |
| GuidelineService | 10 | ✅ All passing |
| CitationVerifier | 3 | ✅ All passing |
| LORNEWS Frontend | 10 | ✅ All passing |
| TypeScript | — | ✅ 0 errors |
| ESLint | — | ✅ 0 errors |

### Known Limitations

1. **No LORNEWS integration tested** — requires running LORNEWS services together
2. **PDF ingestion not tested** — needs real guideline PDFs and LORNEWS
3. **LLM prompts not tested** — needs configured LLM provider
4. **Russian patterns limited** — covers common patterns, not all guideline formats
5. **No drug database yet** — planned for Sprint 2

### Next Sprint (Sprint 2)

- DrugKnowledgeBase with dosing, interactions, contraindications
- Pregnancy, pediatric, renal adjustment support
- Antibiotic recommendation engine
