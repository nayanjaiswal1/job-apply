from pathlib import Path

_REQUIRED_DIRS = [
    Path("data/resumes"),
    Path("data/cover_letters"),
    Path("logs/screenshots"),
]


def ensure_dirs() -> None:
    for d in _REQUIRED_DIRS:
        d.mkdir(parents=True, exist_ok=True)
