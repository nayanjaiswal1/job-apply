from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from job_agent.db.models import ResumeVersion


class ResumeVersionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, version: ResumeVersion) -> None:
        self._session.add(version)

    async def get(self, version_id: str) -> ResumeVersion | None:
        result = await self._session.execute(
            select(ResumeVersion).where(ResumeVersion.id == version_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[ResumeVersion]:
        result = await self._session.execute(
            select(ResumeVersion).order_by(ResumeVersion.created_at.desc())
        )
        return list(result.scalars().all())

    async def latest(self) -> ResumeVersion | None:
        result = await self._session.execute(
            select(ResumeVersion).order_by(ResumeVersion.created_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()
