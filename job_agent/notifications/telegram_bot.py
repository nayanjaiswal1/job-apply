from __future__ import annotations

import os
from typing import Any

import structlog

from job_agent.ports.notifier import NotifierPort

log = structlog.get_logger()


class TelegramBot:
    """NotifierPort: sends plain text Telegram alerts."""

    def __init__(self) -> None:
        self._token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self._chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        self._enabled = bool(self._token and self._chat_id)

    async def send_alert(self, event: str, payload: dict[str, Any]) -> None:
        if not self._enabled:
            log.info("telegram_disabled", event=event)
            return
        msg = f"[{event}] {self._format(payload)}"
        await self._send(msg)

    async def send_digest(self, subject: str, body_html: str, body_text: str) -> None:
        if not self._enabled:
            return
        await self._send(f"DIGEST: {subject}\n\n{body_text[:500]}")

    async def _send(self, text: str) -> None:
        import httpx
        url = f"https://api.telegram.org/bot{self._token}/sendMessage"
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json={"chat_id": self._chat_id, "text": text[:4096]}, timeout=10)
            if not resp.is_success:
                log.warning("telegram_send_fail", status=resp.status_code)

    def _format(self, payload: dict[str, Any]) -> str:
        return " | ".join(f"{k}={v}" for k, v in list(payload.items())[:4])


def _check() -> None:
    _: NotifierPort = TelegramBot.__new__(TelegramBot)  # type: ignore[type-abstract]


_check()
