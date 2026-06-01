from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from job_agent.db.repositories.application_repo import ApplicationRepository
from job_agent.db.session import get_session
from job_agent.services.application_state import transition

router = APIRouter(prefix="/api/v1", tags=["applications"])


class StatusPatch(BaseModel):
    status: str


@router.get("/applications")
async def list_applications() -> list[dict[str, Any]]:
    async with get_session() as session:
        from sqlalchemy import select
        from job_agent.db.models import Application
        result = await session.execute(select(Application).limit(200))
        apps = list(result.scalars().all())
    return [_app_dict(a) for a in apps]


@router.patch("/applications/{app_id}/status")
async def patch_status(app_id: str, body: StatusPatch) -> dict[str, Any]:
    async with get_session() as session:
        repo = ApplicationRepository(session)
        app = await repo.get(app_id)
        if app is None:
            raise HTTPException(status_code=404, detail="Application not found")
        try:
            new_status = transition(app.status, body.status)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        await repo.update_status(app_id, new_status)
        return {"id": app_id, "status": new_status}


def _app_dict(a) -> dict[str, Any]:
    return {
        "id": a.id, "job_id": a.job_id, "status": a.status,
        "resume_version": a.resume_version,
        "sent_at": a.sent_at.isoformat() if a.sent_at else None,
        "last_reply_at": a.last_reply_at.isoformat() if a.last_reply_at else None,
        "submit_screenshot": a.submit_screenshot,
    }
