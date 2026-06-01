from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from job_agent.ports.scraper import Job
from job_agent.tools.scrapers.base import BaseScraper


class WellfoundScraper(BaseScraper):
    platform = "wellfound"
    _BASE = "https://wellfound.com"

    async def search(self, keywords: str, location: str = "remote") -> list[Job]:
        async def _run(page):
            await self._check_robots(page, self._BASE)
            url = f"{self._BASE}/jobs?q={keywords.replace(' ', '+')}&l={location}"
            await page.goto(url, wait_until="networkidle")
            await self._page_delay()

            jobs: list[Job] = []
            cards = await page.query_selector_all("[data-test='StartupResult']")
            for card in cards:
                title_el = await card.query_selector("a[data-test='job-title']")
                company_el = await card.query_selector("a[data-test='startup-link']")
                loc_el = await card.query_selector("[data-test='location']")
                title = await title_el.inner_text() if title_el else ""
                company = await company_el.inner_text() if company_el else ""
                loc = await loc_el.inner_text() if loc_el else location
                href = await title_el.get_attribute("href") if title_el else ""
                if not title or not company:
                    continue
                jid = hashlib.sha256(f"{title}|{company}|{loc}".lower().encode()).hexdigest()
                jobs.append(Job(
                    id=jid,
                    title=title.strip(),
                    company=company.strip(),
                    location=loc.strip(),
                    platform=self.platform,
                    url=f"{self._BASE}{href}" if href else "",
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
