from __future__ import annotations

import re
from pathlib import Path
from typing import IO

import structlog
from pydantic import BaseModel, Field

log = structlog.get_logger()


class ExperienceEntry(BaseModel):
    title: str
    company: str
    location: str = ""
    start: str = ""
    end: str = ""
    bullets: list[str] = Field(default_factory=list)


class EducationEntry(BaseModel):
    degree: str
    school: str
    year: str = ""
    gpa: str | None = None


class Resume(BaseModel):
    summary: str = ""
    skills: list[str] = Field(default_factory=list)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)
    raw_text: str = ""


def parse(path: Path) -> Resume:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _parse_pdf(path)
    if suffix in (".docx", ".doc"):
        return _parse_docx(path)
    raise ValueError(f"Unsupported format: {suffix}")


def _parse_pdf(path: Path) -> Resume:
    text = _extract_pdf_text(path)
    return _parse_text(text)


def _extract_pdf_text(path: Path) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(str(path)) as pdf:
            pages = [p.extract_text() or "" for p in pdf.pages]
            text = "\n".join(pages)
            if text.strip():
                return text
    except Exception as exc:
        log.warning("pdfplumber_failed", reason=str(exc), path=str(path))

    # Fallback: pymupdf (handles scanned / complex layouts)
    try:
        import fitz  # pymupdf
        doc = fitz.open(str(path))
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        return text
    except Exception as exc:
        log.warning("pymupdf_failed", reason=str(exc), path=str(path))

    return ""


def _parse_docx(path: Path) -> Resume:
    try:
        import docx
        doc = docx.Document(str(path))
        text = "\n".join(p.text for p in doc.paragraphs)
        return _parse_text(text)
    except Exception as exc:
        log.warning("docx_parse_failed", reason=str(exc))
        return Resume()


# ── Text → structured Resume ──────────────────────────────────────────────────

_SECTION_HEADERS = {
    "summary": re.compile(r"^\s*(summary|profile|objective|about)\s*$", re.I),
    "experience": re.compile(r"^\s*(experience|work experience|employment|work history)\s*$", re.I),
    "education": re.compile(r"^\s*(education|academic|qualifications)\s*$", re.I),
    "skills": re.compile(r"^\s*(skills|technical skills|core competencies|technologies)\s*$", re.I),
    "certifications": re.compile(r"^\s*(certifications?|certificates?|licenses?)\s*$", re.I),
}

_URL_RE = re.compile(r"https?://\S+|linkedin\.com/\S+|github\.com/\S+")
_BULLET_RE = re.compile(r"^[•‣◦⁃\-\*\+]\s+")
_DATE_RE = re.compile(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|20\d\d|19\d\d|present|current)\b", re.I)


def _parse_text(text: str) -> Resume:
    lines = [l.rstrip() for l in text.splitlines()]
    resume = Resume(raw_text=text)
    resume.links = _URL_RE.findall(text)

    current_section = "preamble"
    section_lines: dict[str, list[str]] = {s: [] for s in _SECTION_HEADERS}
    section_lines["preamble"] = []

    for line in lines:
        matched = False
        for section, pattern in _SECTION_HEADERS.items():
            if pattern.match(line):
                current_section = section
                matched = True
                break
        if not matched and current_section in section_lines:
            section_lines[current_section].append(line)

    resume.summary = " ".join(l for l in section_lines.get("summary", []) if l.strip())[:500]

    skills_text = " ".join(section_lines.get("skills", []))
    resume.skills = [s.strip() for s in re.split(r"[,|•·/]", skills_text) if s.strip()][:50]

    resume.certifications = [
        l.strip() for l in section_lines.get("certifications", []) if l.strip()
    ]

    resume.experience = _parse_experience(section_lines.get("experience", []))
    resume.education = _parse_education(section_lines.get("education", []))

    return resume


def _parse_experience(lines: list[str]) -> list[ExperienceEntry]:
    entries: list[ExperienceEntry] = []
    current: ExperienceEntry | None = None
    for line in lines:
        if not line.strip():
            continue
        if _BULLET_RE.match(line):
            if current:
                current.bullets.append(_BULLET_RE.sub("", line).strip())
        elif _DATE_RE.search(line) and current is None or (current and not current.start):
            # Likely a job header line — parse title / company / dates
            parts = re.split(r"\s{2,}|\t|\|", line)
            if len(parts) >= 2:
                if current:
                    entries.append(current)
                current = ExperienceEntry(title=parts[0].strip(), company=parts[1].strip())
                if len(parts) >= 3:
                    current.start = parts[2].strip()
                if len(parts) >= 4:
                    current.end = parts[3].strip()
            elif current:
                current.bullets.append(line.strip())
        else:
            if current is None:
                current = ExperienceEntry(title=line.strip(), company="")
            else:
                current.bullets.append(line.strip())
    if current:
        entries.append(current)
    return entries


def _parse_education(lines: list[str]) -> list[EducationEntry]:
    entries: list[EducationEntry] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = re.split(r"\s{2,}|\t|\|", line)
        if len(parts) >= 2:
            entries.append(EducationEntry(degree=parts[0].strip(), school=parts[1].strip()))
        elif line:
            entries.append(EducationEntry(degree=line, school=""))
    return entries
