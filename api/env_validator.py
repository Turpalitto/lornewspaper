"""Environment variable validation at startup."""

from __future__ import annotations

import os
import sys


REQUIRED_VARS: list[str] = []

OPTIONAL_VARS: dict[str, str] = {
    "SECRET_KEY": "change-me-in-production",
    "LLM_API_KEY": "",
    "DATABASE_URL": "postgresql+asyncpg://lornews:lornews@postgres:5432/lornews",
    "REDIS_URL": "redis://redis:6379/0",
    "QDRANT_URL": "http://qdrant:6333",
}

SECRET_VARS: list[str] = [
    "SECRET_KEY",
    "LLM_API_KEY",
    "DATABASE_URL",
    "REDIS_URL",
    "POSTGRES_PASSWORD",
]


def validate_env() -> list[str]:
    """Validate environment configuration. Returns list of warnings/issues.

    Calls sys.exit(1) for security-critical misconfigurations.
    """
    issues: list[str] = []

    for var in REQUIRED_VARS:
        if not os.environ.get(var):
            issues.append(f"Missing required env var: {var}")
            sys.exit(1)

    for var, default in OPTIONAL_VARS.items():
        val = os.environ.get(var, default)
        if var in SECRET_VARS and val in ("", "change-me-in-production", "secret"):
            issues.append(
                f"FATAL: {var} is set to default/empty value. "
                "This is INSECURE for production. Set a unique value."
            )
            sys.exit(1)

    api_debug = os.environ.get("API_DEBUG", "false").lower()
    if api_debug in ("1", "true"):
        issues.append("WARNING: API_DEBUG=true should not be used in production")

    api_cors = os.environ.get("API_CORS_ORIGINS", "*")
    if api_cors == "*" and api_debug not in ("1", "true"):
        issues.append(
            "WARNING: API_CORS_ORIGINS=* is permissive. Restrict to specific origins in production."
        )

    trusted_hosts = os.environ.get("TRUSTED_HOSTS", "*")
    if trusted_hosts == "*" and api_debug not in ("1", "true"):
        issues.append(
            "WARNING: TRUSTED_HOSTS=* is permissive. Set specific hostnames in production."
        )

    llm_provider = os.environ.get("LLM_PROVIDER", "ollama")
    valid_providers = {"openai", "anthropic", "google", "ollama"}
    if llm_provider not in valid_providers:
        issues.append(
            f"WARNING: Unknown LLM_PROVIDER={llm_provider}. "
            f"Valid: {', '.join(sorted(valid_providers))}"
        )

    if llm_provider in ("openai", "anthropic") and not os.environ.get("LLM_API_KEY"):
        issues.append(
            f"WARNING: LLM_PROVIDER={llm_provider} requires LLM_API_KEY to be set"
        )

    try:
        rate_limit = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "60"))
        if rate_limit < 1:
            issues.append("WARNING: RATE_LIMIT_PER_MINUTE must be >= 1")
    except ValueError:
        issues.append("WARNING: RATE_LIMIT_PER_MINUTE must be an integer")

    return issues
