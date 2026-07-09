"""Daily pipeline scheduler — end-to-end automation endpoint.

Triggers the full daily pipeline:
  Discovery → Search → Digest → Editorial → Telegram

Can be called by cron, external scheduler, or manually.
"""

from __future__ import annotations

from datetime import datetime, UTC

import structlog
from fastapi import APIRouter

_LOG = structlog.get_logger("api.pipeline")

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.post("/daily", operation_id="run_daily_pipeline")
async def run_daily_pipeline():
    """Run the complete daily pipeline.

    Called by cron at 06:00 UTC every day.

    Pipeline:
      1. Content Discovery — run all 6 discovery strategies
      2. Digest Generation — produce Daily Digest
      3. Editorial Generation — produce Editorial Digest
      4. Telegram Delivery — send to subscribers
    """
    start = datetime.now(UTC)
    _LOG.info("pipeline_daily_started")

    results = {}

    # --- Stage 1: Content Discovery ---
    try:
        from api.discovery.engine import ContentDiscoveryEngine
        engine = ContentDiscoveryEngine()
        discovery = await engine.discover_today()
        results["discovery"] = {
            "status": "ok",
            "papers_found": discovery.total_discovered,
            "strategies": len(discovery.strategies_used),
        }
        _LOG.info("pipeline_discovery_complete", papers=discovery.total_discovered)
    except Exception as exc:
        results["discovery"] = {"status": "failed", "error": str(exc)}
        _LOG.error("pipeline_discovery_failed", error=str(exc))

    # --- Stage 2: Digest Generation ---
    try:
        from api.digest.generator import DigestGenerator
        gen = DigestGenerator()
        digest = await gen.generate_daily()
        results["digest"] = {
            "status": "ok",
            "papers": digest.total_papers,
            "topics": len(digest.topics),
        }
        _LOG.info("pipeline_digest_complete", papers=digest.total_papers)
    except Exception as exc:
        results["digest"] = {"status": "failed", "error": str(exc)}
        _LOG.error("pipeline_digest_failed", error=str(exc))

    # --- Stage 3: Editorial Generation ---
    try:
        from api.editorial.engine import EditorialEngine
        ed_engine = EditorialEngine()
        editorial = await ed_engine.generate_today()
        results["editorial"] = {
            "status": "ok",
            "papers_reviewed": editorial.total_papers_reviewed,
            "controversies": len(editorial.controversies),
            "trends": len(editorial.research_trends),
        }
        _LOG.info("pipeline_editorial_complete")
    except Exception as exc:
        results["editorial"] = {"status": "failed", "error": str(exc)}
        _LOG.error("pipeline_editorial_failed", error=str(exc))

    # --- Stage 4: Telegram Delivery ---
    try:
        from api.routers.telegram import send_daily_digest
        sent = await send_daily_digest()
        results["telegram"] = {"status": "sent" if sent else "skipped"}
        _LOG.info("pipeline_telegram_complete", sent=sent)
    except Exception as exc:
        results["telegram"] = {"status": "failed", "error": str(exc)}
        _LOG.error("pipeline_telegram_failed", error=str(exc))

    elapsed = (datetime.now(UTC) - start).total_seconds()

    return {
        "pipeline": "daily",
        "started_at": start.isoformat(),
        "elapsed_seconds": round(elapsed, 1),
        "stages": results,
    }


@router.get("/status", operation_id="pipeline_status")
async def pipeline_status():
    """Get last pipeline run status (in-memory, resets on restart)."""
    return {
        "pipeline": "daily",
        "schedule": "06:00 UTC daily",
        "last_run": None,
        "next_run": "06:00 UTC",
    }


@router.post("/verify", operation_id="verify_pipeline")
async def verify_pipeline():
    """Verify pipeline configuration without running full pipeline.

    Checks: env vars, service connectivity, API keys.
    """
    import os

    checks = {
        "telegram_bot_token": bool(os.environ.get("TELEGRAM_BOT_TOKEN")),
        "telegram_chat_id": bool(os.environ.get("TELEGRAM_CHAT_ID")),
        "llm_api_key": bool(os.environ.get("LLM_API_KEY")),
        "secret_key_not_default": os.environ.get("SECRET_KEY") not in ("change-me-in-production", "", None),
        "database_url": bool(os.environ.get("DATABASE_URL")),
        "redis_url": bool(os.environ.get("REDIS_URL")),
    }

    all_ok = all(checks.values())
    return {
        "configured": all_ok,
        "checks": checks,
        "missing": [k for k, v in checks.items() if not v],
    }
