from __future__ import annotations

import json
from datetime import datetime, timezone

import structlog
from pydantic import BaseModel

from job_agent.ports.llm import LLMPort
from job_agent.ports.researcher import ResearchPort

log = structlog.get_logger()


class CompanyProfile(BaseModel):
    name: str
    funding_stage: str = ""
    team_size: str = ""
    tech_stack: list[str] = []
    glassdoor_rating: float | None = None
    recent_news: list[str] = []
    culture_keywords: list[str] = []
    summary: str = ""


_RESEARCH_PROMPT = """Research this company and return a JSON object with these keys:
funding_stage, team_size, tech_stack (list), glassdoor_rating (float or null),
recent_news (list of 2-3 items), culture_keywords (list), summary (2 sentences).

Company: {company}
Context from web search:
{context}

Return ONLY valid JSON."""

_CACHE_TTL_DAYS = 7


async def get_or_research(
    company_name: str,
    company_id: str,
    researcher: ResearchPort,
    llm: LLMPort,
    company_repo,
) -> CompanyProfile:
    """Returns cached CompanyProfile or triggers fresh research."""
    existing = await company_repo.get(company_id)
    if existing and existing.researched_at:
        age_days = (datetime.now(timezone.utc) - existing.researched_at.replace(tzinfo=timezone.utc)).days
        if age_days < _CACHE_TTL_DAYS and existing.summary:
            try:
                return CompanyProfile.model_validate_json(existing.summary)
            except Exception:
                pass

    results = await researcher.search(f"{company_name} company funding tech stack culture", max_results=5)
    context = "\n".join(f"- {r.title}: {r.snippet}" for r in results[:5])

    llm_result = llm.complete(
        "company_research",
        [{"role": "user", "content": _RESEARCH_PROMPT.format(company=company_name, context=context)}],
    )

    if llm_result.is_err():
        log.warning("company_research_fail", company=company_name, reason=str(llm_result.unwrap_err()))
        return CompanyProfile(name=company_name)

    try:
        data = json.loads(llm_result.unwrap().text)
        profile = CompanyProfile(name=company_name, **data)
    except Exception as exc:
        log.warning("company_profile_parse_fail", company=company_name, reason=str(exc))
        profile = CompanyProfile(name=company_name, summary=llm_result.unwrap().text[:500])

    log.info("company_research_done", company=company_name)
    return profile
