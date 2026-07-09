from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class APISettings:
    app_name: str = "Research Agent API"
    version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    debug: bool = False
    cors_origins: list[str] = field(default_factory=lambda: ["*"])
    cors_methods: list[str] = field(default_factory=lambda: ["*"])
    cors_headers: list[str] = field(default_factory=lambda: ["*"])
    log_level: str = "INFO"
    request_id_header: str = "X-Request-ID"
    secret_key: str = "change-me-in-production"
    trusted_hosts: list[str] = field(default_factory=lambda: ["*"])
    enable_metrics: bool = True
    enable_rate_limit: bool = True
    enable_compression: bool = True
    rate_limit_per_minute: int = 60
    redis_url: str = "redis://redis:6379/0"
    database_url: str = ""
    qdrant_url: str = "http://qdrant:6333"
    connection_pool_min: int = 2
    connection_pool_max: int = 10

    @classmethod
    def from_env(cls) -> APISettings:
        import os
        return cls(
            debug=os.environ.get("API_DEBUG", "").lower() in ("1", "true"),
            cors_origins=os.environ.get("API_CORS_ORIGINS", "*").split(","),
            cors_methods=os.environ.get("API_CORS_METHODS", "*").split(","),
            cors_headers=os.environ.get("API_CORS_HEADERS", "*").split(","),
            log_level=os.environ.get("API_LOG_LEVEL", "INFO"),
            secret_key=os.environ.get("SECRET_KEY", "change-me-in-production"),
            trusted_hosts=os.environ.get("TRUSTED_HOSTS", "*").split(","),
            enable_metrics=os.environ.get("ENABLE_METRICS", "true").lower() in ("1", "true"),
            enable_rate_limit=os.environ.get("ENABLE_RATE_LIMIT", "true").lower() in ("1", "true"),
            enable_compression=os.environ.get("ENABLE_COMPRESSION", "true").lower() in ("1", "true"),
            rate_limit_per_minute=int(os.environ.get("RATE_LIMIT_PER_MINUTE", "60")),
            redis_url=os.environ.get("REDIS_URL", "redis://redis:6379/0"),
            database_url=os.environ.get("DATABASE_URL", ""),
            qdrant_url=os.environ.get("QDRANT_URL", "http://qdrant:6333"),
            connection_pool_min=int(os.environ.get("CONNECTION_POOL_MIN", "2")),
            connection_pool_max=int(os.environ.get("CONNECTION_POOL_MAX", "10")),
        )
