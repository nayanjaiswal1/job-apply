from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import structlog

from job_agent.db.models import FollowUp
from job_agent.ports.llm import LLMPort

log = structlog.get_logger()

_NUDGE_PROMPT = """Write a brief follow-up email (60–80 words). Rules:
- Reference the original application (role + company)
- Politely check on status
- No desperation, no "just following up" opener
- End with one clear question
- Plain text only"""


async def check_and_draft(
    application_repo,
    followup_repo,
    outreach_repo,
    llm: LLMPort,
    dry_run: bool = False,
) -> list[str]:
    """Creates follow-up drafts for applications at day +7, +14, +21."""
    applications = await application_repo.list_by_status("applied")
    applications += await application_repo.list_by_status("outreach_sent")
    drafted_ids: list[str] = []
    now = datetime.now(timezone.utc)

    for app in applications:
        if not app.sent_at:
            continue
        sent = app.sent_at.replace(tzinfo=timezone.utc)
        days_elapsed = (now - sent).days

        for day_offset in (7, 14, 21):
            if days_elapsed < day_offset:
                break

            existing = await followup_repo.list_by_application(app.id)
            already_has = any(f.day_offset == day_offset for f in existing)
            if already_has:
                continue

            if day_offset == 21:
                await application_repo.update_status(app.id, "archived")
                log.info("application_archived", app_id=app.id)
                break

            if day_offset == 14:
                await application_repo.update_status(app.id, "ghosted")

            # Draft the nudge
            result = llm.complete(
                "mail_classifier",
                [{"role": "user", "content": f"{_NUDGE_PROMPT}\n\nRole: unknown\nCompany: unknown\nDay: +{day_offset}"}],
            )
            draft = result.unwrap().text if not result.is_err() else ""

            fu = FollowUp(
                id=uuid.uuid4().hex,
                application_id=app.id,
                day_offset=day_offset,
                channel="email",
                draft=draft,
                status="draft",
            )
            if not dry_run:
                await followup_repo.save(fu)
                drafted_ids.append(fu.id)
            log.info("followup_drafted", app_id=app.id, day_offset=day_offset)

    return drafted_ids
