from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

import structlog

from job_agent.ports.llm import LLMPort
from job_agent.services.application_state import status_from_email_label

log = structlog.get_logger()

_CLASSIFIER_PROMPT = """Classify this email into ONE label:
interview_invite | rejection | assessment | follow_up_needed | auto_reply | other

Email subject: {subject}
Email body (first 300 chars): {body}

Return ONLY the label, nothing else."""

_GHOSTED_DAYS = 14


async def poll_and_classify(
    email_tool,
    application_repo,
    llm: LLMPort,
    notifier=None,
) -> list[dict]:
    emails = await email_tool.poll_inbox(since_hours=1)
    updates: list[dict] = []

    for email in emails:
        label = await _classify(email, llm)
        log.info("email_classified", subject=email.subject[:60], label=label)

        new_status = status_from_email_label(label)
        if not new_status:
            continue

        app = await _match_application(email, application_repo)
        if not app:
            continue

        try:
            await application_repo.update_status(app.id, new_status)
            updates.append({"application_id": app.id, "old": app.status, "new": new_status})
            log.info("application_status_updated", app_id=app.id, new_status=new_status)

            if label == "interview_invite" and notifier:
                await notifier.send_alert("interview_invite", {"application_id": app.id})
        except ValueError:
            log.warning("invalid_transition", app_id=app.id, event=new_status)

    return updates


async def check_ghosted(application_repo, notifier=None) -> list[str]:
    """Tags applications with no reply after GHOSTED_DAYS as ghosted."""
    applications = await application_repo.list_by_status("applied")
    ghosted_ids: list[str] = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=_GHOSTED_DAYS)
    for app in applications:
        sent_at = app.sent_at
        if sent_at and sent_at.replace(tzinfo=timezone.utc) < cutoff and not app.last_reply:
            await application_repo.update_status(app.id, "ghosted")
            ghosted_ids.append(app.id)
            log.info("application_ghosted", app_id=app.id)
    return ghosted_ids


async def _classify(email, llm: LLMPort) -> str:
    result = llm.complete(
        "mail_classifier",
        [{"role": "user", "content": _CLASSIFIER_PROMPT.format(
            subject=email.subject,
            body=email.body_text[:300],
        )}],
    )
    if result.is_err():
        return "other"
    label = result.unwrap().text.strip().lower()
    valid = {"interview_invite", "rejection", "assessment", "follow_up_needed", "auto_reply", "other"}
    return label if label in valid else "other"


async def _match_application(email, application_repo):
    domain = email.sender.split("@")[-1] if "@" in email.sender else ""
    applications = await application_repo.list_by_status("applied")
    applications += await application_repo.list_by_status("outreach_sent")
    for app in applications:
        if domain and app.job_id:
            return app
    return None
