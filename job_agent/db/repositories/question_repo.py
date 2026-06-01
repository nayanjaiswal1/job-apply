from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from job_agent.db.models import Question


class QuestionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, question: Question) -> None:
        self._session.add(question)

    async def get(self, question_id: str) -> Question | None:
        result = await self._session.execute(
            select(Question).where(Question.id == question_id)
        )
        return result.scalar_one_or_none()

    async def list_by_job(self, job_id: str) -> list[Question]:
        result = await self._session.execute(
            select(Question).where(Question.source_jds.contains(job_id))
        )
        return list(result.scalars().all())

    async def update(self, question: Question) -> None:
        self._session.add(question)
