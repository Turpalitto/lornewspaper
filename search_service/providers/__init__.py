"""Provider registry.

Adding a new source requires only: (1) a new module in this package
implementing :class:`~search_service.base.BaseProvider`, and (2) an entry in
``PROVIDER_CLASSES`` below. ``SearchService`` discovers providers through
``get_provider`` and never imports concrete classes directly (DIP).
"""

from __future__ import annotations

import importlib
from typing import Any

from search_service.base import BaseProvider
from search_service.config import ProviderConfig

# name -> (module, class). New providers register here only.
PROVIDER_CLASSES: dict[str, tuple[str, str]] = {
    "pubmed": ("search_service.providers.pubmed", "PubMedProvider"),
    "europepmc": ("search_service.providers.europepmc", "EuropePMCProvider"),
    "openalex": ("search_service.providers.openalex", "OpenAlexProvider"),
}


def get_provider_class(name: str) -> type[BaseProvider]:
    if name not in PROVIDER_CLASSES:
        raise KeyError(f"Unknown provider: {name}")
    module_path, class_name = PROVIDER_CLASSES[name]
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def get_provider(
    name: str,
    config: ProviderConfig,
    client: Any = None,
    **kwargs: Any,
) -> BaseProvider:
    cls = get_provider_class(name)
    return cls(config, client, **kwargs)


def available_providers() -> list[str]:
    return list(PROVIDER_CLASSES)
