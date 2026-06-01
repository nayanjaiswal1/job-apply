from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from job_agent.graph import _HITL_NODES, build_graph


def test_graph_compiles() -> None:
    with patch("job_agent.graph.StateGraph") as mock_sg:
        mock_builder = MagicMock()
        mock_sg.return_value = mock_builder
        mock_builder.compile.return_value = MagicMock()
        graph = build_graph()
        assert graph is mock_builder


def test_hitl_nodes_defined() -> None:
    assert "resume_hitl" in _HITL_NODES
    assert "cover_letter_hitl" in _HITL_NODES
    assert "outreach_hitl" in _HITL_NODES
    assert "apply_confirm" in _HITL_NODES
    assert "referral_hitl" in _HITL_NODES
    assert "followup_hitl" in _HITL_NODES
    assert "captcha_hitl" in _HITL_NODES
    assert len(_HITL_NODES) == 7


def test_graph_builds_without_error() -> None:
    # Verifies all 12 nodes + 7 HITL stubs are added without raising
    builder = build_graph()
    assert builder is not None
