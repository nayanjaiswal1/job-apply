import os

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from job_agent.db.models import Base

# Use SQLite in-memory when Postgres is not available — matches REQUIREMENTS "SQLite (dev)"
_PG_URL = os.environ.get("DATABASE_URL", "")
TEST_DATABASE_URL = (
    _PG_URL
    if _PG_URL.startswith("postgresql")
    else "sqlite+aiosqlite:///:memory:"
)


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
async def engine():
    connect_args = {"check_same_thread": False} if "sqlite" in TEST_DATABASE_URL else {}
    eng = create_async_engine(TEST_DATABASE_URL, connect_args=connect_args)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest.fixture()
async def session(engine) -> AsyncSession:
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        async with s.begin():
            yield s
            await s.rollback()
