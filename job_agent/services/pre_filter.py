from __future__ import annotations

from job_agent.models.preferences import Preferences
from job_agent.ports.scraper import Job


def passes_pre_filter(job: Job, prefs: Preferences) -> bool:
    """Rule-based pre-filter. Returns False if job should be skipped before LLM scoring."""
    title_lower = job.title.lower()
    company_lower = job.company.lower()
    jd_lower = (job.jd_text or "").lower()

    if company_lower in (c.lower() for c in prefs.blacklist_companies):
        return False

    for keyword in prefs.blacklist_keywords:
        if keyword.lower() in title_lower or keyword.lower() in jd_lower:
            return False

    if prefs.remote != "any":
        if prefs.remote == "remote" and not job.remote:
            return False

    if prefs.role_levels and job.experience_level:
        if job.experience_level not in prefs.role_levels:
            return False

    if prefs.preferred_locations:
        location_lower = (job.location or "").lower()
        if not any(loc.lower() in location_lower for loc in prefs.preferred_locations):
            if not job.remote:
                return False

    return True
