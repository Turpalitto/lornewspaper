# Contributing to LORNEWS

We welcome contributions! This document explains the development process.

## Quick Start

```bash
# Clone
git clone https://github.com/anomalyco/lornewspaper
cd lornewspaper

# Backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

# Frontend
cd web && npm install

# Run
uvicorn api.app:app --reload --port 8000 &
cd web && npm run dev
```

## Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Make changes
4. Run tests
5. Submit a pull request

## Coding Standards

### Python
- **Formatter**: Ruff (`ruff check . && ruff format .`)
- **Type checker**: MyPy (`mypy . --ignore-missing-imports`)
- **Style**: Follow existing patterns in the codebase
- **Async**: All I/O-bound and CPU-bound code must be async. Use `asyncio.to_thread()` for blocking operations.

### TypeScript
- **Formatter**: Prettier (via ESLint)
- **Type checker**: TypeScript strict (`tsc --noEmit`)
- **Framework**: React with hooks, TanStack Query, Tailwind CSS

## Testing

### Backend
```bash
pytest                            # All tests
pytest tests/e2e/ -v             # E2E pipeline test
python tests/e2e/benchmark_runner.py --dataset smoke
python tests/e2e/load_test.py --concurrency 50
```

### Frontend
```bash
cd web
npm test                          # Vitest unit tests
npx playwright test               # E2E Playwright tests
npm run lint                       # ESLint
npm run typecheck                  # TypeScript
```

## Pull Request Process

1. Ensure all tests pass
2. Add tests for new functionality
3. Update documentation if needed
4. Keep PRs focused — one feature per PR
5. Use conventional commits: `feat:`, `fix:`, `chore:`, `docs:`, `test:`

## Commit Message Format

```
<type>(<scope>): <subject>

<body>
```

Types: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`, `perf`, `security`

Examples:
```
feat(search): add PubMed date range filter
fix(download): handle 403 from PMC resolver
docs: update deployment guide for Railway
```

## Project Structure

```
api/                    # FastAPI REST API
  routers/              # Endpoints
  schemas/              # Pydantic models
  jobs/                 # Background job queue
  auth/                 # Authentication (pluggable)
research_agent/         # LLM orchestration
search_service/         # Academic search
download_service/       # PDF/XML download
document_processing_service/ # PDF extraction
knowledge_base/         # Chunking, embedding, storage
web/                    # Next.js frontend
tests/                  # Backend tests
docs/                   # Documentation
```

## Getting Help

- Open a GitHub Discussion for questions
- Open a GitHub Issue for bugs
- Tag maintainers for urgent matters
