import operator
from typing import get_type_hints

import pytest

from job_agent.state.schema import JobAgentState


def test_state_fields_exist() -> None:
    state = JobAgentState(
        messages=[],
        discovered_job_ids=[],
        jobs_to_score=[],
        scored_job_ids=[],
        application_ids=[],
        active_agent="orchestrator",
        minimize=False,
        dry_run=False,
        errors=[],
    )
    assert state["active_agent"] == "orchestrator"
    assert state["minimize"] is False
    assert state["dry_run"] is False


def test_list_fields_use_add_reducer() -> None:
    # include_extras=True preserves Annotated metadata even with PEP 563/649
    hints = get_type_hints(JobAgentState, include_extras=True)
    for field in ("discovered_job_ids", "jobs_to_score", "scored_job_ids", "application_ids", "errors"):
        assert field in hints, f"Missing field: {field}"
        metadata = getattr(hints[field], "__metadata__", None)
        assert metadata is not None, f"{field} has no Annotated metadata"
        assert operator.add in metadata, f"{field} reducer should be operator.add"


@pytest.mark.anyio
async def test_checkpointer_returns_memory_saver_for_sqlite() -> None:
    from unittest.mock import MagicMock, patch
    import job_agent.state.checkpointer as chk_module
    settings = MagicMock()
    settings.database_url = "sqlite+aiosqlite:///:memory:"
    with patch.object(chk_module, "load_config", return_value=(settings, MagicMock())):
        result = await chk_module.build_checkpointer()
    from langgraph.checkpoint.memory import MemorySaver
    assert isinstance(result, MemorySaver)


@pytest.mark.anyio
async def test_checkpointer_uses_memory_saver_when_postgres_unavailable() -> None:
    from unittest.mock import MagicMock, patch
    import job_agent.state.checkpointer as chk_module
    settings = MagicMock()
    settings.database_url = "postgresql+asyncpg://u:p@localhost/db"
    with patch.object(chk_module, "load_config", return_value=(settings, MagicMock())), \
         patch.dict("sys.modules", {"langgraph.checkpoint.postgres.aio": None}):
        result = await chk_module.build_checkpointer()
    from langgraph.checkpoint.memory import MemorySaver
    assert isinstance(result, MemorySaver)


@pytest.mark.anyio
async def test_checkpointer_uses_postgres_when_available() -> None:
    from unittest.mock import AsyncMock, MagicMock, patch
    import job_agent.state.checkpointer as chk_module
    settings = MagicMock()
    settings.database_url = "postgresql+asyncpg://u:p@localhost/db"

    mock_saver = MagicMock()
    mock_saver.setup = AsyncMock()
    mock_pg_module = MagicMock()
    mock_pg_module.AsyncPostgresSaver.from_conn_string.return_value = mock_saver

    with patch.object(chk_module, "load_config", return_value=(settings, MagicMock())), \
         patch.dict("sys.modules", {"langgraph.checkpoint.postgres.aio": mock_pg_module}):
        result = await chk_module.build_checkpointer()

    mock_saver.setup.assert_awaited_once()
    assert result is mock_saver


def test_state_errors_accumulate() -> None:
    # Simulate reducer combining two partial states
    existing = ["error_a"]
    new = ["error_b"]
    combined = operator.add(existing, new)
    assert combined == ["error_a", "error_b"]
