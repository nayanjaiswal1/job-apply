from __future__ import annotations

import os

import structlog

from job_agent.errors import UpstreamUnavailable
from job_agent.ports.researcher import ResearchPort, SearchResult

log = structlog.get_logger()


class ResearchTool:
    """ResearchPort: Tavily primary, SerpAPI fallback."""

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        tavily_key = os.environ.get("TAVILY_API_KEY", "")
        if tavily_key:
            try:
                return await self._tavily(query, max_results, tavily_key)
            except Exception as exc:
                log.warning("tavily_fail", reason=str(exc))

        serpapi_key = os.environ.get("SERPAPI_API_KEY", "")
        if serpapi_key:
            try:
                return await self._serpapi(query, max_results, serpapi_key)
            except Exception as exc:
                log.warning("serpapi_fail", reason=str(exc))

        raise UpstreamUnavailable("No search provider available")

    async def _tavily(self, query: str, max_results: int, key: str) -> list[SearchResult]:
        from tavily import TavilyClient  # type: ignore[import]
        client = TavilyClient(api_key=key)
        resp = client.search(query=query, max_results=max_results)
        return [
            SearchResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                snippet=r.get("content", ""),
                source="tavily",
            )
            for r in resp.get("results", [])
        ]

    async def _serpapi(self, query: str, max_results: int, key: str) -> list[SearchResult]:
        import httpx
        params = {"q": query, "api_key": key, "num": max_results, "engine": "google"}
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://serpapi.com/search", params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        return [
            SearchResult(
                title=r.get("title", ""),
                url=r.get("link", ""),
                snippet=r.get("snippet", ""),
                source="serpapi",
            )
            for r in data.get("organic_results", [])[:max_results]
        ]


def _check() -> None:
    _: ResearchPort = ResearchTool.__new__(ResearchTool)  # type: ignore[type-abstract]


_check()
