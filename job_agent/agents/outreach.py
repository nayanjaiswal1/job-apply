from __future__ import annotations

import uuid

import structlog

from job_agent.agents.company_research import CompanyProfile
from job_agent.db.models import Outreach
from job_agent.ports.llm import LLMPort
from job_agent.queue.rate_limiter import RateLimiter, make_idempotency_key
from job_agent.queue.tasks import send_email, send_linkedin_dm

log = structlog.get_logger()

_EMAIL_PROMPT = """Write a short recruiter outreach email (120–150 words). Rules:
- Personalise with company name, role title, and ONE insight from company research
- No hollow flattery, no "I am excited", no "leverage"
- Clear call to action in final line
- Plain text only"""


async def send_recruiter_email(
    to: str,
    job_title: str,
    company_profile: CompanyProfile,
    resume_summary: str,
    sender_name: str,
    llm: LLMPort,
    rate_limiter: RateLimiter,
    outreach_repo,
    dry_run: bool = False,
) -> bool:
    idem_key = make_idempotency_key({"to": to, "job_title": job_title, "company": company_profile.name})
    check = await rate_limiter.check("email", idem_key)
    if not check.allowed:
        log.info("outreach_rate_limited", channel="email", retry_after=check.retry_after)
        return False

    insight = company_profile.recent_news[0] if company_profile.recent_news else company_profile.summary[:100]
    result = llm.complete(
        "orchestrator",
        [{"role": "user", "content": f"{_EMAIL_PROMPT}\n\nRole: {job_title}\nCompany: {company_profile.name}\nInsight: {insight}\nSender: {sender_name}"}],
    )
    if result.is_err():
        return False

    body = result.unwrap().text
    subject = f"Re: {job_title} at {company_profile.name}"

    already_contacted = await outreach_repo.already_contacted(to, company_profile.name)
    if already_contacted:
        log.info("outreach_already_contacted", to=to, company=company_profile.name)
        return False

    if not dry_run:
        send_email.delay(to, subject, f"<pre>{body}</pre>", body, idem_key)
        await rate_limiter.mark_sent(idem_key)
        outreach = Outreach(id=uuid.uuid4().hex, person=to, company=company_profile.name, channel="email", message=body)
        await outreach_repo.save(outreach)

    log.info("outreach_queued", channel="email", to=to, dry_run=dry_run)
    return True
