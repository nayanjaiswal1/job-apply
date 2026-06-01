"""Eval runner — benchmarks LLM models on actual tasks before production use."""
from __future__ import annotations

import json
import re
import statistics
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import typer

app = typer.Typer(help="LLM eval runner")

_DATA_DIR = Path(__file__).parent / "data"
_RESULTS_DIR = Path(__file__).parent / "results"
_RESULTS_DIR.mkdir(exist_ok=True)

_BANNED_VERBS = {
    "spearheaded", "leveraged", "orchestrated", "championed", "fostered",
    "utilized", "facilitated", "streamlined", "synergized", "revolutionized",
}


@dataclass
class EvalResult:
    task: str
    model: str
    ai_detect_score: float = 0.0
    ats_keyword_pct: float = 0.0
    banned_count: int = 0
    bullet_length_variance: float = 0.0
    latency_ms: int = 0
    passed: bool = False
    notes: str = ""


@dataclass
class EvalReport:
    results: list[EvalResult] = field(default_factory=list)

    def leaderboard(self) -> list[EvalResult]:
        def score(r: EvalResult) -> float:
            return (
                (1.0 - r.ai_detect_score) * 0.3
                + (r.ats_keyword_pct / 100) * 0.3
                + (1.0 if r.banned_count == 0 else 0.0) * 0.2
                + min(r.bullet_length_variance / 5.0, 1.0) * 0.2
            )
        return sorted(self.results, key=score, reverse=True)

    def to_dict(self) -> dict[str, Any]:
        return {"results": [r.__dict__ for r in self.results]}


def _count_banned(text: str) -> int:
    text_lower = text.lower()
    return sum(1 for v in _BANNED_VERBS if v in text_lower)


def _bullet_length_variance(text: str) -> float:
    bullets = [
        line.strip() for line in text.splitlines()
        if line.strip().startswith(("•", "-", "*", "·"))
    ]
    if len(bullets) < 2:
        return 0.0
    lengths = [len(b.split()) for b in bullets]
    return statistics.stdev(lengths) if len(lengths) >= 2 else 0.0


def _ats_keyword_pct(resume_text: str, jd_text: str) -> float:
    jd_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", jd_text.lower()))
    resume_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", resume_text.lower()))
    if not jd_words:
        return 0.0
    overlap = jd_words & resume_words
    return len(overlap) / len(jd_words) * 100


def _run_resume_rewrite(models: list[str], jd_paths: list[Path]) -> list[EvalResult]:
    from job_agent.tools.llm_router import LLMRouter
    results = []
    for model_name in models:
        for jd_path in jd_paths:
            jd_text = jd_path.read_text()
            router = LLMRouter()
            messages = [
                {"role": "system", "content": "Rewrite the resume summary for this JD. Output plain text only."},
                {"role": "user", "content": f"JD:\n{jd_text[:500]}"},
            ]
            t0 = time.monotonic()
            result = router.complete("resume_rewrite", messages)
            latency = int((time.monotonic() - t0) * 1000)
            if result.is_err():
                results.append(EvalResult(task="resume_rewrite", model=model_name, notes=str(result.unwrap_err())))
                continue
            text = result.unwrap().text
            er = EvalResult(
                task="resume_rewrite",
                model=model_name,
                ats_keyword_pct=_ats_keyword_pct(text, jd_text),
                banned_count=_count_banned(text),
                bullet_length_variance=_bullet_length_variance(text),
                latency_ms=latency,
            )
            er.passed = er.banned_count == 0 and er.ats_keyword_pct > 85
            results.append(er)
    return results


def _run_job_scoring(models: list[str]) -> list[EvalResult]:
    sample_path = _DATA_DIR / "sample_jobs.json"
    if not sample_path.exists():
        return []
    jobs = json.loads(sample_path.read_text())
    from job_agent.tools.llm_router import LLMRouter
    results = []
    for model_name in models:
        for job in jobs[:3]:
            router = LLMRouter()
            messages = [
                {"role": "system", "content": "Score this job 0.0–1.0 for a Python backend engineer. Return just a number."},
                {"role": "user", "content": job.get("jd_text", "")},
            ]
            t0 = time.monotonic()
            result = router.complete("job_scoring", messages)
            latency = int((time.monotonic() - t0) * 1000)
            if result.is_err():
                results.append(EvalResult(task="job_scoring", model=model_name, notes=str(result.unwrap_err())))
                continue
            text = result.unwrap().text.strip()
            try:
                score = float(re.search(r"\d+\.?\d*", text).group())  # type: ignore[union-attr]
                passed = 0.0 <= score <= 1.0
            except Exception:
                score, passed = 0.0, False
            results.append(EvalResult(task="job_scoring", model=model_name, passed=passed, latency_ms=latency))
    return results


@app.command()
def run(
    task: str = typer.Option("all", help="Task name or 'all'"),
    models: str = typer.Option("", help="Comma-separated model IDs to test"),
    jds: Path = typer.Option(_DATA_DIR / "sample_jds", help="JD directory"),
    auto_update_config: bool = typer.Option(False, "--auto-update-config"),
    log: Path = typer.Option(None, help="Save results JSON to this path"),
) -> None:
    model_list = [m.strip() for m in models.split(",") if m.strip()] or ["claude-sonnet-4-6"]
    jd_paths = list(jds.glob("*.txt")) if jds.exists() else []

    report = EvalReport()

    if task in ("resume_rewrite", "all"):
        report.results.extend(_run_resume_rewrite(model_list, jd_paths))
    if task in ("job_scoring", "all"):
        report.results.extend(_run_job_scoring(model_list))

    board = report.leaderboard()
    typer.echo("\n=== Leaderboard ===")
    for r in board:
        status = "✓" if r.passed else "✗"
        typer.echo(f"  {status} {r.model:40s}  ats={r.ats_keyword_pct:.0f}%  banned={r.banned_count}  var={r.bullet_length_variance:.1f}")

    if log:
        log.write_text(json.dumps(report.to_dict(), indent=2))
        typer.echo(f"\nSaved to {log}")

    if auto_update_config and board and board[0].passed:
        typer.echo(f"\nWinner: {board[0].model} — run `uv run alembic` then update config.yaml manually after reviewing.")


if __name__ == "__main__":
    app()
