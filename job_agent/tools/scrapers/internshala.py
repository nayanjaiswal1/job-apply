from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from job_agent.ports.scraper import Job
from job_agent.tools.scrapers.base import BaseScraper


class IntershalaScraper(BaseScraper):
    platform = "internshala"
    _BASE = "https://internshala.com"

    async def search(self, keywords: str) -> list[Job]:
        async def _run(page):
            await self._check_robots(page, self._BASE)
            slug = keywords.lower().replace(" ", "-")
            await page.goto(f"{self._BASE}/jobs/{slug}-jobs", wait_until="domcontentloaded")
            await self._page_delay()

            jobs: list[Job] = []
            cards = await page.query_selector_all(".individual_internship")
            for card in cards:
                title_el = await card.query_selector(".job-title-href")
                company_el = await card.query_selector(".company-name")
                loc_el = await card.query_selector(".locations span")
                title = await title_el.inner_text() if title_el else ""
                company = await company_el.inner_text() if company_el else ""
                loc = await loc_el.inner_text() if loc_el else ""
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
                    remote="work from home" in loc.lower(),
                    experience_level="junior",
                    posted_at=datetime.now(timezone.utc),
                    scraped_at=datetime.now(timezone.utc),
                    match_score=0.0,
                    status="discovered",
                    source_type="browser",
                ))
            return jobs

        return await self.run_with_browser(_run)
