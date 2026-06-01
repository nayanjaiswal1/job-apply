from __future__ import annotations

import asyncio
from typing import Any

import structlog
from langgraph.graph import END, START, StateGraph

from job_agent.state.schema import JobAgentState

log = structlog.get_logger()

# HITL nodes — graph pauses before these for human approval
_HITL_NODES = {
    "resume_hitl",
    "cover_letter_hitl",
    "outreach_hitl",
    "apply_confirm",
    "referral_hitl",
    "followup_hitl",
    "captcha_hitl",
}


def _stub_node(name: str) -> Any:
    async def node(state: JobAgentState) -> dict[str, Any]:
        log.info("node_stub", node=name)
        return {}
    node.__name__ = name
    return node


def build_graph() -> StateGraph:  # type: ignore[type-arg]
    builder: StateGraph = StateGraph(JobAgentState)  # type: ignore[type-arg]

    nodes = [
        "orchestrator",
        "job_search",
        "company_research",
        "resume",
        "cover_letter",
        "referral_finder",
        "outreach",
        "form_filler",
        "tracker",
        "followup",
        "prep",
        "notifier",
    ]
    for name in nodes:
        builder.add_node(name, _stub_node(name))

    # HITL interrupt stubs
    for name in _HITL_NODES:
        builder.add_node(name, _stub_node(name))

    builder.add_edge(START, "orchestrator")
    builder.add_edge("orchestrator", "job_search")
    builder.add_edge("job_search", "company_research")
    builder.add_edge("company_research", "resume")
    builder.add_edge("resume", "resume_hitl")
    builder.add_edge("resume_hitl", "cover_letter")
    builder.add_edge("cover_letter", "cover_letter_hitl")
    builder.add_edge("cover_letter_hitl", "referral_finder")
    builder.add_edge("referral_finder", "referral_hitl")
    builder.add_edge("referral_hitl", "outreach")
    builder.add_edge("outreach", "outreach_hitl")
    builder.add_edge("outreach_hitl", "form_filler")
    builder.add_edge("form_filler", "apply_confirm")
    builder.add_edge("apply_confirm", "tracker")
    builder.add_edge("tracker", "followup")
    builder.add_edge("followup", "followup_hitl")
    builder.add_edge("followup_hitl", "prep")
    builder.add_edge("prep", "notifier")
    builder.add_edge("notifier", END)

    return builder


def run_graph(minimize: bool = False, dry_run: bool = False, agent: str | None = None) -> None:
    from job_agent.state.checkpointer import build_checkpointer

    async def _run() -> None:
        checkpointer = await build_checkpointer()
        graph = build_graph().compile(
            checkpointer=checkpointer,
            interrupt_before=list(_HITL_NODES),
        )
        initial: dict[str, Any] = {
            "messages": [],
            "discovered_job_ids": [],
            "jobs_to_score": [],
            "scored_job_ids": [],
            "application_ids": [],
            "active_agent": agent or "orchestrator",
            "minimize": minimize,
            "dry_run": dry_run,
            "errors": [],
        }
        config = {"configurable": {"thread_id": "main"}}
        async for chunk in graph.astream(initial, config=config):
            log.info("graph_step", chunk=list(chunk.keys()))

    asyncio.run(_run())
