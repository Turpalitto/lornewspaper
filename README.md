<img src="https://img.shields.io/badge/python-3.12-blue" alt="Python"> <img src="https://img.shields.io/badge/next.js-15-black" alt="Next.js"> <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
<img src="https://img.shields.io/github/actions/workflow/status/anomalyco/lornewspaper/ci.yml?label=CI" alt="CI">
<img src="https://img.shields.io/github/actions/workflow/status/anomalyco/lornewspaper/release.yml?label=Release" alt="Release">
<img src="https://img.shields.io/badge/tests-288%20passing-brightgreen" alt="Tests">

# LORNEWS

**Open-source academic research platform. Search, ingest, and ask questions about millions of scientific papers.**

Search across PubMed, Europe PMC, and OpenAlex. Download full-text PDFs. Extract structure (sections, references, tables, figures). Index in a vector knowledge base. Ask questions with AI-powered answers and real citations.

```bash
docker compose --profile optional up -d
# → Frontend at http://localhost:3000
# → API at http://localhost:8000/api/v1
# → Docs at http://localhost:8000/api/v1/docs
```

> **Live demo**: _Deploy free in 45 min → [FREE_DEPLOYMENT_GUIDE.md](docs/FREE_DEPLOYMENT_GUIDE.md) (Render + Cloudflare Pages + Supabase, $0/mo)_

---

## Feedback

Every page has a 💬 button (bottom-right) to:
- 🐞 **Report issue** → opens GitHub issue with bug template
- 💡 **Suggest improvement** → opens GitHub issue with feature template
- 👍/👎 **Rate today's digest** → stored locally, helps prioritize fixes

We read every submission. Your feedback shapes the roadmap.

---

## Features

🔍 **Multi-provider search** — PubMed, Europe PMC, OpenAlex. Concurrent, deduplicated, provider-isolated.

📥 **Full ingest pipeline** — Search → Download → Process → Index → Query. Automated end-to-end.

📄 **PDF extraction** — Sections, references, tables, figures, markdown. No GROBID required.

🧠 **RAG question answering** — Embed questions, retrieve chunks, generate answers with citations.

📊 **Knowledge base** — Chunking (3 strategies), embedding (4 providers), vector storage (Chroma/FAISS/Qdrant).

🎨 **Modern frontend** — Next.js 15, dark/light theme, responsive, 7 pages.

🔧 **Pluggable architecture** — Swap LLM providers, embedding models, vector stores without code changes.

---

## Quick Start

### Docker (recommended)

```bash
# Clone
git clone https://github.com/anomalyco/lornewspaper && cd lornewspaper

# Start everything
cp .env.example .env
docker compose --profile optional up -d

# Verify
curl http://localhost:8000/api/v1/health
```

### Local development

```bash
# Backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e .
uvicorn api.app:app --reload --port 8000

# Frontend (separate terminal)
cd web && npm install && npm run dev
```

---

## Screenshots

