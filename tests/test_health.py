from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from job_agent.api.main import app

client = TestClient(app)


def test_health_all_ok() -> None:
    with (
        patch("job_agent.api.health._check_db", new=AsyncMock(return_value=True)),
        patch("job_agent.api.health._check_redis", new=AsyncMock(return_value=True)),
        patch("job_agent.api.health._check_chroma", new=AsyncMock(return_value=True)),
    ):
        response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["db"] == "ok"
    assert data["redis"] == "ok"
    assert data["chroma"] == "ok"


def test_health_db_down_returns_503() -> None:
    with (
        patch("job_agent.api.health._check_db", new=AsyncMock(return_value=False)),
        patch("job_agent.api.health._check_redis", new=AsyncMock(return_value=True)),
        patch("job_agent.api.health._check_chroma", new=AsyncMock(return_value=True)),
    ):
        response = client.get("/health")
    assert response.status_code == 503
    assert response.json()["db"] == "fail"


def test_health_redis_down_returns_503() -> None:
    with (
        patch("job_agent.api.health._check_db", new=AsyncMock(return_value=True)),
        patch("job_agent.api.health._check_redis", new=AsyncMock(return_value=False)),
        patch("job_agent.api.health._check_chroma", new=AsyncMock(return_value=True)),
    ):
        response = client.get("/health")
    assert response.status_code == 503


def test_health_chroma_down_still_200() -> None:
    with (
        patch("job_agent.api.health._check_db", new=AsyncMock(return_value=True)),
        patch("job_agent.api.health._check_redis", new=AsyncMock(return_value=True)),
        patch("job_agent.api.health._check_chroma", new=AsyncMock(return_value=False)),
    ):
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["chroma"] == "fail"
