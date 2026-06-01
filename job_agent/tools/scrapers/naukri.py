from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from job_agent.ports.scraper import Job
from job_agent.tools.scrapers.base import BaseScraper


class NaukriScraper(BaseScraper):
    platform = "naukri"
    _BASE = "https://www.naukri.com"

    async def search(self, keywords: str, location: str = "", pages: int = 3) -> list[Job]:
        async def _run(page):
            await self._check_robots(page, self._BASE)
            jobs: list[Job] = []
            for p in range(pages):
                url = f"{self._BASE}/{keywords.replace(' ', '-')}-jobs-in-{location or 'india'}?pageNo={p + 1}"
                await page.goto(url, wait_until="domcontentloaded")
                await self._page_delay()
                cards = await page.query_selector_all("article.jobTuple")
                for card in cards:
                    title_el = await card.query_selector("a.title")
                    company_el = await card.query_selector("a.subTitle")
                    loc_el = await card.query_selector("li.location")
                    url_el = await card.query_selector("a.title")
                    title = await title_el.inner_text() if title_el else ""
                    company = await company_el.inner_text() if company_el else ""
                    loc = await loc_el.inner_text() if loc_el else location
                    href = await url_el.get_attribute("href") if url_el else ""
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
                        remote=False,
                        experience_level="",
                        posted_at=datetime.now(timezone.utc),
                        scraped_at=datetime.now(timezone.utc),
                        match_score=0.0,
                        status="discovered",
                        source_type="browser",
                    ))
            return jobs

        return await self.run_with_browser(_run)
