from __future__ import annotations

import os

import structlog

from job_agent.errors import HumanReviewNeeded, TransientError
from job_agent.ports.captcha import CaptchaPort

log = structlog.get_logger()

_CIRCUIT_OPEN_AFTER = 3


class CaptchaSolver:
    """CaptchaPort implementation using 2captcha + capsolver with circuit breaker."""

    def __init__(self) -> None:
        self._failures = 0
        self._twocaptcha_key = os.environ.get("TWOCAPTCHA_API_KEY", "")
        self._capsolver_key = os.environ.get("CAPSOLVER_API_KEY", "")

    def _is_open(self) -> bool:
        return self._failures >= _CIRCUIT_OPEN_AFTER

    async def solve(
        self,
        site_key: str,
        page_url: str,
        captcha_type: str = "recaptcha_v2",
    ) -> str:
        if self._is_open():
            log.warning("captcha_circuit_open", failures=self._failures)
            raise HumanReviewNeeded("Captcha solver circuit open — manual solve required")

        for provider, key in [("2captcha", self._twocaptcha_key), ("capsolver", self._capsolver_key)]:
            if not key:
                continue
            try:
                token = await self._solve_with(provider, key, site_key, page_url, captcha_type)
                self._failures = 0
                return token
            except Exception as exc:
                log.warning("captcha_provider_fail", provider=provider, reason=str(exc))

        self._failures += 1
        if self._is_open():
            raise HumanReviewNeeded("Captcha solver circuit open — manual solve required")
        raise TransientError("All captcha providers failed")

    async def _solve_with(
        self,
        provider: str,
        key: str,
        site_key: str,
        page_url: str,
        captcha_type: str,
    ) -> str:
        if provider == "2captcha":
            from twocaptcha import TwoCaptcha  # type: ignore[import]
            solver = TwoCaptcha(key)
            result = solver.recaptcha(sitekey=site_key, url=page_url)
            return str(result["code"])
        raise NotImplementedError(f"Provider {provider} not implemented")
