# End-to-End Pipeline Report

## Pipeline Architecture

```
SearchService ──► DownloadService ──► DocumentProcessingService ──► KnowledgeBaseService ──► ResearchAgent ──► FastAPI
    │                    │                       │                         │                     │              │
    │  PubMed            │  Resolver chain        │  PyMuPDF extract       │  Chunking            │  RAG         │  REST
    │  EuropePMC         │  (PMC -> DOI ->        │  Section/ref/table/    │  Embedding           │  Summarize   │  JSON
    │  OpenAlex          │   Publisher)           │  figure extraction     │  SQLite storage      │  Similar     │  OpenAPI
    │  concurrent        │  PDF/XML download      │  Markdown generation   │  Vector store        │  Search      │  Types
    ▼                    ▼                       ▼                         ▼                     ▼              ▼
   articles            PDF path              ProcessedDocument          KnowledgeDocument     Answer+Sources   Response
```

## Data Flow

### 1. Search Service
**Input:** `(query: str, max_results: int = 10)`
**Output:** `list[Article]` (merged, deduplicated)
**Mechanism:**
- Fires concurrent requests to all enabled providers (PubMed, EuropePMC, OpenAlex)
- Semaphore bounds concurrency (default: 5)
- Each provider returns `list[Article]` with provenance tags
- Deduplication merges by DOI, then PMID, then PMCID
- Lists fields (keywords, authors, provenance) are unioned
- First-found abstract is preferred
- Provider failures are isolated — partial results still returned
- Response time: min(provider timeouts), typically 2–5s

### 2. Download Service
**Input:** `Article` (with DOI, PMID, PMCID)
**Output:** `DownloadResult` (with file_path)
**Mechanism:**
- Resolver chain tries: PMC -> DOI -> Publisher URL resolvers
- Each resolver returns `list[ContentInfo]` with confidence scores
- Highest-confidence candidate selected
- Downloader (PDF or XML) fetches the document
- Rate-limited per downloader (default: 3 req/s)
- Retry with backoff on transient failures
- Checksum verification on downloaded content
- Cached by article ID to avoid re-download
- Response time: 1–10s (network-bound)

### 3. Document Processing Service
**Input:** `DownloadResult` (with file_path)
**Output:** `ProcessedDocument` (with sections, metadata, references, tables, figures)
**Mechanism:**
- PDF text extraction via PyMuPDF (`fitz`)
- OCR detection (configurable fallback)
- Section parser: regex-based heading detection (Introduction, Methods, Results, etc.)
- Reference parser: regex-based citation extraction
- Table parser: simple text-based table detection
- Figure parser: caption extraction
- Metadata extraction: heuristic (first ~200 chars = title, last ~500 chars with "abstract" = abstract)
- Markdown generation from extracted sections
- Response time: 0.5–5s (CPU-bound, page count dependent)

### 4. Knowledge Base Service
**Input:** `ProcessedDocument`
**Output:** `KnowledgeDocument` (indexed with chunks and embeddings)
**Mechanism:**
- Chunking: section strategy (1 chunk per section heading) | fixed strategy | sentence strategy
- Embedding: configured provider (Ollama, Jina, OpenAI, Voyage) generates vector per chunk
- Storage: SQLite persists documents, chunks, embeddings metadata
- Vector store: ChromaDB (persistent) or FAISS (in-memory) indexes vectors for similarity search
- Transactional: document + chunks + embeddings stored atomically
- Response time: 0.5–3s (embedding-model-bound)

### 5. Research Agent
**Input:** `(question: str, document_id?: str, llm_params?: dict)`
**Output:** `AgentResult` (with Answer, sources, citations)
**Mechanism:**
- Embeds the user's question using the configured embedding provider
- Vector search retrieves top-k relevant chunks
- Builds context by joining chunk text
- Calls LLM provider (OpenAI, Anthropic, Google, Ollama) with QA prompt
- Returns Answer with confidence score, sources, citations
- Caches question-answer pairs (configurable TTL)
- Singleton agent (busy -> 409 Conflict)
- Endpoints: ask, summarize, similar, search_chunks, search_documents
- Response time: 1–5s (LLM-generation-bound)

