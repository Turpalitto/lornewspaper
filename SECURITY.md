# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | ✅ |
| < 1.0   | ❌ |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please
**do not** open a public issue.

Instead, send a private report to the project maintainers.

### How to Report

1. **GitHub Security Advisories**: Use the "Report a vulnerability" link under
   the repository's Security tab.
2. **Email**: Contact the maintainers directly (see MAINTAINERS.md).

### What to Include

- Type of vulnerability
- Steps to reproduce
- Affected versions
- Potential impact
- Suggested fix (if any)

### Response Timeline

- **24 hours**: Acknowledgment of receipt
- **7 days**: Initial assessment and severity classification
- **30 days**: Fix deployed for critical/high severity issues

## Security Measures

### In This Project

| Measure | Status |
|---------|--------|
| Security headers (HSTS, XFO, CSP) | ✅ All responses |
| Rate limiting | ✅ 60 req/min/IP |
| CORS configuration | ✅ Configurable |
| Startup secret validation | ✅ Exits on defaults |
| Non-root Docker containers | ✅ |
| Multi-stage builds | ✅ |
| HEALTHCHECK on all containers | ✅ |
| Structured logging | ✅ structlog JSON |
| Request ID tracking | ✅ All requests |

### For Production Deployments

1. **Always** set `SECRET_KEY` to a unique, random 64+ character string
2. **Restrict** `API_CORS_ORIGINS` to specific domains
3. **Restrict** `TRUSTED_HOSTS` to specific hostnames
4. **Disable** `API_DEBUG` in production
5. **Use** HTTPS/TLS in front of the application
6. **Enable** rate limiting
7. **Regularly** update dependencies
