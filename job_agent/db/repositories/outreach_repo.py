from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from job_agent.db.models import Outreach


class OutreachRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, outreach: Outreach) -> None:
        self._session.add(outreach)

    async def already_contacted(self, person: str, company: str) -> bool:
        result = await self._session.execute(
            select(Outreach).where(Outreach.person == person, Outreach.company == company)
        )
        return result.scalar_one_or_none() is not None

    async def get_by_job(self, job_id: str) -> list[Outreach]:
        result = await self._session.execute(
            select(Outreach).where(Outreach.job_id == job_id)
        )
        return list(result.scalars().all())
