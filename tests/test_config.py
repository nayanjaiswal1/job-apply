from pathlib import Path

import pytest
import yaml

from job_agent.config.models import AppConfig


def _write_config(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "config.yaml"
    p.write_text(yaml.dump(data))
    return p


def _minimal_models_dict() -> dict:
    agents = [
        "orchestrator", "resume_rewrite", "cover_letter", "job_scoring",
        "company_research", "referral_dm", "mail_classifier", "form_screening",
        "interview_prep",
    ]
    return {
        "models": {
            a: {"primary": "gpt-4o-mini", "fallback": "gpt-4o-mini", "min_mode": "gpt-4o-mini"}
            for a in agents
        }
    }


def test_valid_config_loads(tmp_path: Path) -> None:
    data = {
        "chroma": {
            "job_embeddings_collection": "job_embeddings",
            "question_embeddings_collection": "question_embeddings",
        },
        **_minimal_models_dict(),
    }
    cfg_path = _write_config(tmp_path, data)
    raw = yaml.safe_load(cfg_path.read_text())
    config = AppConfig.model_validate(raw)
    assert config.chroma.job_embeddings_collection == "job_embeddings"
    assert config.chroma.question_embeddings_collection == "question_embeddings"


def test_chroma_collection_names_loaded(tmp_path: Path) -> None:
    data = {
        "chroma": {
            "job_embeddings_collection": "custom_jobs",
            "question_embeddings_collection": "custom_questions",
        },
        **_minimal_models_dict(),
    }
    cfg_path = _write_config(tmp_path, data)
    raw = yaml.safe_load(cfg_path.read_text())
    config = AppConfig.model_validate(raw)
    assert config.chroma.job_embeddings_collection == "custom_jobs"
    assert config.chroma.question_embeddings_collection == "custom_questions"


def test_missing_models_rejected(tmp_path: Path) -> None:
    cfg_path = _write_config(tmp_path, {"chroma": {"job_embeddings_collection": "x"}})
    raw = yaml.safe_load(cfg_path.read_text())
    with pytest.raises(Exception):
        AppConfig.model_validate(raw)


def test_invalid_yaml_rejected(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text("key: [unclosed")
    with pytest.raises(yaml.YAMLError):
        yaml.safe_load(cfg_path.read_text())


def test_model_config_per_agent(tmp_path: Path) -> None:
    cfg_path = _write_config(tmp_path, _minimal_models_dict())
    raw = yaml.safe_load(cfg_path.read_text())
    config = AppConfig.model_validate(raw)
    assert config.models.orchestrator.primary == "gpt-4o-mini"
    assert config.models.orchestrator.fallback == "gpt-4o-mini"
    assert config.models.orchestrator.min_mode == "gpt-4o-mini"


def test_schedule_defaults(tmp_path: Path) -> None:
    cfg_path = _write_config(tmp_path, _minimal_models_dict())
    raw = yaml.safe_load(cfg_path.read_text())
    config = AppConfig.model_validate(raw)
    assert config.schedule.job_search_interval_hours == 6
    assert config.schedule.mail_watcher_interval_minutes == 30


def test_load_config_reads_file(tmp_path: Path) -> None:
    from job_agent.config.loader import load_config
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml.dump(_minimal_models_dict()))
    # Clear lru_cache so we get a fresh call
    load_config.cache_clear()
    import os
    old = os.environ.get("DATABASE_URL", "")
    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    os.environ.setdefault("APP_API_KEY", "test")
    os.environ.setdefault("SECRET_KEY", "test")
    try:
        settings, config = load_config(cfg_path)
        assert config.models.orchestrator.primary == "gpt-4o-mini"
    finally:
        load_config.cache_clear()
        if not old:
            os.environ.pop("DATABASE_URL", None)
