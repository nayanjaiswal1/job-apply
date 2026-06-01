from __future__ import annotations

import json
import uuid
from typing import Any

import structlog

from job_agent.ports.llm import LLMPort
from job_agent.tools.resume_parser import Resume

log = structlog.get_logger()

_DEDUP_THRESHOLD = 0.88

_CATEGORIES = ["technical", "behavioural", "role_specific", "company_specific"]
_SENIOR_CATEGORIES = ["technical", "system_design", "behavioural", "role_specific", "company_specific"]

_COUNTS = {"technical": 4, "system_design": 2, "behavioural": 4, "role_specific": 3, "company_specific": 2}

_PROMPT = """Generate interview questions for this job. Return JSON array.
Each item: {{"text": "...", "category": "...", "difficulty": "easy|medium|hard", "model_answer": "..."}}

Categories to generate: {categories}
Counts per category: {counts}
JD: {jd}
Company: {company}
Candidate experience level: {level}

For behavioural: model_answer uses STAR format from candidate resume.
For technical: short answer + key points + example from resume if applicable.
For system_design (mid/senior only): clarify → design → deep dive → trade-offs.

Candidate background:
{resume_summary}

Return ONLY valid JSON array."""


async def generate_questions(
    job_id: str,
    jd_text: str,
    company_name: str,
    experience_level: str,
    resume: Resume,
    llm: LLMPort,
    embedder,
    question_repo,
) -> list[dict[str, Any]]:
    is_senior = experience_level in ("mid", "senior", "lead")
    categories = _SENIOR_CATEGORIES if is_senior else _CATEGORIES
    counts = {k: v for k, v in _COUNTS.items() if k in categories}

    result = llm.complete(
        "interview_prep",
        [{"role": "user", "content": _PROMPT.format(
            categories=", ".join(categories),
            counts=json.dumps(counts),
            jd=jd_text[:600],
            company=company_name,
            level=experience_level,
            resume_summary="\n".join(resume.experience[0].bullets[:5]) if resume.experience else "",
        )}],
    )

    if result.is_err():
        log.warning("prep_generate_fail", job_id=job_id, reason=str(result.unwrap_err()))
        return []

    try:
        questions = json.loads(result.unwrap().text)
        if not isinstance(questions, list):
            return []
    except Exception as exc:
        log.warning("prep_parse_fail", job_id=job_id, reason=str(exc))
        return []

    saved: list[dict[str, Any]] = []
    for q in questions:
        text = q.get("text", "").strip()
        if not text:
            continue

        # Embed + dedup
        vec = await embedder.embed(text)
        existing = await question_repo.list_by_job(job_id)
        is_dup = False
        for existing_q in existing:
            if existing_q.embedding:
                existing_vec = list(existing_q.embedding)
                if embedder.cosine_similarity(vec, existing_vec) > _DEDUP_THRESHOLD:
                    # Merge: append this job_id to source_jds
                    source_jds = json.loads(existing_q.source_jds or "[]")
                    if job_id not in source_jds:
                        source_jds.append(job_id)
                        existing_q.source_jds = json.dumps(source_jds)
                        await question_repo.update(existing_q)
                    is_dup = True
                    break

        if not is_dup:
            from job_agent.db.models import Question
            import struct
            embedding_bytes = bytes(struct.pack(f"{len(vec)}f", *vec))
            new_q = Question(
                id=uuid.uuid4().hex,
                text=text,
                embedding=embedding_bytes,
                category=q.get("category", "technical"),
                difficulty=q.get("difficulty"),
                model_answer=q.get("model_answer"),
                source_jds=json.dumps([job_id]),
                confidence="unseen",
            )
            await question_repo.save(new_q)
            saved.append(q)
            log.info("prep_question_saved", job_id=job_id, category=q.get("category"))

    return saved
