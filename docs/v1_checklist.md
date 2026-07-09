# v1.0 Release Checklist

## Pre-Release

### Code Quality
- [x] All Python tests pass (`pytest`)
- [x] Ruff lint passes (`ruff check .`)
- [x] MyPy type checks pass (`mypy . --ignore-missing-imports`)
- [x] TypeScript compiles (`tsc --noEmit`)
- [x] Vitest tests pass (`npm test`)
- [x] ESLint passes (`npx eslint .`)
- [x] Next.js builds successfully (`npm run build`)
- [x] Playwright e2e tests pass (`npx playwright test`)

### Performance
- [x] No event loop blocking — all CPU-bound work in thread pool
- [x] Concurrent provider requests with semaphore bounding
- [x] Rate limiting enabled (60 req/min/IP)
- [x] Response compression enabled (GZipMiddleware)
- [x] Static asset compression enabled (Next.js compress)

### Security
- [x] Security headers on all responses (HSTS, XFO, CSP, etc.)
- [x] CORS restricted (configurable, default `*` flagged)
- [x] Rate limiting enabled by default
- [x] Secret validation exits on default values
- [x] Non-root user in Docker containers
- [x] HEALTHCHECK on all containers
- [x] Multi-stage Docker builds

### Infrastructure
- [x] Docker image builds (backend + frontend)
- [x] Docker Compose orchestration (6 services)
- [x] Health endpoints (`/health`, `/liveness`, `/readiness`)
- [x] Metrics endpoint (`/metrics` — Prometheus format)
- [x] Structured logging (structlog JSON)
- [x] Request IDs on all responses

### Deployment
- [x] GitHub Actions CI (9 job types)
- [x] GitHub Actions CD (release workflow)
- [x] Docker image publish to GHCR
- [x] Semantic version tagging
- [x] Deployment guides for 6 platforms

## Release Process

### 1. Version Bump
```bash
# Update version in:
#   pyproject.toml
#   research_agent/__init__.py
#   api/app.py (APISettings.version)
#   web/package.json
git commit -m "chore: bump version to v1.0.0"
git tag v1.0.0
git push origin main --tags
```

### 2. CI/CD Trigger
The release workflow will:
1. Run full test suite
2. Build Docker images (backend + frontend)
3. Publish to `ghcr.io/<repo>/lornews-{backend,frontend}:v1.0.0`
4. Create GitHub Release with auto-generated notes

### 3. Post-Release
- [ ] Verify Docker images at `ghcr.io/<repo>/lornews-backend:v1.0.0`
- [ ] Deploy to staging environment
- [ ] Run smoke tests against staging
- [ ] Verify health endpoints
- [ ] Verify metrics endpoint
- [ ] Verify frontend loads
- [ ] Deploy to production
- [ ] Monitor logs for first 24 hours

### 4. Rollback
```bash
# Rollback Docker deployment
docker pull ghcr.io/<repo>/lornews-backend:<previous-version>
docker compose up -d backend

# Rollback GitHub Release
gh release delete v1.0.0
git tag -d v1.0.0
git push origin :refs/tags/v1.0.0
```
