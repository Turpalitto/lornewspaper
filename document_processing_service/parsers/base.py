"""Parser ABC — thin strategy wrapper."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseParser(ABC):
    name: str

    @abstractmethod
    async def parse(self, doc: Any, **kwargs: Any) -> Any:
        ...