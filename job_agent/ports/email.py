from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass
class RawEmail:
    message_id: str
    subject: str
    sender: str
    body_text: str
    received_at: datetime


class EmailPort(Protocol):
    async def send(self, to: str, subject: str, body_html: str, body_text: str) -> None: ...
    async def poll_inbox(self, since_hours: int = 1) -> list[RawEmail]: ...
