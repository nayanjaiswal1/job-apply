from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from job_agent.db.models import (
    Application,
    Company,
    FollowUp,
    Job,
    Outreach,
    Question,
    ResumeVersion,
    UserProfile,
)
from job_agent.db.repositories.application_repo import ApplicationRepository
from job_agent.db.repositories.company_repo import CompanyRepository
from job_agent.db.repositories.followup_repo import FollowUpRepository
from job_agent.db.repositories.job_repo import JobRepository
from job_agent.db.repositories.outreach_repo import OutreachRepository
from job_agent.db.repositories.question_repo import QuestionRepository
from job_agent.db.repositories.resume_version_repo import ResumeVersionRepository
from job_agent.db.repositories.user_profile_repo import UserProfileRepository


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── Job ────────────────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_job_upsert_and_get(session: AsyncSession) -> None:
    repo = JobRepository(session)
    job = Job(
        id="abc123",
        title="Backend Engineer",
        company="Acme",
        location="Remote",
        platform="linkedin",
        url="https://example.com/job/1",
        jd_text="Python required",
        remote=True,
        exp_level="mid",
        status="discovered",
        source_type="api",
        posted_at=_now(),
    )
    await repo.upsert_job(job)
    fetched = await repo.get("abc123")
    assert fetched is not None
    assert fetched.title == "Backend Engineer"


@pytest.mark.anyio
async def test_job_upsert_is_idempotent(session: AsyncSession) -> None:
    repo = JobRepository(session)
    job = Job(id="dup1", title="Dev", company="Co", status="discovered")
    await repo.upsert_job(job)
    job.match_score = 0.9
    await repo.upsert_job(job)
    fetched = await repo.get("dup1")
    assert fetched is not None
    assert fetched.match_score == 0.9


@pytest.mark.anyio
async def test_job_list_by_status(session: AsyncSession) -> None:
    repo = JobRepository(session)
    for i in range(3):
        await repo.upsert_job(Job(id=f"s{i}", title="T", company="C", status="scored"))
    results = await repo.list_by_status("scored")
    assert len(results) >= 3


# ── Company ───────────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_company_upsert_and_get(session: AsyncSession) -> None:
    repo = CompanyRepository(session)
    company = Company(id="acme", name="Acme", summary='{"funding":"Series B"}', researched_at=_now())
    await repo.upsert(company)
    fetched = await repo.get("acme")
    assert fetched is not None
    assert fetched.summary == '{"funding":"Series B"}'


# ── Application ───────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_application_save_and_get(session: AsyncSession) -> None:
    job_repo = JobRepository(session)
    await job_repo.upsert_job(Job(id="j1", title="T", company="C", status="discovered"))

    repo = ApplicationRepository(session)
    app = Application(id="app1", job_id="j1", status="applied")
    await repo.save(app)
    fetched = await repo.get("app1")
    assert fetched is not None
    assert fetched.status == "applied"


@pytest.mark.anyio
async def test_application_update_status(session: AsyncSession) -> None:
    job_repo = JobRepository(session)
    await job_repo.upsert_job(Job(id="j2", title="T", company="C", status="discovered"))

    repo = ApplicationRepository(session)
    app = Application(id="app2", job_id="j2", status="applied")
    await repo.save(app)
    await repo.update_status("app2", "interview_scheduled")
    fetched = await repo.get("app2")
    assert fetched is not None
    assert fetched.status == "interview_scheduled"


# ── Outreach ──────────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_outreach_already_contacted(session: AsyncSession) -> None:
    repo = OutreachRepository(session)
    outreach = Outreach(id="o1", person="Alice", company="Acme", channel="email")
    await repo.save(outreach)
    assert await repo.already_contacted("Alice", "Acme") is True
    assert await repo.already_contacted("Bob", "Acme") is False


# ── Question ──────────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_question_save_and_list_by_job(session: AsyncSession) -> None:
    repo = QuestionRepository(session)
    q = Question(
        id="q1",
        text="What is async?",
        embedding=b"\x00" * 16,
        category="technical",
        source_jds='["job_xyz"]',
        confidence="unseen",
    )
    await repo.save(q)
    results = await repo.list_by_job("job_xyz")
    assert any(r.id == "q1" for r in results)


# ── ResumeVersion ─────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_resume_version_latest(session: AsyncSession) -> None:
    repo = ResumeVersionRepository(session)
    v1 = ResumeVersion(id="rv1", filename="resume_v1.pdf", ats_score=70.0)
    v2 = ResumeVersion(id="rv2", filename="resume_v2.pdf", ats_score=85.0)
    await repo.save(v1)
    await repo.save(v2)
    latest = await repo.latest()
    assert latest is not None
    assert latest.id in ("rv1", "rv2")


