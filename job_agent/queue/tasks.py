from __future__ import annotations

import os
from typing import Any

from celery import Celery

_REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("job_agent", broker=_REDIS_URL, backend=_REDIS_URL)
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_email(self, to: str, subject: str, body_html: str, body_text: str, idempotency_key: str) -> None:
    import asyncio
    from job_agent.tools.email_tool import EmailTool
    try:
        asyncio.get_event_loop().run_until_complete(
            EmailTool().send(to, subject, body_html, body_text)
        )
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_linkedin_dm(self, recipient_urn: str, message: str, idempotency_key: str) -> None:
    import asyncio
    from job_agent.tools.linkedin_api import LinkedInClient
    try:
        asyncio.get_event_loop().run_until_complete(
            LinkedInClient().send_dm(recipient_urn, message)
        )
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=1)
def poll_inbox(self) -> None:
    import asyncio
    from job_agent.tools.email_tool import EmailTool
    asyncio.get_event_loop().run_until_complete(EmailTool().poll_inbox())


@celery_app.task(bind=True, max_retries=1)
def submit_form(self, application_id: str, resume_path: str, idempotency_key: str) -> None:
    pass  # Implemented by form_filler agent
