from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from job_agent.db.models import Company


class CompanyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, company_id: str) -> Company | None:
        result = await self._session.execute(
            select(Company).where(Company.id == company_id)
        )
        return result.scalar_one_or_none()

    async def upsert(self, company: Company) -> None:
        existing = await self.get(company.id)
        if existing is not None:
            existing.summary = company.summary
            existing.tech_stack = company.tech_stack
            existing.glassdoor_rating = company.glassdoor_rating
            existing.researched_at = company.researched_at
        else:
            self._session.add(company)
