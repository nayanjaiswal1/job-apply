from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass
class Job:
    id: str
    title: str
    company: str
    location: str
    platform: str
    url: str
    jd_text: str
    salary_range: str | None
    remote: bool
    experience_level: str
    posted_at: datetime
    scraped_at: datetime
    match_score: float
    status: str
    source_type: str


class ScraperPort(Protocol):
    async def search(self, query: str, preferences: object) -> list[Job]: ...
