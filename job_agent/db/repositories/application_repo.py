from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from job_agent.db.models import Application


class ApplicationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, application: Application) -> None:
        self._session.add(application)

    async def get(self, application_id: str) -> Application | None:
        result = await self._session.execute(
            select(Application).where(Application.id == application_id)
        )
        return result.scalar_one_or_none()

    async def list_by_status(self, status: str) -> list[Application]:
        result = await self._session.execute(
            select(Application).where(Application.status == status)
        )
        return list(result.scalars().all())

    async def update_status(self, application_id: str, status: str) -> None:
        app = await self.get(application_id)
        if app is not None:
            app.status = status
