"""Async utilities: run blocking code in thread pool executor."""

from __future__ import annotations

import asyncio
from typing import Any, Callable, TypeVar

T = TypeVar("T")


async def to_thread(fn: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Run a synchronous function in a thread pool executor.

    Wraps asyncio.to_thread() with a fallback for Python < 3.9.
    Use this for ALL CPU-bound or blocking I/O operations.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: fn(*args, **kwargs))
