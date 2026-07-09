"""Extensible async literature search service.

Sources are pluggable providers (PubMed, Europe PMC, OpenAlex) behind a
unified interface. Cross-cutting concerns (HTTP pool, rate limiting, retry,
structured logging) are shared so adding a provider needs only a new class.
"""

from search_service.base import BaseProvider
from search_service.models import Article
from search_service.service import SearchService

__all__ = ["SearchService", "Article", "BaseProvider"]
__version__ = "0.1.0"
