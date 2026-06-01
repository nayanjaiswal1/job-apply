from datetime import datetime, timezone

import pytest

from job_agent.models.preferences import Preferences
from job_agent.ports.scraper import Job
from job_agent.services.pre_filter import passes_pre_filter


def _job(**kwargs) -> Job:
    defaults = dict(
        id="x",
        title="Python Developer",
        company="Acme",
        location="Bangalore, India",
        platform="linkedin",
        url="",
        jd_text="Python, FastAPI",
        salary_range=None,
        remote=False,
        experience_level="mid",
        posted_at=datetime.now(timezone.utc),
        scraped_at=datetime.now(timezone.utc),
        match_score=0.0,
        status="discovered",
        source_type="api",
    )
    defaults.update(kwargs)
    return Job(**defaults)


def _prefs(**kwargs) -> Preferences:
    return Preferences(**kwargs)


def test_passes_empty_prefs():
    assert passes_pre_filter(_job(), _prefs()) is True


def test_blacklist_company_blocks():
    assert passes_pre_filter(_job(company="BadCorp"), _prefs(blacklist_companies=["BadCorp"])) is False


def test_blacklist_company_case_insensitive():
    assert passes_pre_filter(_job(company="badcorp"), _prefs(blacklist_companies=["BadCorp"])) is False


def test_blacklist_keyword_in_title():
    assert passes_pre_filter(_job(title="Senior Java Developer"), _prefs(blacklist_keywords=["Java"])) is False


def test_blacklist_keyword_in_jd():
    assert passes_pre_filter(_job(jd_text="Must know Java"), _prefs(blacklist_keywords=["Java"])) is False


def test_blacklist_keyword_not_present_passes():
    assert passes_pre_filter(_job(), _prefs(blacklist_keywords=["Java"])) is True


def test_remote_filter_blocks_onsite_job():
    assert passes_pre_filter(_job(remote=False), _prefs(remote="remote")) is False


def test_remote_filter_allows_remote_job():
    assert passes_pre_filter(_job(remote=True), _prefs(remote="remote")) is True


def test_remote_any_allows_all():
    assert passes_pre_filter(_job(remote=False), _prefs(remote="any")) is True
    assert passes_pre_filter(_job(remote=True), _prefs(remote="any")) is True


def test_role_level_filter():
    assert passes_pre_filter(_job(experience_level="senior"), _prefs(role_levels=["junior", "mid"])) is False
    assert passes_pre_filter(_job(experience_level="mid"), _prefs(role_levels=["junior", "mid"])) is True


def test_location_filter_blocks_non_matching_onsite():
    assert passes_pre_filter(
        _job(location="Mumbai", remote=False),
        _prefs(preferred_locations=["Bangalore"]),
    ) is False


def test_location_filter_allows_remote_regardless():
    assert passes_pre_filter(
        _job(location="Mumbai", remote=True),
        _prefs(preferred_locations=["Bangalore"]),
    ) is True
