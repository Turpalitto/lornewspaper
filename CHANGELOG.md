# Changelog

All notable changes to LORNEWS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.0.0] — 2026-07-09

### Added

#### Core Platform
- Academic literature search (PubMed, Europe PMC, OpenAlex)
- PDF download with resolver chain (PMC → DOI → Publisher)
- Document processing pipeline (text extraction, sections, references, tables, figures)
- Knowledge base with chunking, embedding, and vector storage
- RAG question answering with citation tracking
- Document summarization and similarity analysis
- Background job queue for async ingestion
- Prometheus metrics endpoint
- Structured logging (structlog) with request IDs

#### API (15 endpoints)
- Health, liveness, readiness probes
- Search, ingest, download operations
- Document CRUD with pagination
- Question answering (RAG)
- Summarization and similarity
- Background job management
- OpenAPI documentation (Swagger + ReDoc)

#### Frontend (7 pages)
- Home dashboard with quick actions
- Literature search with result metadata
- Document browsing and detail view
- RAG question answering interface
- Ingest pipeline with progress
- System settings and health monitoring
- Dark/light theme with persistence

#### Security
- Security headers (HSTS, XFO, CSP, Permissions-Policy)
- CORS configuration
- Rate limiting (60 req/min/IP)
- Trusted hosts validation
- Startup environment validation
- Secrets scanning prevention

#### Infrastructure
- Multi-stage Docker builds (backend 180MB, frontend 250MB)
- Docker Compose for full-stack orchestration (6 services)
- GitHub Actions CI (9 job types)
- GitHub Actions CD (automated releases)
- Docker image publishing to GHCR

#### Performance
- All CPU-bound operations in thread pool (zero event loop blocking)
- Concurrent provider fan-out with semaphore bounding
- Response caching for LLM Q&A
- GZip compression on all endpoints
- Static asset compression
- Connection pooling for HTTP clients

#### Testing (288+ tests)
- 254 backend tests (unit + integration + e2e)
- 10 frontend component tests
- 24 Playwright e2e tests
- Benchmark runner (smoke/medium/large datasets)
- Load test runner (10-250 concurrent users)
- Security audit scanner

#### Documentation
- Deployment guide (6 platforms)
- Operations guide with monitoring
- Production checklist
- Architecture deep-dive
- E2E validation report
- Performance benchmarks
- Security audit report
- Platform scorecard
- Acceptance test report
- API reference (OpenAPI auto-generated)

### Fixed
- Event loop blocking in PyMuPDF, FAISS, OCR, chunking, file I/O
- Import fallback classes removed (fail-fast on missing dependencies)
- Startup timeout for knowledge base initialization
- Default SECRET_KEY blocks startup (exits with error)
- ChromaDB synchronous calls wrapped in executor
- Package discovery includes all 6 Python packages
- Frontend Docker HEALTHCHECK targets frontend, not backend

### Security
- `SECRET_KEY` default value blocked by `env_validator` (exits with 1)
- All containers run as non-root user
- HEALTHCHECK on all containers
- CORS/trusted hosts warnings at startup
- Rate limiting enabled by default

## [0.1.0] — 2026-06-01

### Added
- Initial project scaffolding
- SearchService with PubMed, EuropePMC, OpenAlex
- DownloadService with resolver chain
- DocumentProcessingService with PyMuPDF extraction
- KnowledgeBaseService with SQLite + ChromaDB
- ResearchAgent with RAG orchestration
- FastAPI REST API
- Next.js frontend scaffold
