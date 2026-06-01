from __future__ import annotations

from job_agent.config.loader import load_config


async def build_checkpointer():  # type: ignore[return]
    """Returns AsyncPostgresSaver in production, MemorySaver in tests/dev."""
    settings, _ = load_config()

    if settings.database_url.startswith("postgresql"):
        try:
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
            pg_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
            checkpointer = AsyncPostgresSaver.from_conn_string(pg_url)
            await checkpointer.setup()
            return checkpointer
        except ImportError:
            pass  # langgraph-checkpoint-postgres not installed — fall through

    # Dev / test fallback
    from langgraph.checkpoint.memory import MemorySaver
    return MemorySaver()
