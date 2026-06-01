from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from job_agent.ports.scraper import Job
from job_agent.tools.scrapers.base import BaseScraper


class LinkedInScraper(BaseScraper):
    """LinkedIn Playwright fallback scraper (used when OAuth API fails/returns 403)."""

    platform = "linkedin"
    _BASE = "https://www.linkedin.com"

    async def search(self, keywords: str, location: str = "", count: int = 25) -> list[Job]:
        async def _run(page):
            await self._check_robots(page, self._BASE)
            url = (
                f"{self._BASE}/jobs/search/?keywords={keywords.replace(' ', '%20')}"
                f"&location={location.replace(' ', '%20')}&f_TPR=r86400"
            )
            await page.goto(url, wait_until="domcontentloaded")
            await self._page_delay()

            jobs: list[Job] = []
            cards = await page.query_selector_all("div.job-search-card")
            for card in cards[:count]:
                title_el = await card.query_selector("h3.base-search-card__title")
                company_el = await card.query_selector("h4.base-search-card__subtitle")
                loc_el = await card.query_selector("span.job-search-card__location")
                link_el = await card.query_selector("a.base-card__full-link")
                title = await title_el.inner_text() if title_el else ""
                company = await company_el.inner_text() if company_el else ""
                loc = await loc_el.inner_text() if loc_el else location
                href = await link_el.get_attribute("href") if link_el else ""
                if not title or not company:
                    continue
                jid = hashlib.sha256(f"{title}|{company}|{loc}".lower().encode()).hexdigest()
                jobs.append(Job(
                    id=jid,
                    title=title.strip(),
                    company=company.strip(),
                    location=loc.strip(),
                    platform=self.platform,
                    url=href or "",
                    jd_text="",
                    salary_range=None,
                    remote="remote" in loc.lower(),
                    experience_level="",
                    posted_at=datetime.now(timezone.utc),
                    scraped_at=datetime.now(timezone.utc),
                    match_score=0.0,
                    status="discovered",
                    source_type="browser",
                ))
            return jobs

        return await self.run_with_browser(_run)
