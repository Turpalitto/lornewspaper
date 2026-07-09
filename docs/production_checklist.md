# Production Readiness Checklist

## Pre-Deployment

### Security
- [ ] `SECRET_KEY` is set to a unique, random 64+ character string
- [ ] `LLM_API_KEY` (or equivalent) is set for all cloud LLM providers
- [ ] `API_CORS_ORIGINS` restricted to specific domains (not `*`)
- [ ] `TRUSTED_HOSTS` restricted to specific hostnames (not `*`)
- [ ] `API_DEBUG` is `false`
- [ ] Database passwords are unique and strong
- [ ] Redis is configured with `REDIS_PASSWORD` if exposed
- [ ] Rate limiting is enabled (`ENABLE_RATE_LIMIT=true`)
- [ ] Security headers are confirmed via `curl -I <url>`

### Infrastructure
- [ ] PostgreSQL is configured with persistent volume
- [ ] Redis is configured with persistent volume
- [ ] Qdrant is configured with persistent volume
- [ ] Application data volume is backed up
- [ ] Object storage (S3/MinIO) configured for downloads (optional)
- [ ] SSL/TLS certificates provisioned (via platform or Let's Encrypt)
- [ ] Domain DNS records configured

### Performance
- [ ] Compression enabled (`ENABLE_COMPRESSION=true`)
- [ ] Static assets cached via CDN or platform edge
- [ ] Database connection pool sized appropriately (`CONNECTION_POOL_MIN`/`MAX`)
- [ ] LLM provider rate limits reviewed
- [ ] Search service rate limits tuned per provider

### Monitoring
- [ ] Prometheus scraping `/metrics` endpoint
- [ ] Grafana dashboard created with key metrics
- [ ] Uptime monitoring configured (e.g., UptimeRobot, Better Uptime)
- [ ] Error alerting configured (e.g., Sentry integration pending)
- [ ] Log aggregation configured (e.g., Grafana Loki, Axiom)

### CI/CD
- [ ] GitHub Actions CI passing on `main` branch
- [ ] Docker images build without warnings
- [ ] All tests passing (backend + frontend)
- [ ] Lint checks passing (ruff + eslint)
- [ ] Type checks passing (mypy + tsc)

### Documentation
- [ ] Deployment guide reviewed (`docs/deployment.md`)
- [ ] Operations guide reviewed (`docs/operations.md`)
- [ ] Environment variables documented in `.env.example`
- [ ] Runbook created for common incidents

## Post-Deployment

- [ ] Health check endpoints respond correctly
- [ ] Metrics endpoint returns Prometheus-formatted data
- [ ] Frontend loads without errors
- [ ] API search works end-to-end
- [ ] API ingest works end-to-end
- [ ] API ask (RAG) works end-to-end
- [ ] Dark/light theme toggle works
- [ ] All pages load without horizontal scroll on mobile
- [ ] Rate limiting returns 429 after threshold exceeded
- [ ] Security headers present on all responses

## Continuous
- [ ] Dependency updates automated (Dependabot/Renovate)
- [ ] Docker image vulnerability scanning enabled
- [ ] Backup strategy documented and tested
- [ ] Disaster recovery plan documented
- [ ] Load testing performed before major releases
