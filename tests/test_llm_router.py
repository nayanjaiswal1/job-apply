from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from job_agent.config.models import AgentModelConfig, AppConfig, ChromaConfig, ModelConfig  # noqa: F401
from job_agent.errors import AgentError, RateLimited, TransientError
from job_agent.tools.llm_router import CostTracker, LLMRouter, _cache


def _make_app_config() -> AppConfig:
    agent_cfg = AgentModelConfig(primary="gpt-4o-mini", fallback="gpt-4o-mini", min_mode="gpt-4o-mini")
    models = ModelConfig(
        orchestrator=agent_cfg,
        resume_rewrite=agent_cfg,
        cover_letter=agent_cfg,
        job_scoring=agent_cfg,
        company_research=agent_cfg,
        referral_dm=agent_cfg,
        mail_classifier=agent_cfg,
        form_screening=agent_cfg,
        interview_prep=agent_cfg,
    )
    return AppConfig(chroma=ChromaConfig(), models=models)


def _mock_litellm_response(text: str = "ok") -> MagicMock:
    resp = MagicMock()
    resp.choices[0].message.content = text
    resp.usage.prompt_tokens = 10
    resp.usage.completion_tokens = 5
    return resp


@pytest.fixture(autouse=True)
def clear_cache():
    _cache.clear()
    yield
    _cache.clear()


@patch("job_agent.tools.llm_router.load_config")
def test_complete_success(mock_load_config) -> None:
    import litellm
    mock_load_config.return_value = (MagicMock(), _make_app_config())
    router = LLMRouter()

    with patch.object(litellm, "completion", return_value=_mock_litellm_response("hello")):
        result = router.complete("orchestrator", [{"role": "user", "content": "hi"}])

    assert not result.is_err()
    assert result.unwrap().text == "hello"
    assert result.unwrap().cache_hit is False


@patch("job_agent.tools.llm_router.load_config")
def test_cache_hit_on_repeat(mock_load_config) -> None:
    import litellm
    mock_load_config.return_value = (MagicMock(), _make_app_config())
    router = LLMRouter()
    messages = [{"role": "user", "content": "repeat"}]

    with patch.object(litellm, "completion", return_value=_mock_litellm_response("cached")) as mock_call:
        router.complete("orchestrator", messages)
        result = router.complete("orchestrator", messages)

    assert mock_call.call_count == 1
    assert result.unwrap().cache_hit is True


@patch("job_agent.tools.llm_router.load_config")
def test_fallback_on_rate_limit(mock_load_config) -> None:
    import litellm
    app_cfg = _make_app_config()
    app_cfg.models.orchestrator = AgentModelConfig(
        primary="gpt-4o-mini", fallback="gpt-4o", min_mode="gpt-4o-mini"
    )
    mock_load_config.return_value = (MagicMock(), app_cfg)
    router = LLMRouter()

    calls = [litellm.RateLimitError("rate limited", llm_provider="openai", model="gpt-4o-mini"), _mock_litellm_response("fallback")]

    with patch.object(litellm, "completion", side_effect=calls):
        result = router.complete("orchestrator", [{"role": "user", "content": "x"}])

    assert not result.is_err()
    assert result.unwrap().fallback_from is not None


@patch("job_agent.tools.llm_router.load_config")
def test_both_models_fail_returns_err(mock_load_config) -> None:
    import litellm
    mock_load_config.return_value = (MagicMock(), _make_app_config())
    router = LLMRouter()

    with patch.object(litellm, "completion", side_effect=litellm.ServiceUnavailableError("down", llm_provider="openai", model="x")):
        result = router.complete("orchestrator", [{"role": "user", "content": "x"}])

    assert result.is_err()
    assert isinstance(result.unwrap_err(), (TransientError, AgentError))


