"""Async SHA256 streaming checksum computation.

Uses hashlib in a thread pool executor to avoid blocking the event loop, since
hashlib operations are CPU-bound. For typical file sizes (<50 MB) the overhead
is negligible.
"""

from __future__ import annotations

import asyncio
import hashlib
from collections.abc import AsyncIterator


async def sha256_stream(stream: AsyncIterator[bytes]) -> tuple[str, int]:
    """Read from ``stream``, compute SHA256 digest, return (hex_digest, total_bytes)."""
    sha = hashlib.sha256()
    loop = asyncio.get_running_loop()
    total = 0
    async for chunk in stream:
        total += len(chunk)
        await loop.run_in_executor(None, sha.update, chunk)
    return sha.hexdigest(), total


def verify_sha256(file_path: str, expected_hex: str) -> tuple[bool, str]:
    """Verify the file at ``file_path`` matches ``expected_hex``.

    Returns (is_match, computed_hex). This is synchronous (reading file).
    """
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            sha.update(chunk)
    computed = sha.hexdigest()
    return computed == expected_hex, computed