### 6. FastAPI Layer
**Input:** HTTP Requests
**Output:** JSON Responses
**Endpoints (15):**

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/health` | System health |
| GET | `/api/v1/liveness` | Liveness probe |
| GET | `/api/v1/readiness` | Readiness probe |
| POST | `/api/v1/search` | Search literature |
| POST | `/api/v1/ingest` | Full ingest pipeline |
| POST | `/api/v1/ingest/download` | Download only |
| POST | `/api/v1/ask` | RAG question answering |
| GET | `/api/v1/documents` | List documents |
| GET | `/api/v1/documents/{id}` | Document detail |
| GET | `/api/v1/documents/{id}/chunks` | Document chunks |
| GET | `/api/v1/documents/{id}/summary` | Summarize document |
| GET | `/api/v1/documents/{id}/similar` | Similar documents |
| GET | `/api/v1/docs` | Swagger UI |
| GET | `/api/v1/redoc` | ReDoc UI |
| GET | `/api/v1/openapi.json` | OpenAPI schema |
| GET | `/metrics` | Prometheus metrics |

## Error Handling

| Scenario | HTTP Status | Error Code | Example |
|----------|-------------|------------|---------|
| Validation failure | 422 | `VALIDATION_ERROR` | Empty query, missing field |
| Agent busy | 409 | `AGENT_BUSY` | Concurrent request to same agent |
| Document not found | 404 | `DOCUMENT_NOT_FOUND` | Invalid document_id |
| Unknown LLM provider | 400 | `UNKNOWN_PROVIDER` | `provider="invalid_name"` |
| Internal error | 500 | `INTERNAL_ERROR` | Unexpected exception |
| Rate limited | 429 | `RATE_LIMIT_EXCEEDED` | >60 req/min per IP |
| Invalid host | 400 | n/a | Untrusted Host header |

## Bottleneck Analysis

### Current Bottlenecks

| Stage | Bottleneck | Type | Impact | Mitigation |
|-------|-----------|------|--------|------------|
| Search | Provider network latency | I/O-bound | 2-5s per query | Already concurrent. Timeout per provider. |
| Download | PDF download size | I/O-bound | 1-10s per paper | Caching, connection pooling, range requests |
| Process | PyMuPDF text extraction | CPU-bound | 0.5-5s per paper | Thread pool executor (not implemented) |
| Index | Embedding generation | CPU/GPU-bound | 0.5-3s per doc | Batch embedding, GPU acceleration |
| Ask | LLM inference | Network/GPU-bound | 1-5s per question | Streaming, caching, model quantization |

### Fixed Bottlenecks

| Bottleneck | Before | After | Fix |
|------------|--------|-------|-----|
| ChromaDB blocking | Sync calls blocked event loop | Wrapped in `run_in_executor` | `chroma.py` async wrapper |
| KB init timeout | Indefinite hang on startup | 30s timeout | `asyncio.wait_for` |
| Package installation | 5 packages missing from `find` | All 6 namespaces included | `pyproject.toml` |

## Data Integrity

### Cross-Stage Field Mapping

| Field | Search Article | DownloadResult | ProcessedDocument | KnowledgeDocument |
|-------|---------------|---------------|-------------------|-------------------|
| article_id / document_id | `id` | `article_id` | `article_id` | `document_id` |
| title | `title` | — | `metadata.title` | `metadata.title` |
| authors | `authors` | — | `metadata.authors` | `metadata.authors` |
| source | `source` | `source` | — | `metadata.source` |
| file_path | — | `file_path` | `source_file` | — |

### Deduplication Strategy
- Primary key: DOI (preferred)
- Secondary: PMID
- Tertiary: PMCID
- Fallback: title hash
- Provenance tracked as `list[str]` per article
- Merged fields: authors (union), keywords (union), provenance (union), abstract (first found)

## Verification

All stages produce valid, typed outputs. The `test_full_pipeline_end_to_end` test in `tests/e2e/test_full_pipeline.py` validates:
1. Search returns merged article with correct DOI and provenance
2. Download returns file path to existing PDF
3. Process returns `ProcessedDocument` with `status == "completed"`
4. Index returns `KnowledgeDocument` with `chunk_count > 0`
5. Ask returns `Answer` with sources referencing the indexed document
6. API returns valid 200 responses with correct schema

## Test Coverage

| Service | Test Files | Tests | Coverage Areas |
|---------|-----------|-------|---------------|
| Search Service | 10 files | 77 | Integration, dedup, rate limit, retry, resilience |
| Download Service | 3 files | 24 | Resolvers, downloaders, orchestration |
| Document Processing | 4 files | 21 | Text extraction, section/ref/table parsing |
| Knowledge Base | 7 files | 67 | Indexing, search, chunking, embedding, storage, vector |
| Research Agent | 1 file | 28 | Agent orchestration, caching |
| API (FastAPI) | 2 files | 27 | All endpoints, validation, errors, CORS |
| E2E Pipeline | 1 file | 10 | Full pipeline end-to-end |
| **Total** | **28 files** | **254** | |

## API Contract Validation

Frontend types are generated from the backend OpenAPI schema via `openapi-typescript`. The generated `web/lib/api-types.d.ts` covers all 15 endpoints with full request/response typing. The `npm run api:sync` script regenerates types from the backend schema.

All frontend API calls go through `lib/api-client.ts` (openapi-fetch) which is fully typed against the generated types. No `fetch()` calls bypass the typed client.