@patch("job_agent.tools.llm_router.load_config")
def test_minimize_uses_min_mode(mock_load_config) -> None:
    import litellm
    app_cfg = _make_app_config()
    app_cfg.models.orchestrator = AgentModelConfig(
        primary="claude-sonnet-4-6", fallback="gpt-4o", min_mode="gpt-4o-mini"
    )
    mock_load_config.return_value = (MagicMock(), app_cfg)
    router = LLMRouter(minimize=True)

    called_model: list[str] = []

    def capture(**kwargs):
        called_model.append(kwargs["model"])
        return _mock_litellm_response()

    with patch.object(litellm, "completion", side_effect=capture):
        router.complete("orchestrator", [{"role": "user", "content": "x"}])

    assert called_model[0] == "gpt-4o-mini"


@patch("job_agent.tools.llm_router.load_config")
def test_unknown_task_returns_err(mock_load_config) -> None:
    mock_load_config.return_value = (MagicMock(), _make_app_config())
    router = LLMRouter()
    result = router.complete("nonexistent_task", [])
    assert result.is_err()


@patch("job_agent.tools.llm_router.load_config")
def test_both_models_rate_limited_returns_err(mock_load_config) -> None:
    import litellm
    app_cfg = _make_app_config()
    app_cfg.models.orchestrator = AgentModelConfig(
        primary="gpt-4o-mini", fallback="gpt-4o", min_mode="gpt-4o-mini"
    )
    mock_load_config.return_value = (MagicMock(), app_cfg)
    router = LLMRouter()

    with patch.object(litellm, "completion", side_effect=litellm.RateLimitError("rate limited", llm_provider="openai", model="x")):
        result = router.complete("orchestrator", [{"role": "user", "content": "x"}])

    assert result.is_err()
    from job_agent.errors import RateLimited
    assert isinstance(result.unwrap_err(), RateLimited)


@patch("job_agent.tools.llm_router.load_config")
def test_service_unavailable_returns_err(mock_load_config) -> None:
    import litellm
    app_cfg = _make_app_config()
    app_cfg.models.orchestrator = AgentModelConfig(
        primary="gpt-4o-mini", fallback="gpt-4o", min_mode="gpt-4o-mini"
    )
    mock_load_config.return_value = (MagicMock(), app_cfg)
    router = LLMRouter()

    with patch.object(litellm, "completion", side_effect=litellm.ServiceUnavailableError("down", llm_provider="openai", model="x")):
        result = router.complete("orchestrator", [{"role": "user", "content": "x"}])

    assert result.is_err()
    from job_agent.errors import UpstreamUnavailable
    assert isinstance(result.unwrap_err(), UpstreamUnavailable)


@patch("job_agent.tools.llm_router.load_config")
def test_auth_error_returns_permanent_err(mock_load_config) -> None:
    import litellm
    mock_load_config.return_value = (MagicMock(), _make_app_config())
    router = LLMRouter()

    with patch.object(litellm, "completion", side_effect=litellm.AuthenticationError("bad key", llm_provider="openai", model="x")):
        result = router.complete("orchestrator", [{"role": "user", "content": "unique_auth_error_msg"}])

    assert result.is_err()
    from job_agent.errors import AgentError
    assert isinstance(result.unwrap_err(), AgentError)


@patch("job_agent.tools.llm_router.load_config")
def test_generic_exception_returns_transient_err(mock_load_config) -> None:
    import litellm
    app_cfg = _make_app_config()
    app_cfg.models.orchestrator = AgentModelConfig(
        primary="gpt-4o-mini", fallback="gpt-4o", min_mode="gpt-4o-mini"
    )
    mock_load_config.return_value = (MagicMock(), app_cfg)
    router = LLMRouter()

    with patch.object(litellm, "completion", side_effect=RuntimeError("unexpected error")):
        result = router.complete("orchestrator", [{"role": "user", "content": "unique_generic_err"}])

    assert result.is_err()
    from job_agent.errors import TransientError
    assert isinstance(result.unwrap_err(), TransientError)


def test_cost_tracker_records_cost() -> None:
    tracker = CostTracker()
    cost = tracker.record("claude-sonnet-4-6", tokens_in=1000, tokens_out=100)
    assert cost > Decimal("0")
    assert tracker.total == cost


def test_cost_tracker_unknown_model_zero_cost() -> None:
    tracker = CostTracker()
    cost = tracker.record("some-unknown-model", tokens_in=1000, tokens_out=100)
    assert cost == Decimal("0")
