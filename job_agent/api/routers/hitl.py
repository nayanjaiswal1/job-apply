from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/approvals", tags=["hitl"])


class ResumeApproval(BaseModel):
    version_id: str
    edited_text: str | None = None
    approved: bool = True


class CoverApproval(BaseModel):
    body: str
    approved: bool = True


class OutreachApproval(BaseModel):
    approved_ids: list[str]
    skipped_ids: list[str] = []


class FollowUpApproval(BaseModel):
    followup_id: str
    approved: bool = True


@router.post("/resume/{version_id}")
async def approve_resume(version_id: str, body: ResumeApproval) -> dict[str, Any]:
    from job_agent.db.repositories.resume_version_repo import ResumeVersionRepository
    from job_agent.db.session import get_session
    async with get_session() as session:
        repo = ResumeVersionRepository(session)
        version = await repo.get(version_id)
        if version is None:
            raise HTTPException(status_code=404, detail="Resume version not found")
        if body.edited_text:
            import json
            existing = json.loads(version.sections or "{}")
            existing["raw_text"] = body.edited_text
            version.sections = json.dumps(existing)
    return {"approved": body.approved, "version_id": version_id}


@router.post("/followup/{followup_id}")
async def approve_followup(followup_id: str, body: FollowUpApproval) -> dict[str, Any]:
    from job_agent.db.repositories.followup_repo import FollowUpRepository
    from job_agent.db.session import get_session
    async with get_session() as session:
        repo = FollowUpRepository(session)
        fu = await repo.get(followup_id)
        if fu is None:
            raise HTTPException(status_code=404, detail="Follow-up not found")
        fu.status = "approved" if body.approved else "skipped"
    return {"followup_id": followup_id, "status": fu.status}


@router.get("/queue/dlq")
async def get_dlq() -> list[dict[str, Any]]:
    import os
    from job_agent.queue.dlq import DeadLetterQueue
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    dlq = DeadLetterQueue(redis_url)
    return await dlq.list_entries()
