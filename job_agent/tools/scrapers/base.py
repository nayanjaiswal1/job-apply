from __future__ import annotations

import asyncio
import random
from pathlib import Path

import structlog
from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from job_agent.tools.proxy_pool import ProxyEntry, ProxyPool
from job_agent.tools.session_store import SessionStore

log = structlog.get_logger()

_SCREENSHOTS_DIR = Path("logs/screenshots")
_TYPING_DELAY_RANGE = (40, 120)   # ms per character (50–120 WPM)
_ACTION_DELAY = (1.0, 4.0)        # seconds between actions
_PAGE_DELAY = (3.0, 8.0)          # seconds between page loads


class BaseScraper:
    """Async Playwright base: stealth, human-input simulation, session restore, proxy injection."""

    platform: str = "base"

    def __init__(
        self,
        session_store: SessionStore | None = None,
        proxy_pool: ProxyPool | None = None,
    ) -> None:
        self._session_store = session_store or SessionStore()
        self._proxy_pool = proxy_pool or ProxyPool()

    async def _launch_context(self, browser: Browser) -> BrowserContext:
        proxy_entry: ProxyEntry | None = self._proxy_pool.get_for_platform(self.platform)
        proxy_cfg = None
        if proxy_entry:
            proxy_cfg = {
                "server": proxy_entry.url,
                "username": proxy_entry.username,
                "password": proxy_entry.password,
            }

        context = await browser.new_context(
            viewport={"width": random.randint(1280, 1920), "height": random.randint(800, 1080)},
            user_agent=self._random_ua(),
            locale="en-US",
            timezone_id="America/New_York",
            proxy=proxy_cfg,
        )

        cookies = self._session_store.load(self.platform)
        if cookies:
            await context.add_cookies([
                {"name": k, "value": v, "domain": "", "path": "/"}
                for k, v in cookies.items()
            ])
        return context

    async def _save_session(self, context: BrowserContext) -> None:
        cookies = await context.cookies()
        self._session_store.save(
            self.platform,
            {c["name"]: c["value"] for c in cookies},
        )

    async def _screenshot_on_fail(self, page: Page, label: str) -> None:
        _SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        from datetime import datetime
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        path = _SCREENSHOTS_DIR / f"{ts}_{self.platform}_{label}.png"
        try:
            await page.screenshot(path=str(path))
            log.info("screenshot_saved", path=str(path))
        except Exception:
            pass

    async def _human_type(self, page: Page, selector: str, text: str) -> None:
        await page.click(selector)
        for char in text:
            await page.keyboard.type(char)
            await asyncio.sleep(random.randint(*_TYPING_DELAY_RANGE) / 1000)

    async def _human_delay(self, short: bool = False) -> None:
        lo, hi = (0.5, 1.5) if short else _ACTION_DELAY
        await asyncio.sleep(random.uniform(lo, hi))

    async def _page_delay(self) -> None:
        await asyncio.sleep(random.uniform(*_PAGE_DELAY))

    async def _check_robots(self, page: Page, base_url: str) -> bool:
        """Return True if scraping is allowed per robots.txt."""
        try:
            resp = await page.goto(f"{base_url}/robots.txt", wait_until="domcontentloaded")
            if resp and resp.ok:
                text = await resp.text()
                if "Disallow: /" in text:
                    log.warning("robots_disallowed", platform=self.platform, url=base_url)
                    return False
        except Exception:
            pass
        return True

    def _random_ua(self) -> str:
        agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        ]
        return random.choice(agents)

    async def run_with_browser(self, fn):  # type: ignore[type-arg]
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await self._launch_context(browser)
            page = await context.new_page()
            try:
                result = await fn(page)
                await self._save_session(context)
                return result
            except Exception as exc:
                await self._screenshot_on_fail(page, "error")
                raise
            finally:
                await context.close()
                await browser.close()
