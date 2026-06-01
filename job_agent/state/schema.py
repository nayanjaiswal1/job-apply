from __future__ import annotations

import operator
from typing import Annotated

from langgraph.graph import MessagesState


class JobAgentState(MessagesState):
    # Job IDs discovered this run
    discovered_job_ids: Annotated[list[str], operator.add]
    # Job IDs that passed pre-filter and are queued for scoring
    jobs_to_score: Annotated[list[str], operator.add]
    # Job IDs that have been scored and are ready for resume/cover
    scored_job_ids: Annotated[list[str], operator.add]
    # Application IDs created this run
    application_ids: Annotated[list[str], operator.add]
    # Active agent name, set by orchestrator for routing
    active_agent: str
    # Whether --minimize mode is active
    minimize: bool
    # Whether --dry-run mode is active
    dry_run: bool
    # Errors accumulated this run (non-fatal, logged and continued)
    errors: Annotated[list[str], operator.add]
