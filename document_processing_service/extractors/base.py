"""Base extractor — strategy pattern.

Extractors accept different positional arguments depending on the extraction
type (text, fitz doc, etc.).  The signature is intentionally loose — each
subclass documents its own ``extract`` signature via type annotations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseExtractor(ABC):
    name: str

    @abstractmethod
    async def extract(self, doc: Any, **kwargs: Any) -> Any:
        ...