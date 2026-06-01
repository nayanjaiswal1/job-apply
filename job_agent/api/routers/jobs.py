from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from job_agent.db.repositories.job_repo import JobRepository
from job_agent.db.session import get_session

router = APIRouter(prefix="/api/v1", tags=["jobs"])


@router.get("/jobs")
async def list_jobs(
    status: str | None = Query(None),
    platform: str | None = Query(None),
    limit: int = Query(50, le=200),
) -> list[dict[str, Any]]:
    async with get_session() as session:
        repo = JobRepository(session)
        if status:
            jobs = await repo.list_by_status(status, limit=limit)
        else:
            from sqlalchemy import select
            from job_agent.db.models import Job
            result = await session.execute(select(Job).limit(limit))
            jobs = list(result.scalars().all())
    return [_job_dict(j) for j in jobs]


@router.get("/jobs/{job_id}")
async def get_job(job_id: str) -> dict[str, Any]:
    from fastapi import HTTPException
    async with get_session() as session:
        repo = JobRepository(session)
        job = await repo.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return _job_dict(job)


def _job_dict(j) -> dict[str, Any]:
    return {
        "id": j.id, "title": j.title, "company": j.company,
        "location": j.location, "platform": j.platform, "url": j.url,
        "remote": j.remote, "exp_level": j.exp_level, "match_score": j.match_score,
        "status": j.status, "source_type": j.source_type,
        "posted_at": j.posted_at.isoformat() if j.posted_at else None,
    }
