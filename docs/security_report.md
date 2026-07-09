# Security Audit Report

## Methodology

- Static analysis of source code (secrets, configs, headers)
- Dependency vulnerability scan (npm audit)
- Dockerfile security review
- Configuration audit (CORS, rate limiting, trusted hosts)

## Findings

### Dependency Vulnerabilities

| Severity | Package | Count | Fix Available |
|----------|---------|-------|---------------|
| Moderate | postcss (via next.js) | 2 | `npm audit fix --force` (breaking change) |

**Status:** ✅ Acceptable risk (transitive dep, no direct exploit path in this app)

### Secret Leakage Scan

| Type | Files Scanned | Matches | Verdict |
|------|--------------|---------|---------|
| API keys / passwords | 250+ | 0 direct matches | ✅ Clean |
| Private keys | 250+ | 0 matches | ✅ Clean |
| `change-me-in-production` | All | 1 (intentional default) | ✅ Blocked by `env_validator` |

### Security Headers

| Header | Backend | Frontend | Both |
|--------|---------|----------|------|
| `X-Content-Type-Options: nosniff` | ✅ | ✅ | ✅ |
| `X-Frame-Options: DENY` | ✅ | ✅ | ✅ |
| `Strict-Transport-Security` | ✅ | ✅ | ✅ |
| `X-XSS-Protection: 0` | ✅ | ✅ | ✅ |
| `Referrer-Policy` | ✅ | ✅ | ✅ |
| `Permissions-Policy` | ✅ | ✅ | ✅ |

### CORS Configuration

| Setting | Backend Default | Frontend Proxy |
|---------|----------------|----------------|
| `Access-Control-Allow-Origin` | `*` (configurable) | N/A (same-origin) |
| `Access-Control-Allow-Methods` | `*` (configurable) | N/A |

**Warning:** Backend defaults to `*` for CORS origins. Must be restricted in production via `API_CORS_ORIGINS`.

### Rate Limiting

| Layer | Type | Limit | Status |
|-------|------|-------|--------|
| Backend API | In-memory sliding window | 60 req/min/IP | ✅ Enabled by default |
| Search providers | Async token bucket | 3-10 req/s/provider | ✅ Per-provider config |

**Note:** In-memory rate limiter resets per worker process. Use Redis for multi-worker deployments.

### Docker Security

| Check | Backend Dockerfile | Frontend Dockerfile |
|-------|-------------------|---------------------|
| Non-root user | ✅ `USER app` | ✅ `USER app` |
| HEALTHCHECK | ✅ | ✅ |
| Multi-stage build | ✅ | ✅ |
| Slim base image | ✅ (python:3.12-slim) | ✅ (node:22-alpine) |
| Package manager cleanup | ✅ | ✅ |

### Startup Validation

| Check | Mechanism | Status |
|-------|-----------|--------|
| Secret key validation | `env_validator.py` → `sys.exit(1)` | ✅ |
| Debug mode warning | `env_validator.py` → WARNING | ✅ |
| CORS warning | `env_validator.py` → WARNING | ✅ |
| Trusted hosts check | `env_validator.py` + middleware | ✅ |
| Rate limit config | `env_validator.py` → validates integer | ✅ |

## Summary

| Category | Score | Critical Issues | High Issues |
|----------|-------|-----------------|-------------|
| Dependency security | 🟡 7/10 | 0 | 0 |
| Secret management | 🟢 9/10 | 0 | 0 |
| HTTP security headers | 🟢 10/10 | 0 | 0 |
| CORS | 🟡 7/10 | 0 | 0 (configurable) |
| Rate limiting | 🟢 8/10 | 0 | 0 |
| Docker security | 🟢 10/10 | 0 | 0 |
| Startup validation | 🟢 10/10 | 0 | 0 |
| **Overall** | **🟢 8.7/10** | **0** | **0** |
