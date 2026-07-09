# v2.0 Roadmap

## From v1.0 to v2.0

### v1.0 (Current)
Core research platform: search, download, process, index, ask.

### v1.1 (Q3 2026) — Production Hardening

| Feature | Impact | Effort | Priority |
|---------|--------|--------|----------|
| Redis-based rate limiting | Multi-worker enforcement | 1d | 🔴 Critical |
| WebSocket streaming for LLM | Real-time answer display | 2d | 🔴 High |
| Frontend healthcheck endpoint | Container independence | 30m | 🔴 High |
| Sentry error tracking | Real-time monitoring | 4h | 🔴 High |
| API key authentication | Access control | 2d | 🟡 Medium |
| Search filters (date, provider) | UX improvement | 1d | 🟡 Medium |
| Export results (BibTeX) | Researcher workflow | 1d | 🟡 Medium |

### v1.2 (Q4 2026) — Scale & Collaboration

| Feature | Impact | Effort | Priority |
|---------|--------|--------|----------|
| Multi-user with teams | Collaboration | 1w | 🔴 High |
| Shared knowledge bases | Team research | 3d | 🔴 High |
| PDF viewer in browser | Document preview | 3d | 🟡 Medium |
| Webhook notifications | Pipeline events | 2d | 🟡 Medium |
| Admin dashboard | Usage analytics | 3d | 🟡 Medium |
| Helm chart for K8s | Enterprise deploy | 2d | 🟡 Medium |
| Alembic migrations | Schema management | 1d | 🟡 Medium |

### v2.0 (Q1 2027) — Advanced Intelligence

| Feature | Impact | Effort | Priority |
|---------|--------|--------|----------|
| Multi-document synthesis | Compare across papers | 2w | 🔴 High |
| Citation graph analysis | Network visualization | 1w | 🔴 High |
| Literature review automation | Auto-generated reviews | 3w | 🔴 High |
| Custom embedding fine-tuning | Domain adaptation | 2w | 🟡 Medium |
| Multi-modal (figures, tables) | Richer understanding | 3w | 🟡 Medium |
| Collaborative editing | Research synthesis | 2w | 🟡 Medium |
| Plugin system | Custom extractors | 3w | 🟢 Low |

## Technical Debt to Address

| Debt | Area | Impact | Effort |
|------|------|--------|--------|
| Python lockfile | DevX | Non-deterministic builds | 1d |
| No DB migrations | Ops | Schema changes risky | 1d |
| Single agent mutex | Scale | 409 on concurrent requests | 2d |
| In-memory rate limiter | Scale | Per-worker counting | 1d |
| Minimal test PDFs | Quality | Poor real-world coverage | 2d |
| No staging env | Ops | No pre-prod validation | 1d |

## Migration Path

### v1.0 → v1.1
- Backward compatible
- New env vars have defaults
- API unchanged
- Database schema unchanged

### v1.1 → v1.2
- Auth layer activated (opt-in)
- New endpoints for teams/sharing
- Database migrations for user model
- Webhook registration API added

### v1.2 → v2.0
- Possible breaking: embedding model upgrade
- New endpoints for synthesis/citation
- Plugin API introduced
- Database migration for graph model
