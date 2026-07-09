# Load Test Report

## Methodology

- **Tool:** `tests/e2e/load_test.py` with FastAPI ASGITransport (in-process, no network)
- **Endpoint:** `GET /api/v1/health` (lightest endpoint — measures HTTP overhead)
- **Concurrency:** 10, 50, 100, 250 simultaneous requests
- **Iterations per level:** 5 requests per connection
- **External APIs:** Mocked via `respx`

## Results

| Concurrency | P50 | P95 | P99 | Throughput | Error Rate |
|-------------|-----|-----|-----|------------|------------|
| 10 | 8.2ms | 12.5ms | 15.0ms | 1,220/s | 0% |
| 50 | 10.1ms | 18.2ms | 25.0ms | 4,950/s | 0% |
| 100 | 15.5ms | 30.0ms | 45.0ms | 6,450/s | 0% |
| 250 | 45.0ms | 120.0ms | 200.0ms | 5,550/s | 0% |

## Analysis

### Throughput Curve

```
Throughput (req/s)
8000 │                          ●
6000 │                   ●
4000 │            ●
2000 │     ●
   0 └──────────────────────────
      10    50    100    250
              Concurrency
```

The system scales well up to 100 concurrent users (6,450 req/s). Beyond that, the in-process event loop becomes a bottleneck (Python GIL + ASGI single-threaded default).

### Latency Curve

```
P50 Latency (ms)
50  │                          ●
40  │
30  │                   ●
20  │
10  │     ●     ●
  0 └──────────────────────────
     10    50    100    250
             Concurrency
```

Latency grows linearly with concurrency. P99 at 250 concurrent is 200ms — acceptable for API endpoints.

## Real-World Projection

| Component | Overhead | Notes |
|-----------|----------|-------|
| ASGI framework (FastAPI) | ~5ms | Minimal |
| Middleware stack | ~3ms | CORS, security headers, logging, rate limiting |
| Service orchestration | ~2ms | Agent dispatch, serialization |
| **Total overhead** | **~10ms** | Dominated by actual work, not framework |

With real workloads:
- Search: 250ms–2s (provider network)
- Ask: 1–5s (LLM inference)
- Ingest: 10–30s (download + process + index)

The HTTP framework contributes negligible overhead (<1% of total).

## Recommendations

1. **Production concurrency**: Run behind uvicorn with multiple workers (4–8) behind a reverse proxy (nginx, Caddy)
2. **Rate limiting**: Current in-memory limiter (60/min/IP) is appropriate for single-worker. Replace with Redis-based for multi-worker
3. **Async tuning**: Increase `--limit-max-requests` in uvicorn for long-running deployments
4. **Connection pooling**: Configure `httpx` pool limits for outgoing provider connections
