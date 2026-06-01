from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass

import redis.asyncio as aioredis

# Daily caps + stagger windows (seconds)
_LIMITS: dict[str, tuple[int, int, int]] = {
    "email": (50, 300, 900),          # 50/day, 5–15 min stagger
    "linkedin_dm": (20, 60, 180),     # 20/day, 60–180s stagger
}
_DAY_SECONDS = 86400


@dataclass
class TokenBucketResult:
    allowed: bool
    retry_after: int = 0   # seconds until allowed


class RateLimiter:
    def __init__(self, redis_url: str) -> None:
        self._redis = aioredis.from_url(redis_url)

    async def check(self, channel: str, idempotency_key: str) -> TokenBucketResult:
        """Returns allowed=True if within daily cap and stagger window."""
        limit, min_stagger, max_stagger = _LIMITS.get(channel, (100, 0, 0))

        # Idempotency: if key already sent, no-op (allowed=True, won't actually re-send)
        idem_key = f"idem:{idempotency_key}"
        if await self._redis.exists(idem_key):
            return TokenBucketResult(allowed=True)

        # Daily counter
        day_key = f"rate:{channel}:{_today()}"
        count = await self._redis.incr(day_key)
        if count == 1:
            await self._redis.expire(day_key, _DAY_SECONDS)
        if count > limit:
            await self._redis.decr(day_key)
            return TokenBucketResult(allowed=False, retry_after=_seconds_until_tomorrow())

        # Stagger: check last-sent timestamp
        stagger_key = f"stagger:{channel}"
        last_sent = await self._redis.get(stagger_key)
        if last_sent:
            elapsed = time.time() - float(last_sent)
            if elapsed < min_stagger:
                await self._redis.decr(day_key)
                return TokenBucketResult(allowed=False, retry_after=int(min_stagger - elapsed))

        await self._redis.set(stagger_key, time.time(), ex=max_stagger)
        return TokenBucketResult(allowed=True)

    async def mark_sent(self, idempotency_key: str) -> None:
        idem_key = f"idem:{idempotency_key}"
        await self._redis.set(idem_key, "1", ex=_DAY_SECONDS * 30)


def make_idempotency_key(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def _today() -> str:
    from datetime import date
    return date.today().isoformat()


def _seconds_until_tomorrow() -> int:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    from datetime import timedelta
    return int((_DAY_SECONDS - (now - midnight).seconds))
