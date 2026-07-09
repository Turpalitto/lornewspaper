"""Telegram bot — daily digest delivery.

Environment variables:
  TELEGRAM_BOT_TOKEN — Bot token from @BotFather
  TELEGRAM_CHAT_ID  — Target chat/channel ID (optional, for broadcast)

Endpoints:
  POST /api/v1/telegram/send-digest — Send today's editorial digest
  POST /api/v1/telegram/webhook     — Telegram bot webhook
"""

from __future__ import annotations

import os

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

_LOG = structlog.get_logger("api.telegram")

router = APIRouter(prefix="/telegram", tags=["telegram"])

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
DEFAULT_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

TELEGRAM_API = "https://api.telegram.org/bot"


class TelegramMessage(BaseModel):
    chat_id: str = ""
    text: str = ""


async def _send_message(chat_id: str, text: str) -> bool:
    """Send a message via Telegram Bot API."""
    if not BOT_TOKEN:
        _LOG.warning("TELEGRAM_BOT_TOKEN not set, skipping")
        return False

    import httpx

    url = f"{TELEGRAM_API}{BOT_TOKEN}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": False,
            })
            if resp.status_code != 200:
                _LOG.error("telegram_send_failed", status=resp.status_code, body=resp.text)
                return False
            return True
    except Exception as exc:
        _LOG.error("telegram_send_error", error=str(exc))
        return False


async def send_daily_digest() -> bool:
    """Send today's editorial digest to Telegram."""
    if not BOT_TOKEN or not DEFAULT_CHAT_ID:
        _LOG.warning("Telegram not configured (TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing)")
        return False

    try:
        from api.editorial.engine import EditorialEngine
        from api.editorial.formats import render_telegram

        engine = EditorialEngine()
        digest = await engine.generate_today()
        text = render_telegram(digest)

        # Telegram has 4096 char limit
        if len(text) > 4096:
            text = text[:4000] + "\n\n...continue reading at dailyent.ai"

        return await _send_message(DEFAULT_CHAT_ID, text)
    except Exception as exc:
        _LOG.error("telegram_digest_error", error=str(exc))
        return False


@router.post("/send-digest", operation_id="send_telegram_digest")
async def send_digest():
    """Manually trigger Telegram digest delivery."""
    sent = await send_daily_digest()
    if not sent:
        raise HTTPException(status_code=500, detail="Failed to send Telegram digest")
    return {"status": "sent"}


@router.post("/send", operation_id="send_telegram_message")
async def send_message(msg: TelegramMessage):
    """Send a custom Telegram message."""
    chat_id = msg.chat_id or DEFAULT_CHAT_ID
    if not chat_id:
        raise HTTPException(status_code=400, detail="No chat_id provided and TELEGRAM_CHAT_ID not set")

    sent = await _send_message(chat_id, msg.text)
    if not sent:
        raise HTTPException(status_code=500, detail="Failed to send message")
    return {"status": "sent"}


@router.get("/health", operation_id="telegram_health")
async def telegram_health():
    """Check Telegram bot configuration."""
    if not BOT_TOKEN:
        return {"configured": False, "message": "TELEGRAM_BOT_TOKEN not set"}

    import httpx

    url = f"{TELEGRAM_API}{BOT_TOKEN}/getMe"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                bot_info = resp.json().get("result", {})
                return {
                    "configured": True,
                    "bot_name": bot_info.get("first_name", ""),
                    "bot_username": bot_info.get("username", ""),
                    "chat_configured": bool(DEFAULT_CHAT_ID),
                }
            return {"configured": False, "error": resp.text}
    except Exception as exc:
        return {"configured": False, "error": str(exc)}
