from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from job_agent.db.models import UserProfile


class UserProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self) -> UserProfile | None:
        result = await self._session.execute(select(UserProfile).where(UserProfile.id == "me"))
        return result.scalar_one_or_none()

    async def upsert(self, profile: UserProfile) -> None:
        profile.id = "me"
        self._session.add(profile)

    async def set_onboarding_step(self, step: int) -> None:
        profile = await self.get()
        if profile is not None:
            profile.onboarding_step = step

    async def set_preferences(self, preferences_json: str) -> None:
        profile = await self.get()
        if profile is not None:
            profile.preferences = preferences_json
