from __future__ import annotations

from typing import Literal

ApplicationStatus = Literal[
    "discovered", "applied", "outreach_sent", "interview_scheduled",
    "offer_received", "rejected", "ghosted", "withdrawn", "archived", "form_failed",
]

# Valid transitions: current_status -> set of allowed new statuses
_TRANSITIONS: dict[str, set[str]] = {
    "discovered": {"applied", "withdrawn"},
    "applied": {"outreach_sent", "interview_scheduled", "rejected", "ghosted", "withdrawn", "form_failed"},
    "outreach_sent": {"interview_scheduled", "rejected", "ghosted", "withdrawn"},
    "interview_scheduled": {"offer_received", "rejected", "withdrawn"},
    "offer_received": {"withdrawn"},
    "rejected": set(),
    "ghosted": {"applied", "withdrawn", "archived"},
    "withdrawn": set(),
    "archived": set(),
    "form_failed": {"applied", "withdrawn"},
}

_EMAIL_LABEL_TO_EVENT: dict[str, str] = {
    "interview_invite": "interview_scheduled",
    "rejection": "rejected",
    "assessment": "interview_scheduled",
    "follow_up_needed": "outreach_sent",
    "auto_reply": "applied",
}


def transition(current: str, event: str) -> str:
    """Pure function: returns new status or raises ValueError if invalid."""
    allowed = _TRANSITIONS.get(current, set())
    if event not in allowed:
        raise ValueError(f"Cannot transition from '{current}' to '{event}'")
    return event


def status_from_email_label(label: str) -> str | None:
    return _EMAIL_LABEL_TO_EVENT.get(label)
