from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from job_agent.db.models import Job


class JobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_job(self, job: Job) -> None:
        existing = await self.get(job.id)
        if existing is not None:
            existing.jd_text = job.jd_text
            existing.match_score = job.match_score
            existing.status = job.status
        else:
            self._session.add(job)

    async def get(self, job_id: str) -> Job | None:
        result = await self._session.execute(select(Job).where(Job.id == job_id))
        return result.scalar_one_or_none()

    async def list_by_status(self, status: str, limit: int = 100) -> list[Job]:
        result = await self._session.execute(
            select(Job).where(Job.status == status).limit(limit)
        )
        return list(result.scalars().all())
