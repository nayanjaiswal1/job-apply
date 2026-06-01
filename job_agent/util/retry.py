from collections.abc import Callable
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from job_agent.errors import TransientError


def retry_transient(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 30.0,
) -> Callable[..., Any]:
    return retry(
        retry=lambda e: isinstance(e.outcome.exception(), TransientError),
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(min=min_wait, max=max_wait),
        reraise=True,
    )
