from datetime import datetime, timezone

import pytest

from job_agent.services.dedup import DedupService, job_id
from job_agent.ports.scraper import Job


def _job(title="Dev", company="Co", location="Remote") -> Job:
    return Job(
        id=job_id(title, company, location),
        title=title,
        company=company,
        location=location,
        platform="linkedin",
        url="",
        jd_text="Python required",
        salary_range=None,
        remote=True,
        experience_level="mid",
        posted_at=datetime.now(timezone.utc),
        scraped_at=datetime.now(timezone.utc),
        match_score=0.0,
        status="discovered",
        source_type="api",
    )


def test_job_id_deterministic():
    id1 = job_id("Dev", "Co", "Remote")
    id2 = job_id("Dev", "Co", "Remote")
    assert id1 == id2


def test_job_id_case_insensitive():
    assert job_id("dev", "co", "remote") == job_id("Dev", "Co", "Remote")


def test_job_id_different_inputs_differ():
    assert job_id("Dev", "Co", "Remote") != job_id("QA", "Co", "Remote")


@pytest.mark.anyio
async def test_exact_duplicate_detected():
    svc = DedupService()
    job = _job()
    existing = {job.id}
    assert await svc.is_duplicate(job, existing) is True


@pytest.mark.anyio
async def test_new_job_not_duplicate():
    svc = DedupService()
    job = _job()
    assert await svc.is_duplicate(job, set()) is False


@pytest.mark.anyio
async def test_fuzzy_duplicate_detected():
    class MockEmbedder:
        async def embed(self, text: str) -> list[float]:
            return [1.0, 0.0, 0.0]

        def cosine_similarity(self, a: list[float], b: list[float]) -> float:
            return 0.95  # above threshold

    svc = DedupService(embedder=MockEmbedder())
    job = _job(title="New Job")
    existing_embeddings = [("other_id", [1.0, 0.0, 0.0])]
    assert await svc.is_duplicate(job, set(), existing_embeddings) is True


@pytest.mark.anyio
async def test_fuzzy_non_duplicate_below_threshold():
    class MockEmbedder:
        async def embed(self, text: str) -> list[float]:
            return [1.0, 0.0, 0.0]

        def cosine_similarity(self, a: list[float], b: list[float]) -> float:
            return 0.80  # below 0.92 threshold

    svc = DedupService(embedder=MockEmbedder())
    job = _job(title="Different Job")
    existing_embeddings = [("other_id", [0.0, 1.0, 0.0])]
    assert await svc.is_duplicate(job, set(), existing_embeddings) is False
