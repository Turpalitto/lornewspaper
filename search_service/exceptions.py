"""Public exception hierarchy for SearchService.

Keeping a single base type lets callers catch all library errors with one
``except``, while still allowing fine-grained handling.
"""

from __future__ import annotations


class SearchServiceError(Exception):
    """Base class for all SearchService errors."""


class UnknownProviderError(SearchServiceError, ValueError):
    """Raised when a requested provider name is not registered/enabled."""
