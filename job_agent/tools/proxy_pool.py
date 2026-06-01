from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ProxyEntry:
    url: str
    username: str
    password: str
    pinned_platforms: set[str] = field(default_factory=set)
    request_count: int = 0
    first_used: datetime | None = None


class ProxyPool:
    """Residential proxy pool with per-platform pinning and warm-up tracking."""

    def __init__(self) -> None:
        self._pool: list[ProxyEntry] = []
        self._platform_pins: dict[str, ProxyEntry] = {}
        self._load_from_env()

    def _load_from_env(self) -> None:
        url = os.environ.get("PROXY_HTTP", "")
        username = os.environ.get("PROXY_USERNAME", "")
        password = os.environ.get("PROXY_PASSWORD", "")
        if url:
            self._pool.append(ProxyEntry(url=url, username=username, password=password))

    def get_for_platform(self, platform: str) -> ProxyEntry | None:
        if not self._pool:
            return None
        if platform in self._platform_pins:
            return self._platform_pins[platform]
        # pin the least-used proxy to this platform
        entry = min(self._pool, key=lambda p: p.request_count)
        entry.pinned_platforms.add(platform)
        if entry.first_used is None:
            entry.first_used = datetime.now(timezone.utc)
        self._platform_pins[platform] = entry
        return entry

    def record_request(self, platform: str) -> None:
        entry = self._platform_pins.get(platform)
        if entry is not None:
            entry.request_count += 1

    def is_warmed_up(self, platform: str, min_requests: int = 20) -> bool:
        entry = self._platform_pins.get(platform)
        return entry is not None and entry.request_count >= min_requests
