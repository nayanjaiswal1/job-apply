from __future__ import annotations

import json
from typing import Any

import structlog

from job_agent.errors import HumanReviewNeeded
from job_agent.ports.llm import LLMPort
from job_agent.tools.ats_scorer import score as ats_score
from job_agent.tools.resume_parser import Resume

log = structlog.get_logger()

_MAX_AI_SCORE = 0.4
_TARGETED_THRESHOLD = 0.55
_MAX_REWRITE_ATTEMPTS = 3

_SYSTEM_PROMPT = """You rewrite resumes to match job descriptions. Follow ALL rules:

ALLOWED VERBS ONLY: built, wrote, designed, migrated, reduced, increased, shipped, reviewed, fixed,
led, ran, set up, debugged, deployed, integrated, automated, documented, tested, refactored, cut,
moved, added.

BANNED (never use): Spearheaded, Leveraged, Orchestrated, Championed, Fostered, Utilized,
Facilitated, Streamlined, Synergized, Revolutionized, and any em-dash (—).

REQUIRED: Every bullet must contain a specific number OR a named technology.
VARY sentence length: mix short (<10 words) with longer.
NO adjectives unless factual ("distributed", "real-time").
NO first person ("I built", "I led").
NO Unicode symbols, no markdown bold, no asterisks.
Output plain text only."""


async def rewrite(
    resume: Resume,
    jd_text: str,
    match_score: float,
    llm: LLMPort,
    ai_detector,
) -> dict[str, Any]:
    """Returns {resume_text, ats_before, ats_after, ai_score, gap_report}."""
    resume_text = _resume_to_text(resume)
    ats_before = ats_score(resume_text, jd_text)
    mode = "targeted" if match_score >= _TARGETED_THRESHOLD else "full_regen"

    user_prompt = _build_prompt(resume, jd_text, mode)
    rewritten = ""
    ai_detect_score = 1.0

    for attempt in range(_MAX_REWRITE_ATTEMPTS):
        result = llm.complete(
            "resume_rewrite",
            [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3 + attempt * 0.1,
        )
        if result.is_err():
            log.warning("resume_rewrite_fail", attempt=attempt, reason=str(result.unwrap_err()))
            continue

        candidate = result.unwrap().text
        ai_detect_score = await ai_detector.score(candidate)
        log.info("resume_rewrite_attempt", attempt=attempt, ai_score=ai_detect_score)

        if ai_detect_score < _MAX_AI_SCORE:
            rewritten = candidate
            break

        user_prompt += "\n\nPREVIOUS OUTPUT WAS FLAGGED AS AI. Rewrite more naturally. Use more varied sentence structures and lengths."

    if not rewritten:
        rewritten = result.unwrap().text if not result.is_err() else resume_text  # type: ignore[possibly-undefined]

    ats_after = ats_score(rewritten, jd_text)
    gap_report = _gap_report(resume, jd_text)

    log.info("resume_rewrite_done", ats_before=ats_before, ats_after=ats_after, ai_score=ai_detect_score)

    return {
        "resume_text": rewritten,
        "ats_before": ats_before,
        "ats_after": ats_after,
        "ai_score": ai_detect_score,
        "gap_report": gap_report,
        "mode": mode,
    }


def _resume_to_text(resume: Resume) -> str:
    parts = []
    if resume.summary:
        parts.append(resume.summary)
    for exp in resume.experience:
        parts.append(f"{exp.title} at {exp.company}")
        parts.extend(exp.bullets)
    parts.append(", ".join(resume.skills))
    return "\n".join(parts)


def _build_prompt(resume: Resume, jd_text: str, mode: str) -> str:
    resume_text = _resume_to_text(resume)
    if mode == "targeted":
        return (
            f"TARGETED EDIT — adjust only what's needed to match the JD.\n\n"
            f"JD:\n{jd_text[:800]}\n\nCurrent resume:\n{resume_text[:1200]}"
        )
    return (
        f"FULL REWRITE — reframe all experience to match the JD.\n\n"
        f"JD:\n{jd_text[:800]}\n\nCurrent resume:\n{resume_text[:1200]}"
    )


def _gap_report(resume: Resume, jd_text: str) -> dict[str, list[str]]:
    import re
    resume_words = set(resume.skills) | {w.lower() for exp in resume.experience for b in exp.bullets for w in b.split()}
    jd_words = set(re.findall(r"\b[a-zA-Z][a-zA-Z0-9+#]{2,}\b", jd_text.lower()))
    missing = jd_words - {w.lower() for w in resume_words}
    # Simple heuristic: words appearing ≥2 times in JD = important
    from collections import Counter
    jd_counter = Counter(re.findall(r"\b[a-zA-Z][a-zA-Z0-9+#]{2,}\b", jd_text.lower()))
    critical = [w for w in missing if jd_counter[w] >= 3]
    important = [w for w in missing if jd_counter[w] == 2]
    nice = [w for w in missing if jd_counter[w] == 1 and len(w) > 4][:10]
    return {"critical": critical[:10], "important": important[:10], "nice_to_have": nice}
