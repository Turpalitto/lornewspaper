# Frequently Asked Questions

## General

### What is LORNEWS?
LORNEWS is an open-source research platform that searches academic literature,
downloads papers, extracts content, indexes them in a knowledge base, and
answers questions using retrieval-augmented generation (RAG).

### Do I need GPU hardware?
No. GPU is only needed for local LLM inference (Ollama). You can use cloud
LLM providers (OpenAI, Anthropic, Google) without GPU.

### What databases are supported?
- PostgreSQL (production)
- SQLite (development, embedded)
- ChromaDB / FAISS / Qdrant (vector storage)

## Setup

### How do I start the platform?
```bash
docker compose --profile optional up -d
```

### How do I run without Docker?
See [CONTRIBUTING.md](CONTRIBUTING.md#quick-start).

### What LLM providers are supported?
OpenAI, Anthropic, Google Gemini, and Ollama (local).

## Usage

### How do I search for papers?
Use the Search page or `POST /api/v1/search` with a query string.

### How do I ingest a paper?
Use the Ingest page or `POST /api/v1/ingest` with a search query.
The pipeline will search, download, process, and index matching papers.

### How do I ask questions about my documents?
Use the Ask page or `POST /api/v1/ask` with your question.
The system retrieves relevant chunks and generates an answer.

### How long does ingestion take?
- Single paper: ~10-30 seconds (search + download + process + index)
- Dependent on PDF size, network speed, and embedding model

## Troubleshooting

### The frontend can't reach the backend
Make sure the backend is running on port 8000. The frontend proxies `/api/v1/*`
to `http://localhost:8000` in development.

### Rate limiting is too strict
Set `RATE_LIMIT_PER_MINUTE` to a higher value (default: 60).

### The app won't start
Run validate_env() manually:
```bash
python -c "from api.env_validator import validate_env; print(validate_env())"
```
