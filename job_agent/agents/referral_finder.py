from __future__ import annotations

import structlog

from job_agent.ports.llm import LLMPort

log = structlog.get_logger()

_EXCLUDED_TITLES = {"recruiter", "talent acquisition", "hr", "human resources", "people ops"}

_DM_PROMPT = """Write a brief LinkedIn DM to request a referral. Rules:
- Reference a mutual connection or shared background if provided
- One line on role fit (specific, not generic)
- Specific ask: "Would you be open to referring me or sharing context about the team?"
- Max 80 words. Plain text only. No exclamation marks."""


def _is_hr_title(title: str) -> bool:
    title_lower = title.lower()
    return any(t in title_lower for t in _EXCLUDED_TITLES)


async def find_and_rank(
    company_slug: str,
    role_title: str,
    linkedin_client,
    llm: LLMPort,
) -> list[dict]:
    connections = await linkedin_client.get_connections(company_slug)
    candidates = [c for c in connections if not _is_hr_title(c.get("title", ""))]

    def rank_key(c: dict) -> int:
        degree = c.get("degree", 2)
        score = 0
        if degree == 1:
            score += 10
        active = bool(c.get("recentActivity"))
        if active:
            score += 3
        return -score

    ranked = sorted(candidates, key=rank_key)[:10]

    drafts = []
    for contact in ranked:
        name = contact.get("name", "")
        mutual = contact.get("mutualConnection", "")
        context = f"Mutual: {mutual}" if mutual else ""
        result = llm.complete(
            "referral_dm",
            [{"role": "user", "content": f"{_DM_PROMPT}\n\nRecipient: {name}\nRole: {role_title}\nCompany: {company_slug}\n{context}"}],
        )
        dm = result.unwrap().text if not result.is_err() else ""
        drafts.append({**contact, "draft_dm": dm})
        log.info("referral_draft", name=name, company=company_slug)

    return drafts
