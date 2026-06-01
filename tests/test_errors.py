import pytest

from job_agent.errors import (
    AgentError,
    HumanReviewNeeded,
    PermanentError,
    RateLimited,
    TransientError,
    UpstreamUnavailable,
)
from job_agent.util.result import Result
from job_agent.util.retry import retry_transient


def test_error_hierarchy() -> None:
    assert issubclass(TransientError, AgentError)
    assert issubclass(PermanentError, AgentError)
    assert issubclass(HumanReviewNeeded, AgentError)
    assert issubclass(RateLimited, TransientError)
    assert issubclass(UpstreamUnavailable, TransientError)


def test_result_ok() -> None:
    r: Result[int, AgentError] = Result.ok(42)
    assert not r.is_err()
    assert r.unwrap() == 42


def test_result_err() -> None:
    err = AgentError("fail")
    r: Result[int, AgentError] = Result.err(err)
    assert r.is_err()
    with pytest.raises(AgentError):
        r.unwrap()


def test_result_map_ok() -> None:
    r: Result[int, AgentError] = Result.ok(10)
    mapped = r.map(lambda x: x * 2)
    assert mapped.unwrap() == 20


def test_result_map_err_passthrough() -> None:
    err = AgentError("fail")
    r: Result[int, AgentError] = Result.err(err)
    mapped = r.map(lambda x: x * 2)
    assert mapped.is_err()


def test_retry_stops_on_permanent_error() -> None:
    call_count = 0

    @retry_transient(max_attempts=3)
    def always_permanent() -> None:
        nonlocal call_count
        call_count += 1
        raise PermanentError("permanent")

    with pytest.raises(PermanentError):
        always_permanent()

    assert call_count == 1


def test_retry_retries_transient_error() -> None:
    call_count = 0

    @retry_transient(max_attempts=3, min_wait=0.0, max_wait=0.01)
    def sometimes_transient() -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise TransientError("retry me")
        return "ok"

    result = sometimes_transient()
    assert result == "ok"
    assert call_count == 3
