from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

from job_agent.api.health import router as health_router
from job_agent.api.routers.applications import router as applications_router
from job_agent.api.routers.hitl import router as hitl_router
from job_agent.api.routers.jobs import router as jobs_router
from job_agent.api.routers.prep import router as prep_router
from job_agent.api.routers.profile import router as profile_router
from job_agent.obs.logging import configure_logging
from job_agent.startup import ensure_dirs

configure_logging()
ensure_dirs()

app = FastAPI(title="Job Agent", version="0.1.0")

for r in (health_router, profile_router, jobs_router, applications_router, prep_router, hitl_router):
    app.include_router(r)

# SSE event bus (in-process; replace with Redis pub/sub for multi-process)
_sse_queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=256)


def emit_event(event_type: str, payload: dict) -> None:
    try:
        _sse_queue.put_nowait({"type": event_type, "payload": payload})
    except asyncio.QueueFull:
        pass


@app.get("/api/v1/events")
async def sse_events(request: Request) -> StreamingResponse:
    async def generator() -> AsyncGenerator[str, None]:
        while True:
            if await request.is_disconnected():
                break
            try:
                event = await asyncio.wait_for(_sse_queue.get(), timeout=30)
                yield f"data: {json.dumps(event)}\n\n"
            except asyncio.TimeoutError:
                yield ": keepalive\n\n"
    return StreamingResponse(generator(), media_type="text/event-stream")


@app.middleware("http")
async def onboarding_guard(request: Request, call_next):
    skip_prefixes = ("/health", "/api/v1/onboarding", "/api/v1/profile", "/openapi.json", "/docs", "/redoc", "/api/v1/events")
    if any(request.url.path.startswith(p) for p in skip_prefixes):
        return await call_next(request)
    from job_agent.db.repositories.user_profile_repo import UserProfileRepository
    from job_agent.db.session import get_session
    async with get_session() as session:
        repo = UserProfileRepository(session)
        profile = await repo.get()
        if profile is None:
            return JSONResponse({"detail": "Onboarding required", "redirect": "/onboarding"}, status_code=307)
    return await call_next(request)
