# End-to-End Validation Report

## Pipeline Stages

### Stage 1: SearchService — Provider Integration

| Provider | Mocked | Articles Returned | Deduplication | Latency (mocked) |
|----------|--------|-------------------|---------------|------------------|
| PubMed | `respx` fixture | 1 | DOI merge | ~50ms |
| EuropePMC | `respx` fixture | 1 | DOI merge | ~50ms |
| OpenAlex | `respx` fixture | 1 | DOI merge | ~50ms |

**Result:** ✅ 3 providers → 1 merged article with union provenance (`["pubmed", "europepmc", "openalex"]`)

### Stage 2: DownloadService — Resolver Chain

| Resolver | Tried | Result |
|----------|-------|--------|
| PMC | ✅ | Hits first |
| DOI | Fallback | — |
| Publisher | Fallback | — |

**Result:** ✅ Download result with file path to local PDF

### Stage 3: DocumentProcessingService — PDF Extraction

| Step | Status |
|------|--------|
| PyMuPDF text extraction | ✅ |
| Section parsing (Intro/Methods/Results) | ✅ |
| Reference extraction | ✅ |
| Markdown generation | ✅ |

**Result:** ✅ `ProcessedDocument` with 3 sections, `status = "completed"`

### Stage 4: KnowledgeBaseService — Indexing

| Sub-stage | Status |
|-----------|--------|
| Section chunking | ✅ 3 chunks |
| Embedding generation (mock) | ✅ 4-dim vectors |
| SQLite storage | ✅ Document + chunks persisted |
| Vector store (DictVectorStore) | ✅ Embeddings indexed |

**Result:** ✅ `KnowledgeDocument` with `chunk_count = 3`, `status = COMPLETED`

### Stage 5: ResearchAgent — RAG Question Answering

| Step | Status |
|------|--------|
| Embed question | ✅ |
| Vector search | ✅ Retrieved chunks from indexed doc |
| Context building | ✅ |
| Answer generation | ✅ (cached) |
| Citation verification | ✅ Sources reference `processed.article_id` |

**Result:** ✅ Answer returned with valid citations

### Stage 6: FastAPI — REST API Validation

| Endpoint | Method | Status |
|----------|--------|--------|
| `/api/v1/health` | GET | ✅ 200 |
| `/api/v1/liveness` | GET | ✅ 200 |
| `/api/v1/readiness` | GET | ✅ 200 |
| `/api/v1/search` | POST | ✅ 200/422 |
| `/api/v1/ask` | POST | ✅ 200/409 |
| `/api/v1/documents` | GET | ✅ 200 |
| `/metrics` | GET | ✅ 200 (Prometheus format) |

**Result:** ✅ All endpoints respond with correct schemas

## Metadata Validation

| Check | Result | Details |
|-------|--------|---------|
| Title preserved | ✅ | `metadata.title` survives index→retrieve |
| Abstract preserved | ✅ | `metadata.abstract` survives round-trip |
| Authors preserved | ✅ | `metadata.authors` intact |
| Document ID consistent | ✅ | Same across all 5 services |
| Chunk headings | ✅ | ALL section headings represented in chunks |
| Delete removes all data | ✅ | Document + chunks + vectors removed |

## Citation Integrity

| Check | Result |
|-------|--------|
| Sources reference indexed doc ID | ✅ |
| Answer non-empty | ✅ |
| Multiple documents coexist | ✅ |
| Empty KB returns empty | ✅ |

## Test Execution

```bash
# Full pipeline (6 stages)
pytest tests/e2e/test_full_pipeline.py -v

# Metadata validation (9 tests)
pytest tests/e2e/test_stage_metadata.py -v

# E2E via Playwright (24 tests)
cd web && npx playwright test
```

See full benchmark data in `benchmark_report.md`.
