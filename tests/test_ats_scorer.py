from job_agent.tools.ats_scorer import score


def test_high_match_scores_above_85():
    # Resume and JD share the same keyword set — score should be very high
    keywords = "Python FastAPI PostgreSQL Redis Docker asyncio SQLAlchemy testing deployment"
    assert score(keywords, keywords) > 85


def test_low_match_scores_below_40():
    resume = "Java Spring Boot Oracle Hibernate JEE enterprise"
    jd = "Python FastAPI PostgreSQL Redis Docker asyncio React TypeScript"
    assert score(resume, jd) < 40


def test_empty_jd_returns_zero():
    assert score("Python developer", "") == 0.0


def test_score_is_capped_at_100():
    text = "python fastapi postgres redis docker celery asyncio sqlalchemy rest api github actions kubernetes"
    assert score(text, text) <= 100.0


def test_section_headers_add_bonus():
    with_sections = "Experience\nPython developer\nEducation\nBS Computer Science\nSkills\nPython"
    without_sections = "Python developer BS Computer Science Python"
    jd = "Python developer"
    assert score(with_sections, jd) >= score(without_sections, jd)
