from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import httpx
import structlog

from job_agent.errors import PermanentError, TransientError

log = structlog.get_logger()

_TOKEN_PATH = Path("sessions/linkedin_token.json")
_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
_API_BASE = "https://api.linkedin.com/v2"


class LinkedInClient:
    """LinkedIn OAuth2 PKCE client: job search, DM, connections."""

    def __init__(self) -> None:
        self._client_id = os.environ.get("LINKEDIN_CLIENT_ID", "")
        self._client_secret = os.environ.get("LINKEDIN_CLIENT_SECRET", "")
        self._redirect_uri = os.environ.get("LINKEDIN_REDIRECT_URI", "http://localhost:8000/auth/linkedin/callback")
        self._token: dict[str, Any] = self._load_token()

    # ── Token management ──────────────────────────────────────────────────────

    def _load_token(self) -> dict[str, Any]:
        if _TOKEN_PATH.exists():
            try:
                return dict(json.loads(_TOKEN_PATH.read_text()))
            except Exception:
                pass
        return {}

    def _save_token(self, token: dict[str, Any]) -> None:
        _TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        _TOKEN_PATH.write_text(json.dumps(token))

    def _is_expired(self) -> bool:
        expires_at = self._token.get("expires_at", 0)
        return time.time() >= float(expires_at) - 60

    async def _refresh(self) -> None:
        refresh_token = self._token.get("refresh_token")
        if not refresh_token:
            raise PermanentError("No LinkedIn refresh token — re-authenticate")
        async with httpx.AsyncClient() as client:
            resp = await client.post(_TOKEN_URL, data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            })
            resp.raise_for_status()
            token = resp.json()
            token["expires_at"] = time.time() + token.get("expires_in", 3600)
            self._token = token
            self._save_token(token)

    async def _headers(self) -> dict[str, str]:
        if self._is_expired():
            await self._refresh()
        return {
            "Authorization": f"Bearer {self._token['access_token']}",
            "X-Restli-Protocol-Version": "2.0.0",
        }

    # ── API methods ───────────────────────────────────────────────────────────

    async def search_jobs(self, keywords: str, location: str, count: int = 25) -> list[dict[str, Any]]:
        headers = await self._headers()
        params = {
            "q": "relevanceBySkills",
            "keywords": keywords,
            "locationId": location,
            "count": count,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{_API_BASE}/jobSearch",
                headers=headers,
                params=params,
                timeout=15,
            )
            if resp.status_code == 429:
                raise TransientError("LinkedIn rate limited")
            resp.raise_for_status()
            return list(resp.json().get("elements", []))

    async def send_dm(self, recipient_urn: str, message: str) -> None:
        headers = await self._headers()
        payload = {
            "recipients": {"values": [{"person": {"com.linkedin.voyager.messaging.MessagingMember": {"miniProfile": {"objectUrn": recipient_urn}}}}]},
            "subject": "",
            "body": message,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{_API_BASE}/messages",
                headers=headers,
                json=payload,
                timeout=15,
            )
            if resp.status_code == 429:
                raise TransientError("LinkedIn rate limited")
            resp.raise_for_status()
            log.info("linkedin_dm_sent", recipient=recipient_urn)

    async def get_connections(self, company_slug: str | None = None) -> list[dict[str, Any]]:
        headers = await self._headers()
        params: dict[str, Any] = {"q": "viewer", "start": 0, "count": 50}
        if company_slug:
            params["currentCompany"] = company_slug
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{_API_BASE}/connections",
                headers=headers,
                params=params,
                timeout=15,
            )
            resp.raise_for_status()
            return list(resp.json().get("elements", []))
