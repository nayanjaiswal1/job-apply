from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str


class ResearchPort(Protocol):
    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]: ...
