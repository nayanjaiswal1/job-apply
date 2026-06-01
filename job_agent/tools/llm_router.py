from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

import litellm
import structlog

from job_agent.config.loader import load_config
from job_agent.errors import AgentError, RateLimited, TransientError, UpstreamUnavailable
from job_agent.util.result import Result

log = structlog.get_logger()

# sha256(model+messages+temperature) → response text
_cache: dict[str, str] = {}

_COST_PER_1K: dict[str, tuple[Decimal, Decimal]] = {
    "claude-sonnet-4-6": (Decimal("0.003"), Decimal("0.015")),
    "gpt-4o": (Decimal("0.005"), Decimal("0.015")),
    "gpt-4o-mini": (Decimal("0.00015"), Decimal("0.0006")),
}


@dataclass
class LLMResponse:
    text: str
    model_used: str
    tokens_in: int
    tokens_out: int
    cost_usd: Decimal
    cache_hit: bool
    fallback_from: str | None


@dataclass
class CostTracker:
    _total: Decimal = field(default_factory=Decimal)

    def record(self, model: str, tokens_in: int, tokens_out: int) -> Decimal:
        in_cost, out_cost = _COST_PER_1K.get(model, (Decimal("0"), Decimal("0")))
        cost = (Decimal(tokens_in) / 1000 * in_cost) + (Decimal(tokens_out) / 1000 * out_cost)
        self._total += cost
        return cost

    @property
    def total(self) -> Decimal:
        return self._total


_cost_tracker = CostTracker()


def _cache_key(model: str, messages: list[dict[str, str]], temperature: float) -> str:
    payload = json.dumps({"model": model, "messages": messages, "temperature": temperature}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


class LLMRouter:
    def __init__(self, minimize: bool = False) -> None:
        self._minimize = minimize
        _, self._app_config = load_config()

    def _resolve_model(self, task: str) -> tuple[str, str, str]:
        model_cfg = getattr(self._app_config.models, task, None)
        if model_cfg is None:
            raise AgentError(f"No model config for task: {task}")
        if self._minimize:
            return model_cfg.min_mode, model_cfg.primary, model_cfg.fallback
        return model_cfg.primary, model_cfg.fallback, model_cfg.min_mode

    def complete(
        self,
        task: str,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        **kw: Any,
    ) -> Result[LLMResponse, AgentError]:
        try:
            primary, fallback, _ = self._resolve_model(task)
        except AgentError as exc:
            return Result.err(exc)
        cache_key = _cache_key(primary, messages, temperature)

        if cache_key in _cache:
            log.info("llm_cache_hit", task=task, model=primary)
            return Result.ok(LLMResponse(
                text=_cache[cache_key],
                model_used=primary,
                tokens_in=0,
                tokens_out=0,
                cost_usd=Decimal("0"),
                cache_hit=True,
                fallback_from=None,
            ))

        attempts = [(primary, None), (fallback, primary)]
        for i, (model, fallback_from) in enumerate(attempts):
            is_last = i == len(attempts) - 1
            try:
                t0 = time.monotonic()
                resp = litellm.completion(model=model, messages=messages, temperature=temperature, **kw)
                latency_ms = int((time.monotonic() - t0) * 1000)
                tokens_in = resp.usage.prompt_tokens
                tokens_out = resp.usage.completion_tokens
                text = resp.choices[0].message.content or ""
                cost = _cost_tracker.record(model, tokens_in, tokens_out)

                log.info(
                    "llm_call",
                    task=task,
                    model=model,
                    tokens_in=tokens_in,
                    tokens_out=tokens_out,
                    cost_usd=str(cost),
                    latency_ms=latency_ms,
                    cache_hit=False,
                    fallback_from=fallback_from,
                )
                _cache[cache_key] = text
                return Result.ok(LLMResponse(
                    text=text,
                    model_used=model,
                    tokens_in=tokens_in,
                    tokens_out=tokens_out,
                    cost_usd=cost,
                    cache_hit=False,
                    fallback_from=fallback_from,
                ))
            except litellm.RateLimitError as exc:
                log.warning("llm_rate_limited", task=task, model=model, reason=str(exc))
                if is_last:
                    return Result.err(RateLimited(str(exc)))
            except litellm.ServiceUnavailableError as exc:
                log.warning("llm_unavailable", task=task, model=model, reason=str(exc))
                if is_last:
                    return Result.err(UpstreamUnavailable(str(exc)))
            except litellm.AuthenticationError as exc:
                return Result.err(AgentError(f"Auth error for {model}: {exc}"))
            except Exception as exc:
                log.warning("llm_error", task=task, model=model, reason=str(exc))
                if is_last:
                    return Result.err(TransientError(str(exc)))

        return Result.err(AgentError(f"All models exhausted for task: {task}"))  # pragma: no cover
