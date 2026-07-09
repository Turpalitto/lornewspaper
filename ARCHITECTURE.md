# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js 15)                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │  Home    │ │  Search  │ │ Documents│ │   Ask    │ │ Ingest   │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│         TanStack Query  ·  openapi-fetch  ·  next-themes           │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTP / JSON
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI / Python 3.12)                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │  Health  │ │  Search  │ │  Ingest  │ │   Ask    │ │Documents │  │
│  │  /docs   │ │  /search │ │  /ingest │ │  /ask    │ │  /docs   │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│         Middleware: CORS · Security · Rate Limit · Logging          │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ResearchAgent (Orchestrator)                      │
│                                                                     │
│  search ──► download ──► process ──► index ──► embed ──► answer    │
│                                                                     │
│  Caches: ResponseCache (LRU) · LLM Provider Registry               │
└──────┬──────────────┬──────────────┬──────────────────┬─────────────┘
       │              │              │                  │
       ▼              ▼              ▼                  ▼
┌──────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
│  Search  │ │   Download   │ │  Document    │ │  Knowledge Base  │
│  Service │ │   Service    │ │  Processing  │ │   Service        │
│          │ │              │ │  Service     │ │                  │
│ PubMed   │ │ PMC Resolver │ │ PyMuPDF      │ │ SQLite Storage   │
│ EuropePMC│ │ DOI Resolver │ │ Sections     │ │ Chroma/FAISS     │
│ OpenAlex │ │ Publisher    │ │ References   │ │ Embeddings       │
│          │ │ PDF/XML      │ │ Tables       │ │ (Ollama/OpenAI/  │
│ Rate     │ │ Checksum     │ │ Figures      │ │  Jina/Voyage)    │
│ Limiter  │ │ Cache        │ │ Markdown     │ │ Chunking         │
└──────────┘ └──────────────┘ └──────────────┘ └──────────────────┘
```

## Data Flow

```
User Query
    │
    ▼
[SearchService] ──► PubMed, EuropePMC, OpenAlex (concurrent)
    │                  │     │     │
    │                  └─────┼─────┘
    │                   dedup by DOI/PMID
    ▼
[DownloadService] ──► PMC Resolver → DOI Resolver → Publisher
    │
    ▼
[DocumentProcessingService] ──► PyMuPDF text extraction
    │                            Section parsing
    │                            Reference extraction
    │                            Table/figure extraction
    │                            Markdown generation
    ▼
[KnowledgeBaseService] ──► Chunking (section/fixed/sentence)
    │                       Embedding generation
    │                       SQLite storage
    │                       Vector index (Chroma/FAISS)
    ▼
[ResearchAgent] ──► Embed query → Vector search → Build context → LLM
    │
    ▼
[FastAPI] ──► JSON response with citations
    │
    ▼
[Next.js] ──► Typed API client → TanStack Query → UI
```

## Layer Architecture

```
┌────────────────────────────────────────────┐
│              Presentation                  │
│  Next.js · React · Tailwind · shadcn/ui   │
├────────────────────────────────────────────┤
│              API Layer                     │
│  FastAPI · Pydantic · OpenAPI             │
├────────────────────────────────────────────┤
│           Application Layer                │
│  ResearchAgent · Job Queue · Cache        │
├────────────────────────────────────────────┤
│           Domain Services                  │
│  Search · Download · Process · Knowledge   │
├────────────────────────────────────────────┤
│           Infrastructure                   │
│  PostgreSQL · Redis · Qdrant · Chroma     │
└────────────────────────────────────────────┘
```

## Key Design Decisions

1. **Protocol-based providers**: `BaseProvider`, `BaseResolver`, `BaseDownloader`,
   `BaseVectorStore`, `BaseEmbeddingProvider` — each with registry pattern.
2. **Async throughout**: All I/O and CPU-bound operations are async.
   Blocking operations run in thread pool via `asyncio.to_thread()`.
3. **OpenAPI contract**: Frontend types auto-generated from backend schema.
   Single source of truth, no manual type duplication.
4. **Pluggable backends**: Job queue, vector store, LLM providers, embedding
   providers all use ABC interfaces — swap without API changes.
5. **Singleton agent**: `ResearchAgent` with `AGENT_BUSY` mutex protects
   against concurrent LLM calls. Planned: connection pool in v1.1.