| Home Dashboard | Literature Search | Document Detail |
|:---:|:---:|:---:|
| ![Home](https://raw.githubusercontent.com/anomalyco/lornewspaper/main/web/public/screenshots/home.png) | ![Search](https://raw.githubusercontent.com/anomalyco/lornewspaper/main/web/public/screenshots/search.png) | ![Documents](https://raw.githubusercontent.com/anomalyco/lornewspaper/main/web/public/screenshots/documents.png) |

| RAG Q&A | Ingest Pipeline | Editorial View |
|:---:|:---:|:---:|
| ![Ask](https://raw.githubusercontent.com/anomalyco/lornewspaper/main/web/public/screenshots/ask.png) | ![Ingest](https://raw.githubusercontent.com/anomalyco/lornewspaper/main/web/public/screenshots/ingest.png) | ![Editorial](https://raw.githubusercontent.com/anomalyco/lornewspaper/main/web/public/screenshots/editorial.png) |

| Daily Digest | Discovery Feed | System Settings |
|:---:|:---:|:---:|
| ![Digest](https://raw.githubusercontent.com/anomalyco/lornewspaper/main/web/public/screenshots/digest.png) | ![Discovery](https://raw.githubusercontent.com/anomalyco/lornewspaper/main/web/public/screenshots/discovery.png) | ![Settings](https://raw.githubusercontent.com/anomalyco/lornewspaper/main/web/public/screenshots/settings.png) |

> *Screenshots stored in `web/public/screenshots/`. Regenerate: `npx tsx screenshot_script.ts` from `web/`.*
> *Demo GIF frames at `web/public/screenshots/demo_frames/`. Convert: `ffmpeg -framerate 0.5 -i ...%02d-*.png ... demo_flow.gif` or use https://ezgif.com/maker .*

---

## API Examples

```bash
# Search
curl -X POST http://localhost:8000/api/v1/search \
  -H 'Content-Type: application/json' \
  -d '{"query": "transformer neural network", "max_results": 5}'

# Ingest
curl -X POST http://localhost:8000/api/v1/ingest \
  -H 'Content-Type: application/json' \
  -d '{"query": "attention is all you need", "max_results": 3}'

# Ask
curl -X POST http://localhost:8000/api/v1/ask \
  -H 'Content-Type: application/json' \
  -d '{"question": "What are the key contributions of the transformer paper?"}'

# List documents
curl http://localhost:8000/api/v1/documents

# Health
curl http://localhost:8000/api/v1/health
```

---

## Architecture

```
Search ──► Download ──► Process ──► Index ──► Embed ──► Ask
  │           │            │           │         │         │
  PubMed     PMC         PyMuPDF     SQLite    Ollama    RAG
  EuropePMC  DOI         Sections    Chroma    OpenAI    + LLM
  OpenAlex   Publisher   Refs/Tables FAISS     Jina
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for full details.

---

## Project Structure

```
lornewspaper/
├── api/                    # FastAPI REST API (15 endpoints)
├── research_agent/         # LLM orchestration
├── search_service/         # Academic search (3 providers)
├── download_service/       # PDF/XML download
├── document_processing_service/ # PDF extraction
├── knowledge_base/         # Chunking, embedding, storage
├── web/                    # Next.js 15 frontend
├── tests/                  # Backend tests (254)
├── docs/                   # Documentation
├── Dockerfile              # Backend container
├── docker-compose.yml      # Full stack orchestration
└── web/Dockerfile          # Frontend container
```

---

## Deployment

| Platform | Guide |
|----------|-------|
| Docker Compose | `docker compose --profile optional up -d` |
| Railway | [docs/deployment.md](docs/deployment.md#railway) |
| Fly.io | [docs/deployment.md](docs/deployment.md#flyio) |
| Render | [docs/deployment.md](docs/deployment.md#render) |
| DigitalOcean | [docs/deployment.md](docs/deployment.md#digitalocean) |

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| API Framework | FastAPI |
| Database | SQLite / PostgreSQL |
| Vector Store | ChromaDB / FAISS / Qdrant |
| LLM Providers | OpenAI, Anthropic, Google, Ollama |
| Embeddings | Ollama, OpenAI, Jina, Voyage |
| Frontend | Next.js 15, React 19, Tailwind 4 |
| State | TanStack Query |
| HTTP Client | openapi-fetch (typed) |
| Container | Docker, Docker Compose |
| CI/CD | GitHub Actions |

---

## Testing

```bash
# Backend
pytest                          # 254 unit + integration tests
pytest tests/e2e -v             # Full pipeline e2e
python tests/e2e/benchmark_runner.py --dataset smoke

# Frontend
cd web && npm test               # 10 component tests
npx playwright test              # 24 e2e tests
```

---

## License

MIT — see [LICENSE](LICENSE).

---

## Contributors

<a href="https://github.com/anomalyco/lornewspaper/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=anomalyco/lornewspaper" />
</a>

---

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=anomalyco/lornewspaper&type=Date)](https://star-history.com/#anomalyco/lornewspaper&Date)