# ── UserProfile ───────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_user_profile_upsert_and_get(session: AsyncSession) -> None:
    repo = UserProfileRepository(session)
    profile = UserProfile(id="me", full_name="Test User", email="test@example.com")
    await repo.upsert(profile)
    fetched = await repo.get()
    assert fetched is not None
    assert fetched.full_name == "Test User"
    assert fetched.onboarding_step == 1


@pytest.mark.anyio
async def test_user_profile_preferences_json_roundtrip(session: AsyncSession) -> None:
    repo = UserProfileRepository(session)
    profile = UserProfile(id="me", full_name="Test User", email="test@example.com")
    await repo.upsert(profile)
    prefs = '{"remote": "remote", "max_applications_per_day": 5}'
    await repo.set_preferences(prefs)
    fetched = await repo.get()
    assert fetched is not None
    assert fetched.preferences == prefs


# ── FollowUp ──────────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_followup_roundtrip(session: AsyncSession) -> None:
    job_repo = JobRepository(session)
    await job_repo.upsert_job(Job(id="j3", title="T", company="C", status="discovered"))
    app_repo = ApplicationRepository(session)
    await app_repo.save(Application(id="app3", job_id="j3", status="applied"))

    repo = FollowUpRepository(session)
    fu = FollowUp(id="fu1", application_id="app3", day_offset=7, status="draft")
    await repo.save(fu)
    fetched = await repo.get("fu1")
    assert fetched is not None
    assert fetched.day_offset == 7

    results = await repo.list_by_application("app3")
    assert any(r.id == "fu1" for r in results)

    by_status = await repo.list_by_status("draft")
    assert any(r.id == "fu1" for r in by_status)


# ── Additional coverage for 100% on db repos ─────────────────────────────────

@pytest.mark.anyio
async def test_application_list_by_status(session: AsyncSession) -> None:
    job_repo = JobRepository(session)
    await job_repo.upsert_job(Job(id="jls1", title="T", company="C", status="discovered"))
    repo = ApplicationRepository(session)
    await repo.save(Application(id="als1", job_id="jls1", status="applied"))
    results = await repo.list_by_status("applied")
    assert any(r.id == "als1" for r in results)


@pytest.mark.anyio
async def test_company_upsert_updates_existing(session: AsyncSession) -> None:
    repo = CompanyRepository(session)
    c = Company(id="upd_co", name="Co", summary='{"v":1}', researched_at=_now())
    await repo.upsert(c)
    c.summary = '{"v":2}'
    await repo.upsert(c)
    fetched = await repo.get("upd_co")
    assert fetched is not None
    assert fetched.summary == '{"v":2}'


@pytest.mark.anyio
async def test_outreach_get_by_job(session: AsyncSession) -> None:
    job_repo = JobRepository(session)
    await job_repo.upsert_job(Job(id="jout1", title="T", company="C", status="discovered"))
    repo = OutreachRepository(session)
    await repo.save(Outreach(id="out2", job_id="jout1", person="Bob", company="Co", channel="email"))
    results = await repo.get_by_job("jout1")
    assert any(r.id == "out2" for r in results)


@pytest.mark.anyio
async def test_question_save_and_update(session: AsyncSession) -> None:
    repo = QuestionRepository(session)
    q = Question(id="qupd1", text="Test?", embedding=b"\x00" * 16, category="technical", source_jds='["j1"]', confidence="unseen")
    await repo.save(q)
    q.confidence = "shaky"
    await repo.update(q)
    fetched = await repo.get("qupd1")
    assert fetched is not None
    assert fetched.confidence == "shaky"


@pytest.mark.anyio
async def test_resume_version_save_get_and_list(session: AsyncSession) -> None:
    repo = ResumeVersionRepository(session)
    v = ResumeVersion(id="rv_list1", filename="resume.pdf", ats_score=80.0)
    await repo.save(v)
    fetched = await repo.get("rv_list1")
    assert fetched is not None
    assert fetched.filename == "resume.pdf"
    all_versions = await repo.list_all()
    assert any(r.id == "rv_list1" for r in all_versions)


@pytest.mark.anyio
async def test_user_profile_set_onboarding_step(session: AsyncSession) -> None:
    repo = UserProfileRepository(session)
    profile = UserProfile(id="me", full_name="Test", email="t@example.com")
    await repo.upsert(profile)
    await repo.set_onboarding_step(3)
    fetched = await repo.get()
    assert fetched is not None
    assert fetched.onboarding_step == 3
