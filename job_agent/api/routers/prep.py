from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from job_agent.db.repositories.question_repo import QuestionRepository
from job_agent.db.session import get_session

router = APIRouter(prefix="/api/v1/prep", tags=["prep"])


class ConfidencePatch(BaseModel):
    confidence: str
    user_answer: str | None = None


@router.get("/questions")
async def list_questions(
    category: str | None = None,
    confidence: str | None = None,
    job_id: str | None = None,
) -> list[dict[str, Any]]:
    async with get_session() as session:
        repo = QuestionRepository(session)
        if job_id:
            questions = await repo.list_by_job(job_id)
        else:
            from sqlalchemy import select
            from job_agent.db.models import Question
            stmt = select(Question).order_by(Question.confidence, Question.created_at)
            if category:
                stmt = stmt.where(Question.category == category)
            if confidence:
                stmt = stmt.where(Question.confidence == confidence)
            result = await session.execute(stmt)
            questions = list(result.scalars().all())
    return [_q_dict(q) for q in questions]


@router.get("/questions/{question_id}")
async def get_question(question_id: str) -> dict[str, Any]:
    async with get_session() as session:
        repo = QuestionRepository(session)
        q = await repo.get(question_id)
        if q is None:
            raise HTTPException(status_code=404, detail="Question not found")
        return _q_dict(q)


@router.put("/questions/{question_id}")
async def update_question(question_id: str, body: ConfidencePatch) -> dict[str, Any]:
    async with get_session() as session:
        repo = QuestionRepository(session)
        q = await repo.get(question_id)
        if q is None:
            raise HTTPException(status_code=404, detail="Question not found")
        if body.confidence:
            q.confidence = body.confidence
            q.practice_count = (q.practice_count or 0) + 1
        if body.user_answer is not None:
            q.user_answer = body.user_answer
        await repo.update(q)
        return _q_dict(q)


@router.get("/jobs/{job_id}")
async def questions_for_job(job_id: str) -> list[dict[str, Any]]:
    async with get_session() as session:
        repo = QuestionRepository(session)
        questions = await repo.list_by_job(job_id)
    return [_q_dict(q) for q in questions]


def _q_dict(q) -> dict[str, Any]:
    import json
    return {
        "id": q.id, "text": q.text, "category": q.category,
        "difficulty": q.difficulty, "model_answer": q.model_answer,
        "user_answer": q.user_answer, "confidence": q.confidence,
        "practice_count": q.practice_count,
        "tags": json.loads(q.tags) if q.tags else [],
        "source_jds": json.loads(q.source_jds) if q.source_jds else [],
    }
