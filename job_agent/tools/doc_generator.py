from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Literal

import structlog
from jinja2 import Environment, FileSystemLoader

log = structlog.get_logger()

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
_env = Environment(loader=FileSystemLoader(str(_TEMPLATES_DIR)), autoescape=False)

_ATS_TXT_RE = re.compile(r"<[^>]+>")


async def _html_to_pdf(html: str, margins: dict[str, str] | None = None) -> bytes:
    from playwright.async_api import async_playwright
    margins = margins or {"top": "0.75in", "bottom": "0.75in", "left": "0.75in", "right": "0.75in"}
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page()
        await page.set_content(html, wait_until="networkidle")
        pdf = await page.pdf(format="A4", print_background=True, margin=margins)
        await browser.close()
    return pdf


def _render_ats_txt(data: dict[str, Any]) -> str:
    lines = [
        data.get("name", ""),
        " | ".join(filter(None, [data.get("email"), data.get("phone"), data.get("linkedin")])),
        "",
    ]
    if data.get("summary"):
        lines += ["SUMMARY", data["summary"], ""]
    if data.get("experience"):
        lines.append("EXPERIENCE")
        lines.append("")
        for job in data["experience"]:
            end = job.get("end") or "Present"
            lines.append(f"{job['title']} — {job['company']} ({job.get('start', '')} – {end})")
            for bullet in job.get("bullets", []):
                lines.append(f"- {bullet}")
            lines.append("")
    if data.get("education"):
        lines.append("EDUCATION")
        lines.append("")
        for edu in data["education"]:
            lines.append(f"{edu['degree']}, {edu['school']}{' (' + edu['year'] + ')' if edu.get('year') else ''}")
        lines.append("")
    if data.get("skills"):
        lines += ["SKILLS", ", ".join(data["skills"]), ""]
    return "\n".join(lines)


async def render_resume(
    data: dict[str, Any],
    fmt: Literal["ats_plain", "human_readable", "one_pager"] = "ats_plain",
) -> tuple[bytes, str]:
    """Returns (pdf_bytes, plain_txt)."""
    template_name = f"resume/{fmt}.html" if fmt != "one_pager" else "resume/human_readable.html"
    template = _env.get_template(template_name)
    html = template.render(**data)
    if fmt == "one_pager":
        one_pager_css = """<style>
        @page { margin: 0.45in 0.5in; }
        body { font-size: 9.5pt; }
        h1.name { font-size: 18pt; }
        .section-header { font-size: 9.5pt; margin-top: 8pt; }
        li { line-height: 1.3; margin-bottom: 1pt; }
        </style>"""
        html = html.replace("</head>", f"{one_pager_css}</head>")
    pdf = await _html_to_pdf(html)
    txt = _render_ats_txt(data)
    return pdf, txt


async def render_cover_letter(
    body: str,
    profile: dict[str, Any],
    salutation: str = "Dear Hiring Manager,",
) -> bytes:
    """Returns pdf_bytes."""
    from datetime import datetime
    template = _env.get_template("cover_letter/cover_letter.html")
    html = template.render(
        name=profile.get("full_name", ""),
        email=profile.get("email", ""),
        phone=profile.get("phone"),
        linkedin=profile.get("linkedin_url"),
        date=datetime.now().strftime("%B %-d, %Y") if hasattr(datetime.now(), "strftime") else "",
        salutation=salutation,
        letter_body=body,
    )
    return await _html_to_pdf(html, {"top": "1in", "bottom": "1in", "left": "1in", "right": "1in"})


async def render_prep_markdown(job_id: str, questions: list[dict[str, Any]]) -> str:
    """Returns markdown of all prep questions for a job."""
    lines = [f"# Interview Prep — {job_id}\n"]
    for q in questions:
        lines.append(f"## {q.get('text', '')}")
        if q.get("model_answer"):
            lines.append(f"\n{q['model_answer']}")
        lines.append("")
    return "\n".join(lines)


async def render_anki_csv(job_id: str, questions: list[dict[str, Any]]) -> str:
    """Returns Anki-format CSV (Question, Answer, Tags, Difficulty)."""
    rows = ['"Question","Answer","Tags","Difficulty"']
    for q in questions:
        text = q.get("text", "").replace('"', '""')
        answer = (q.get("model_answer") or "").replace('"', '""')
        tags = "|".join(q.get("tags", []) if isinstance(q.get("tags"), list) else [])
        difficulty = q.get("difficulty", "")
        rows.append(f'"{text}","{answer}","{tags}","{difficulty}"')
    return "\n".join(rows)
