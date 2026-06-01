from __future__ import annotations

from typing import Any, Protocol

from job_agent.errors import AgentError
from job_agent.util.result import Result


class LLMPort(Protocol):
    def complete(
        self,
        task: str,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        **kw: Any,
    ) -> Result[object, AgentError]: ...
