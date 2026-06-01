import os
from pathlib import Path

import pytest

from job_agent.tools.session_store import SessionStore


@pytest.fixture()
def store(tmp_path: Path) -> SessionStore:
    os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unit-tests")
    return SessionStore(sessions_dir=tmp_path)


def test_save_and_load(store: SessionStore) -> None:
    cookies = {"session_id": "abc123", "csrf": "xyz"}
    store.save("linkedin", cookies)
    loaded = store.load("linkedin")
    assert loaded == cookies


def test_load_nonexistent_returns_none(store: SessionStore) -> None:
    assert store.load("naukri") is None


def test_delete_removes_file(store: SessionStore, tmp_path: Path) -> None:
    store.save("wellfound", {"token": "t"})
    store.delete("wellfound")
    assert store.load("wellfound") is None


def test_different_platforms_independent(store: SessionStore) -> None:
    store.save("linkedin", {"a": "1"})
    store.save("naukri", {"b": "2"})
    assert store.load("linkedin") == {"a": "1"}
    assert store.load("naukri") == {"b": "2"}


def test_corrupted_data_returns_none(store: SessionStore, tmp_path: Path) -> None:
    (tmp_path / "linkedin.enc").write_bytes(b"garbage_data_not_valid_ciphertext")
    assert store.load("linkedin") is None
