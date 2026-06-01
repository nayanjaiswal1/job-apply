from typing import Protocol


class CaptchaPort(Protocol):
    async def solve(self, site_key: str, page_url: str, captcha_type: str = "recaptcha_v2") -> str: ...
