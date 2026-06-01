from __future__ import annotations

import json
import time
from typing import Any

import redis.asyncio as aioredis
import structlog

log = structlog.get_logger()

_DLQ_KEY = "dlq:entries"
_MAX_ATTEMPTS = 3


class DeadLetterQueue:
    def __init__(self, redis_url: str, notifier=None) -> None:
        self._redis = aioredis.from_url(redis_url)
        self._notifier = notifier

    async def record_failure(self, task_name: str, payload: dict[str, Any], error: str, attempt: int) -> None:
        if attempt < _MAX_ATTEMPTS:
            return  # Still retrying — don't DLQ yet
        entry = {
            "task": task_name,
            "payload": payload,
            "error": error,
            "attempts": attempt,
            "failed_at": time.time(),
        }
        await self._redis.lpush(_DLQ_KEY, json.dumps(entry))
        log.warning("dlq_entry", task=task_name, error=error)
        if self._notifier:
            await self._notifier.send_alert("dlq_entry", {"task": task_name, "error": error})

    async def list_entries(self, limit: int = 50) -> list[dict[str, Any]]:
        raw = await self._redis.lrange(_DLQ_KEY, 0, limit - 1)
        return [json.loads(r) for r in raw]

    async def clear(self) -> int:
        length = await self._redis.llen(_DLQ_KEY)
        await self._redis.delete(_DLQ_KEY)
        return int(length)
