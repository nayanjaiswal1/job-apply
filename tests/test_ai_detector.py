import pytest

from job_agent.tools.ai_detector import _pattern_score, score


def test_obvious_ai_text_high_score():
    ai_text = (
        "Spearheaded the leveraging of orchestrated synergies — "
        "championed the facilitation of streamlined processes. "
        "Revolutionized the utilized framework."
    )
    s = _pattern_score(ai_text)
    assert s > 0.5


def test_clean_human_text_low_score():
    human_text = (
        "Built the payments API using FastAPI and Postgres. "
        "Cut latency from 420ms to 180ms by adding Redis caching. "
        "Wrote 95% test coverage on the billing module."
    )
    s = _pattern_score(human_text)
    assert s < 0.5


def test_em_dash_increases_score():
    text_with = "Built system — reduced latency — improved throughput"
    text_without = "Built system. Reduced latency. Improved throughput."
    assert _pattern_score(text_with) > _pattern_score(text_without)


@pytest.mark.anyio
async def test_api_outage_falls_back_to_pattern():
    # gptzero not installed → should return pattern score without raising
    text = "Built the payments API using FastAPI."
    result = await score(text)
    assert 0.0 <= result <= 1.0
