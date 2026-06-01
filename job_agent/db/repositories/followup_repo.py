from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from job_agent.db.models import FollowUp


class FollowUpRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, followup: FollowUp) -> None:
        self._session.add(followup)

    async def get(self, followup_id: str) -> FollowUp | None:
        result = await self._session.execute(
            select(FollowUp).where(FollowUp.id == followup_id)
        )
        return result.scalar_one_or_none()

    async def list_by_application(self, application_id: str) -> list[FollowUp]:
        result = await self._session.execute(
            select(FollowUp).where(FollowUp.application_id == application_id)
        )
        return list(result.scalars().all())

    async def list_by_status(self, status: str) -> list[FollowUp]:
        result = await self._session.execute(
            select(FollowUp).where(FollowUp.status == status)
        )
        return list(result.scalars().all())
