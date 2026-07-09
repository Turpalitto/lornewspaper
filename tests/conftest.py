"""Shared pytest fixtures."""

import pytest

from search_service.logging_config import configure_logging


@pytest.fixture(autouse=True)
def _configure_logging():
    configure_logging("ERROR")
    yield
