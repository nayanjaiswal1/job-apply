from __future__ import annotations

import re
import uuid
from contextvars import ContextVar

import structlog

_request_id: ContextVar[str] = ContextVar("request_id", default="")

_PII_PATTERNS = [
    (re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"), "[email]"),
    (re.compile(r"\+?\d[\d\s\-().]{7,}\d"), "[phone]"),
]


def _scrub_pii(value: str) -> str:
    for pattern, replacement in _PII_PATTERNS:
        value = pattern.sub(replacement, value)
    return value


class _PiiScrubber:
    def __call__(
        self,
        logger: object,
        method: str,
        event_dict: dict[str, object],
    ) -> dict[str, object]:
        for key, value in list(event_dict.items()):
            if isinstance(value, str):
                event_dict[key] = _scrub_pii(value)
        return event_dict


def configure_logging() -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            _PiiScrubber(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )


def new_request_id() -> str:
    rid = uuid.uuid4().hex
    _request_id.set(rid)
    structlog.contextvars.bind_contextvars(request_id=rid)
    return rid
