from __future__ import annotations

import json
from typing import Any

import structlog

from job_agent.ports.llm import LLMPort
from job_agent.ports.scraper import Job
from job_agent.services.pre_filter import passes_pre_filter
from job_agent.state.schema import JobAgentState

log = structlog.get_logger()

_SCORE_PROMPT = """Score this job posting 0.0–1.0 for the candidate based on match with their resume.
0.0 = no match, 1.0 = perfect match.
Return ONLY a decimal number, nothing else.

JD summary (first 400 chars):
{jd}

Candidate skills:
{skills}"""


async def job_search_node(state: JobAgentState, llm: LLMPort, prefs, scrapers: list, dedup) -> dict[str, Any]:
    """Discovers, pre-filters, deduplicates, and LLM-scores new jobs."""
    discovered: list[str] = []
    to_score: list[str] = []

    for scraper in scrapers:
        try:
            jobs: list[Job] = await scraper.search(
                keywords=" ".join(prefs.target_roles[:2]) if prefs.target_roles else "software engineer",
                location=prefs.preferred_locations[0] if prefs.preferred_locations else "",
            )
        except Exception as exc:
            log.warning("scraper_fail", platform=getattr(scraper, "platform", "unknown"), reason=str(exc))
            continue

        for job in jobs:
            if not passes_pre_filter(job, prefs):
                continue
            is_dup = await dedup.is_duplicate(job, set(state.get("discovered_job_ids", [])))
            if is_dup:
                continue
            discovered.append(job.id)
            to_score.append(job.id)

    return {"discovered_job_ids": discovered, "jobs_to_score": to_score}


async def score_jobs(
    job_ids: list[str],
    jobs_by_id: dict[str, Job],
    candidate_skills: list[str],
    llm: LLMPort,
    minimize: bool = False,
) -> dict[str, float]:
    scores: dict[str, float] = {}
    for job_id in job_ids:
        job = jobs_by_id.get(job_id)
        if not job:
            continue
        result = llm.complete(
            "job_scoring",
            [{"role": "user", "content": _SCORE_PROMPT.format(
                jd=(job.jd_text or "")[:400],
                skills=", ".join(candidate_skills[:20]),
            )}],
        )
        if result.is_err():
            log.warning("job_score_fail", job_id=job_id, reason=str(result.unwrap_err()))
            scores[job_id] = 0.0
            continue
        try:
            scores[job_id] = float(result.unwrap().text.strip())
        except ValueError:
            scores[job_id] = 0.0
    return scores
