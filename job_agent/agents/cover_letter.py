from __future__ import annotations

import structlog

from job_agent.agents.company_research import CompanyProfile
from job_agent.ports.llm import LLMPort

log = structlog.get_logger()

_MAX_AI_SCORE = 0.4
_MIN_WORDS = 180
_MAX_WORDS = 240

_BANNED_PHRASES = [
    "I am passionate about", "I would be a great fit", "Please find attached",
    "To whom it may concern", "I am writing to express my interest",
    "leverage my skills", "dynamic team", "thrilled", "excited", "delighted",
]

_SYSTEM_PROMPT = """Write a cover letter (180–240 words). Rules:
- Specific hook: why THIS company, not "I am excited to apply"
- 2 experience points with numbers from the resume
- Clear ask in final paragraph
- NO: {banned}
- NO exclamation marks
- Tone: match company culture (startup = direct, enterprise = professional)
- Plain text, no markdown""".format(banned=", ".join(f'"{p}"' for p in _BANNED_PHRASES))


async def write(
    resume_summary: str,
    jd_text: str,
    company_profile: CompanyProfile,
    candidate_name: str,
    llm: LLMPort,
    ai_detector,
) -> dict[str, str]:
    """Returns {body, ai_score}."""
    culture = "startup" if any(k in company_profile.culture_keywords for k in ["startup", "fast-paced", "agile"]) else "professional"
    user_prompt = (
        f"Company: {company_profile.name}\n"
        f"Culture: {culture}\n"
        f"Recent news: {'; '.join(company_profile.recent_news[:2])}\n"
        f"JD (first 400 chars): {jd_text[:400]}\n"
        f"Candidate background: {resume_summary[:400]}\n"
        f"Candidate name: {candidate_name}"
    )

    body = ""
    ai_detect_score = 1.0

    for attempt in range(3):
        result = llm.complete(
            "cover_letter",
            [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4 + attempt * 0.1,
        )
        if result.is_err():
            continue
        candidate = result.unwrap().text
        word_count = len(candidate.split())
        ai_detect_score = await ai_detector.score(candidate)
        if ai_detect_score < _MAX_AI_SCORE and _MIN_WORDS <= word_count <= _MAX_WORDS:
            body = candidate
            break
        user_prompt += "\n\nPREVIOUS TOO SHORT OR AI-FLAGGED. Write more naturally, vary sentence structure."

    if not body and not result.is_err():  # type: ignore[possibly-undefined]
        body = result.unwrap().text  # type: ignore[possibly-undefined]

    log.info("cover_letter_done", word_count=len(body.split()), ai_score=ai_detect_score)
    return {"body": body, "ai_score": ai_detect_score}
