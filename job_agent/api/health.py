from __future__ import annotations

import asyncio
from typing import Any

import redis.asyncio as aioredis
import structlog
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from job_agent.config.loader import load_config
from job_agent.db.session import get_session

log = structlog.get_logger()
router = APIRouter()


async def _check_db() -> bool:
    try:
        async with get_session() as session:
            await session.execute(__import__("sqlalchemy").text("SELECT 1"))
        return True
    except Exception as exc:
        log.warning("health_db_fail", reason=str(exc))
        return False


async def _check_redis() -> bool:
    try:
        settings, _ = load_config()
        client = aioredis.from_url(settings.redis_url)
        await client.ping()
        await client.aclose()
        return True
    except Exception as exc:
        log.warning("health_redis_fail", reason=str(exc))
        return False


async def _check_chroma() -> bool:
    try:
        import chromadb

        client = chromadb.HttpClient(host="localhost", port=8001)
        client.heartbeat()
        return True
    except Exception as exc:
        log.warning("health_chroma_fail", reason=str(exc))
        return False


@router.get("/health")
async def health() -> JSONResponse:
    db_ok, redis_ok, chroma_ok = await asyncio.gather(
        _check_db(), _check_redis(), _check_chroma()
    )
    status: dict[str, Any] = {
        "db": "ok" if db_ok else "fail",
        "redis": "ok" if redis_ok else "fail",
        "chroma": "ok" if chroma_ok else "fail",
    }
    critical_down = not db_ok or not redis_ok
    http_status = 503 if critical_down else 200
    return JSONResponse(content=status, status_code=http_status)
