"""ResearchAgent exception hierarchy."""

from __future__ import annotations


class ResearchAgentError(Exception):
    """Base exception for all ResearchAgent errors."""


class LLMProviderError(ResearchAgentError, RuntimeError):
    """Raised when an LLM provider fails to respond."""


class UnknownProviderError(ResearchAgentError, ValueError):
    """Raised when an unknown LLM provider is requested."""


class WorkflowError(ResearchAgentError, RuntimeError):
    """Raised when a workflow step fails."""


class CacheError(ResearchAgentError, RuntimeError):
    """Raised on cache operation failure."""


class ConfigurationError(ResearchAgentError, ValueError):
    """Raised on invalid configuration."""


class AgentBusyError(ResearchAgentError, RuntimeError):
    """Raised when agent is already running."""


class DocumentNotFoundError(ResearchAgentError, KeyError):
    """Raised when a document is not found in the knowledge base."""
