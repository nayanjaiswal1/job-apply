from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from job_agent.db.models import UserProfile
from job_agent.db.repositories.user_profile_repo import UserProfileRepository
from job_agent.db.session import get_session
from job_agent.models.preferences import Preferences

router = APIRouter(prefix="/api/v1", tags=["profile"])


class ProfileIn(BaseModel):
    full_name: str
    email: str
    phone: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    current_title: str | None = None
    current_company: str | None = None
    years_exp: int | None = None
    notice_period: str | None = None
    current_location: str | None = None
    target_locations: list[str] | None = None
    expected_salary: int | None = None
    currency: str = "INR"


class ProfileOut(ProfileIn):
    onboarding_step: int
    preferences: dict[str, Any] | None = None


@router.get("/profile", response_model=ProfileOut)
async def get_profile():
    async with get_session() as session:
        repo = UserProfileRepository(session)
        profile = await repo.get()
        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")
        return _to_out(profile)


@router.put("/profile", response_model=ProfileOut)
async def update_profile(data: ProfileIn):
    async with get_session() as session:
        repo = UserProfileRepository(session)
        existing = await repo.get()
        if existing is None:
            profile = UserProfile(id="me", **data.model_dump(exclude_none=False))
        else:
            for k, v in data.model_dump(exclude_none=True).items():
                setattr(existing, k, v)
            profile = existing
        if data.target_locations is not None:
            profile.target_locations = json.dumps(data.target_locations)
        await repo.upsert(profile)
        return _to_out(profile)


@router.get("/profile/preferences", response_model=dict[str, Any])
async def get_preferences():
    async with get_session() as session:
        repo = UserProfileRepository(session)
        profile = await repo.get()
        if profile is None or not profile.preferences:
            return Preferences().model_dump()
        return json.loads(profile.preferences)


@router.put("/profile/preferences")
async def update_preferences(data: Preferences):
    async with get_session() as session:
        repo = UserProfileRepository(session)
        await repo.set_preferences(data.model_dump_json())
        return {"ok": True}


@router.get("/onboarding/status")
async def onboarding_status():
    async with get_session() as session:
        repo = UserProfileRepository(session)
        profile = await repo.get()
        if profile is None:
            return {"step": 1}
        if profile.onboarding_step >= 4:
            return {"step": "complete"}
        return {"step": profile.onboarding_step}


@router.post("/profile/resume")
async def upload_resume(file: UploadFile):
    import tempfile
    from pathlib import Path
    from job_agent.tools.resume_parser import parse as parse_resume
    from job_agent.db.models import ResumeVersion
    from job_agent.db.repositories.resume_version_repo import ResumeVersionRepository
    import hashlib, json

    suffix = Path(file.filename or "resume.pdf").suffix
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    resume = parse_resume(tmp_path)
    tmp_path.unlink(missing_ok=True)

    version_id = hashlib.sha256(content).hexdigest()[:16]
    async with get_session() as session:
        repo = ResumeVersionRepository(session)
        version = ResumeVersion(
            id=version_id,
            filename=file.filename,
            sections=resume.model_dump_json(),
        )
        await repo.save(version)

    return {"version_id": version_id, "parsed": resume.model_dump()}


def _to_out(p: UserProfile) -> dict[str, Any]:
    prefs = json.loads(p.preferences) if p.preferences else None
    locs = json.loads(p.target_locations) if p.target_locations else None
    return {
        "full_name": p.full_name,
        "email": p.email,
        "phone": p.phone,
        "linkedin_url": p.linkedin_url,
        "github_url": p.github_url,
        "portfolio_url": p.portfolio_url,
        "current_title": p.current_title,
        "current_company": p.current_company,
        "years_exp": p.years_exp,
        "notice_period": p.notice_period,
        "current_location": p.current_location,
        "target_locations": locs,
        "expected_salary": p.expected_salary,
        "currency": p.currency,
        "onboarding_step": p.onboarding_step,
        "preferences": prefs,
    }
