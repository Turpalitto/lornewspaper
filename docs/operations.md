# Operations Guide

## Health Endpoints

| Endpoint | Purpose | Expected Response |
|----------|---------|-------------------|
| `GET /api/v1/health` | Overall system health | `{"status": "ok", "version": "0.1.0", "uptime_seconds": N}` |
| `GET /api/v1/liveness` | Container liveness probe | `{"status": "alive"}` |
| `GET /api/v1/readiness` | Dependency readiness | `{"status": "ok", "agent_ready": true, "knowledge_base_ready": true, "cache_ready": true}` |

## Metrics

**Endpoint:** `GET /metrics`

**Format:** Prometheus text format

**Metrics exposed:**
- `lornews_uptime_seconds` — application uptime (gauge)
- `lornews_requests_total` — total HTTP requests (counter)
- `lornews_request_duration_seconds` — average request duration (gauge)

## Logging

**Format:** Structured JSON via `structlog`

**Log fields:**
- `event` — event name (`request_start`, `request_end`, `request_error`)
- `method` — HTTP method
- `path` — URL path
- `status_code` — HTTP status
- `request_id` — unique request identifier (UUID)
- `duration_seconds` — request duration
- `error` — error message (on errors)

**Log levels:**
- `DEBUG` — verbose (only in dev)
- `INFO` — request start/end, startup/shutdown
- `WARNING` — validation issues, configuration warnings
- `ERROR` — request failures, startup failures

### Viewing logs
```bash
# Docker
docker compose logs -f backend

# Structured JSON
docker compose logs -f backend | jq
```

## Monitoring

### Prometheus integration
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'lornews'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['backend:8000']
```

### Grafana dashboard
Import metrics into Grafana:
- Uptime: `lornews_uptime_seconds`
- Request rate: `rate(lornews_requests_total[5m])`
- Avg latency: `lornews_request_duration_seconds`

## Scaling

### Horizontal scaling (backend)
```bash
# Increase instances
docker compose up -d --scale backend=3
```

Note: In-memory rate limiter resets per instance. Use Redis-based rate limiting for multi-instance deploys.

### Resource limits (Docker Compose)
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

## Backup & Recovery

### Data volumes
```yaml
volumes:
  postgres_data:     # PostgreSQL database
  redis_data:        # Redis cache
  qdrant_data:       # Qdrant vector store
  app_data:          # Application data (downloads, vector store, SQLite)
  ollama_data:       # Ollama models (if used)
```

### Backup commands
```bash
# PostgreSQL
docker compose exec postgres pg_dump -U lornews lornews > backup_$(date +%Y%m%d).sql

# Application data
docker compose exec backend tar czf /tmp/app_data_backup.tar.gz /app/data
docker cp $(docker compose ps -q backend):/tmp/app_data_backup.tar.gz .
```

## Troubleshooting

### Backend won't start
1. Check logs: `docker compose logs backend`
2. Verify all dependencies are healthy: `docker compose ps`
3. Validate environment: `docker compose run backend python -c "from api.env_validator import validate_env; print(validate_env())"`

### Health check fails
```bash
# Direct check
curl -v http://localhost:8000/api/v1/health

# From inside container
docker compose exec backend python -c "import http.client; c=http.client.HTTPConnection('localhost:8000'); c.request('GET','/api/v1/health'); r=c.getresponse(); print(r.status, r.read())"
```

### Rate limiting too strict
Adjust `RATE_LIMIT_PER_MINUTE` env var (default: 60).

For multi-instance deployments, implement Redis-based rate limiting by replacing the `InMemoryRateLimiter` in `api/security.py`.
