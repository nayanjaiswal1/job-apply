from functools import lru_cache
from pathlib import Path

import yaml

from job_agent.config.models import AppConfig
from job_agent.config.settings import Settings


@lru_cache(maxsize=1)
def load_config(config_path: Path = Path("config.yaml")) -> tuple[Settings, AppConfig]:
    raw = yaml.safe_load(config_path.read_text())
    return Settings(), AppConfig.model_validate(raw)
