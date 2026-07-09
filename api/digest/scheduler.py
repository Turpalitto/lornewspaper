"""Daily Digest scheduler.

Uses the existing LORNEWS job queue to schedule daily digest generation.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, time, timedelta, timezone

import structlog

from api.digest.generator import DigestGenerator

_LOG = structlog.get_logger("api.digest.scheduler")


class DigestScheduler:
    """Schedules daily, weekly, and monthly digest generation."""

    def __init__(self, generator: DigestGenerator):
        self._generator = generator
        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        """Start the scheduler loop."""
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        _LOG.info("digest_scheduler_started")

    async def stop(self) -> None:
        """Stop the scheduler loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        _LOG.info("digest_scheduler_stopped")

    async def generate_now(self) -> str:
        """Generate a digest immediately. Returns digest ID."""
        digest = await self._generator.generate_daily()
        return digest.id

    async def _run_loop(self) -> None:
        """Main scheduler loop — runs daily at configurable time."""
        while self._running:
            try:
                now = datetime.now(timezone.utc)
                # Run at 06:00 UTC daily
                target = now.replace(hour=6, minute=0, second=0, microsecond=0)
                if now >= target:
                    target += timedelta(days=1)

                wait_seconds = (target - now).total_seconds()
                _LOG.debug("next_digest_scheduled", at=target.isoformat(), wait_seconds=wait_seconds)

                await asyncio.sleep(wait_seconds)
                if not self._running:
                    break

                _LOG.info("generating_daily_digest")
                digest = await self._generator.generate_daily()
                _LOG.info("daily_digest_complete", digest_id=digest.id, papers=digest.total_papers)

            except asyncio.CancelledError:
                break
            except Exception as exc:
                _LOG.error("digest_generation_failed", error=str(exc))
                await asyncio.sleep(300)  # Retry in 5 minutes


async def start_scheduler(generator: DigestGenerator) -> DigestScheduler:
    """Create and start the digest scheduler."""
    scheduler = DigestScheduler(generator)
    await scheduler.start()
    return scheduler
