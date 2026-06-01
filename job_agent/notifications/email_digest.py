from __future__ import annotations

from typing import Any

from jinja2 import Environment, FileSystemLoader
from pathlib import Path

_TMPL_DIR = Path(__file__).parent / "templates"
_env = Environment(loader=FileSystemLoader(str(_TMPL_DIR)), autoescape=True)


def render_digest(stats: dict[str, Any]) -> tuple[str, str]:
    """Returns (html, plain_text)."""
    try:
        html = _env.get_template("digest.html").render(**stats)
    except Exception:
        html = f"<pre>{stats}</pre>"

    lines = [
        "Job Agent Daily Digest",
        "======================",
        f"Jobs found today:    {stats.get('jobs_found', 0)}",
        f"Applications sent:   {stats.get('applications', 0)}",
        f"Replies received:    {stats.get('replies', 0)}",
        f"Follow-ups pending:  {stats.get('followups_pending', 0)}",
        f"Interviews scheduled:{stats.get('interviews', 0)}",
    ]
    return html, "\n".join(lines)
