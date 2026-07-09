"""Shared pytest fixtures."""

import asyncio

import pytest

from search_service.logging_config import configure_logging


@pytest.fixture(autouse=True)
def _configure_logging():
    configure_logging("ERROR")
    yield


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
