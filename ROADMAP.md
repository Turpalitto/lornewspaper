# Roadmap

## v1.0 — Current (July 2026)

**Focus:** Core platform, production readiness

- [x] Academic search (PubMed, EuropePMC, OpenAlex)
- [x] PDF download and processing
- [x] Knowledge base with RAG
- [x] FastAPI REST API (15 endpoints)
- [x] Next.js frontend (7 pages)
- [x] Background job queue
- [x] Docker + Compose deployment
- [x] CI/CD pipeline
- [x] Security hardening
- [x] Performance optimization
- [x] 288+ tests
- [x] Documentation

## v1.1 — Next (Q3 2026)

**Focus:** Production hardening, UX polish

- [ ] WebSocket streaming for LLM responses
- [ ] Redis-based rate limiting (multi-worker)
- [ ] API key authentication
- [ ] Better mobile navigation (hamburger menu)
- [ ] Search filters (date range, provider, journal)
- [ ] Batch ingest from DOI list
- [ ] Export results (BibTeX, RIS, CSV)
- [ ] Accessibility audit (axe-core)
- [ ] Sentry error tracking
- [ ] Performance regression CI gate

## v1.2 — (Q4 2026)

**Focus:** Scale, collaboration, ecosystem

- [ ] Multi-user support with teams
- [ ] Shared knowledge bases
- [ ] Document annotation and highlighting
- [ ] PDF viewer in browser
- [ ] Webhook notifications for ingest completion
- [ ] Admin dashboard with usage analytics
- [ ] Helm chart for Kubernetes
- [ ] PostgreSQL migrations (Alembic)
- [ ] OpenAPI spec sync in CI

## v2.0 — (Q1 2027)

**Focus:** Advanced intelligence, domain specialization

- [ ] Multi-document synthesis (compare across papers)
- [ ] Citation graph and network analysis
- [ ] Literature review automation
- [ ] Custom embedding fine-tuning
- [ ] Multi-modal support (figures, tables, equations)
- [ ] Collaborative editing of research synthesis
- [ ] Plugin system for custom extractors
- [ ] API versioning strategy
- [ ] Multi-region deployment

## Future Directions

See [docs/future_products.md](docs/future_products.md) for product concepts built on LORNEWS:
- Medical Research Assistant
- Clinical Guideline Assistant
- ENT Assistant
- Evidence Platform
- Scientific Literature Copilot
