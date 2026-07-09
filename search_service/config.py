"""Configuration models for SearchService.

Declarative settings: global HTTP/timeout/concurrency defaults plus per-provider
rate-limit, timeout and capability flags. Providers register themselves in
``search_service.providers``; this module only holds configuration data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ProviderCapabilities:
    """Declares which operations a provider supports.

    Used by SearchService to skip providers that cannot fulfil a request
    instead of raising.
    """

    supports_search: bool = True
    supports_date: bool = True
    supports_pmid: bool = True
    supports_metadata: bool = True
    supports_abstract: bool = True
    supports_healthcheck: bool = True


@dataclass(slots=True)
class ProviderConfig:
    """Per-provider tunables."""

    name: str
    enabled: bool = True
    base_url: str = ""
    rate: float = 3.0          # requests per second (token bucket refill)
    burst: int = 5             # max tokens / instantaneous burst
    timeout: float = 10.0      # per-request timeout (seconds)
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Settings:
    """Top-level runtime configuration."""

    http_timeout: float = 10.0
    user_agent: str = "SearchService/0.1 (+https://example.org)"
    concurrency_limit: int = 5
    log_level: str = "INFO"
    providers: dict[str, ProviderConfig] = field(default_factory=dict)


def default_settings() -> Settings:
    """Build Settings with the three bundled providers enabled."""
    return Settings(
        providers={
            "pubmed": ProviderConfig(
                name="pubmed",
                base_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
                rate=3.0,
                burst=5,
                timeout=10.0,
            ),
            "europepmc": ProviderConfig(
                name="europepmc",
                base_url="https://www.ebi.ac.uk/europepmc/webservices/rest",
                rate=5.0,
                burst=10,
                timeout=10.0,
            ),
            "openalex": ProviderConfig(
                name="openalex",
                base_url="https://api.openalex.org",
                rate=10.0,
                burst=10,
                timeout=10.0,
                extra={"mailto": "search@example.org"},
            ),
        }
    )
