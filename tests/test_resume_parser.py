import textwrap
from pathlib import Path

import pytest

from job_agent.tools.resume_parser import Resume, _parse_text


def _resume_from_text(text: str) -> Resume:
    return _parse_text(textwrap.dedent(text))


def test_skills_extracted():
    resume = _resume_from_text("""
        Skills
        Python, FastAPI, PostgreSQL, Redis, Docker
    """)
    assert "Python" in resume.skills
    assert "Docker" in resume.skills


def test_summary_extracted():
    resume = _resume_from_text("""
        Summary
        Experienced backend engineer with 4 years of Python development.

        Skills
        Python, SQL
    """)
    assert "backend engineer" in resume.summary.lower()


def test_links_extracted():
    resume = _resume_from_text("""
        Skills
        Python

        https://github.com/testuser
        https://linkedin.com/in/testuser
    """)
    assert any("github.com" in l for l in resume.links)


def test_certifications_extracted():
    resume = _resume_from_text("""
        Certifications
        AWS Certified Solutions Architect
        Google Cloud Professional
    """)
    assert any("AWS" in c for c in resume.certifications)


def test_empty_text_returns_empty_resume():
    resume = _parse_text("")
    assert resume.skills == []
    assert resume.experience == []
    assert resume.summary == ""


def test_raw_text_preserved():
    text = "Skills\nPython, SQL"
    resume = _parse_text(text)
    assert "Python" in resume.raw_text


def test_missing_optional_fields_no_crash(tmp_path: Path):
    # A minimal PDF-like scenario — just test the text parser doesn't crash
    resume = _resume_from_text("""
        John Doe
        john@example.com
    """)
    assert isinstance(resume, Resume)


def test_parse_rejects_unsupported_extension(tmp_path: Path):
    from job_agent.tools.resume_parser import parse
    bad_file = tmp_path / "resume.xyz"
    bad_file.write_text("content")
    with pytest.raises(ValueError, match="Unsupported"):
        parse(bad_file)
