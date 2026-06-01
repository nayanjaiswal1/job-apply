from __future__ import annotations

import hashlib
from datetime import datetime, timezone

import structlog

from job_agent.ports.scraper import Job
from job_agent.tools.scrapers.base import BaseScraper

log = structlog.get_logger()

_HASHTAGS = ["#hiring", "#jobopening", "#wearehiring", "#nowhiring"]

_EXTRACT_PROMPT = """Extract job posting details from this LinkedIn post text.
Return JSON with keys: company, role, contact, apply_instructions.
If a field is absent, use null.

Post:
{post_text}"""


class LinkedInPostScraper(BaseScraper):
    """Scrapes LinkedIn posts for informal job postings (task 2.8)."""

    platform = "linkedin"

    def __init__(self, llm_router=None, **kwargs) -> None:  # type: ignore[type-arg]
        super().__init__(**kwargs)
        self._llm = llm_router

    async def search_hashtag_posts(self, target_companies: list[str] | None = None) -> list[Job]:
        async def _run(page):
            jobs: list[Job] = []
            for tag in _HASHTAGS:
                url = f"https://www.linkedin.com/feed/hashtag/{tag.lstrip('#')}/"
                await page.goto(url, wait_until="domcontentloaded")
                await self._page_delay()
                posts = await page.query_selector_all("div.feed-shared-update-v2")
                for post in posts[:10]:
                    text_el = await post.query_selector("div.feed-shared-text")
                    text = await text_el.inner_text() if text_el else ""
                    if not text or len(text) < 50:
                        continue
                    extracted = await self._extract_job(text)
                    if extracted:
                        jobs.append(extracted)
            return jobs

        return await self.run_with_browser(_run)

    async def _extract_job(self, post_text: str) -> Job | None:
        if self._llm is None:
            return None
        import json
        result = self._llm.complete(
            "job_scoring",
            [{"role": "user", "content": _EXTRACT_PROMPT.format(post_text=post_text[:1000])}],
        )
        if result.is_err():
            return None
        try:
            data = json.loads(result.unwrap().text)
        except Exception:
            return None
        company = data.get("company") or ""
        role = data.get("role") or ""
        if not company or not role:
            return None
        jid = hashlib.sha256(f"{role}|{company}|linkedin_post".lower().encode()).hexdigest()
        return Job(
            id=jid,
            title=role,
            company=company,
            location="",
            platform="linkedin",
            url="",
            jd_text=post_text,
            salary_range=None,
            remote=False,
            experience_level="",
            posted_at=datetime.now(timezone.utc),
            scraped_at=datetime.now(timezone.utc),
            match_score=0.0,
            status="discovered",
            source_type="linkedin_post",
        )
