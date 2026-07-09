"""Extensible async literature search service.

Sources are pluggable providers (PubMed, Europe PMC, OpenAlex) behind a
unified interface. Cross-cutting concerns (HTTP pool, rate limiting, retry,
structured logging) are shared so adding a provider needs only a new class.
"""

__version__ = "0.1.0"
