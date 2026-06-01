# Job Hunting Agent

LangGraph multi-agent system: search, score, tailor resume, cover letters, referrals, outreach, form fill, track replies, follow up, prep interviews.

## Session start — files to load

Auto-load: **only** `CLAUDE.md`, `STATE.md`, `plans/phase-<active>.md`.

On-demand (don't speculatively load):
- `INDEX.md` — symbol map. Read before writing a new utility, or to answer "where is X?".
- `GOAL.md` — one-page project goal and scope.
- `PROFILE.md` — user profile model, onboarding wizard, resume upload flow.
- `DOCS.md` — PDF/document generation: templates, Playwright pipeline, ATS plain text.
- `PREP.md` — interview prep: question generation, dedup logic, confidence tracking, study modes.
- `DESIGN.md` — design system: CSS tokens, Tailwind config, cva variants, shared UI utilities.
- `REQUIREMENTS.md` — full spec.
- `UI.md` — dashboard libs, routes, components.
- Inactive `plans/phase-{n}.md`.
- Any new `.md` the user adds — list it here when it appears; do not auto-load.

## Stack (no substitutions without asking)
Python 3.12 async. LangGraph + LangChain LCEL. LiteLLM router. FastAPI. Next.js. Postgres + SQLAlchemy 2.x + Alembic. Redis + Celery. APScheduler. ChromaDB. Playwright + stealth. structlog + LangSmith + OTel.

## Quality bars (CI gates)
- `mypy --strict` — no `Any`, no untyped defs
- `ruff` — zero warnings on changed files
- `pytest --cov` — ≥85% agents/tools, 100% state/db/config/llm_router
- `alembic` for every schema change — never `create_all()`
- `detect-secrets` blocks `.env` leaks
- `import-linter` — agents → ports only, never tools or db direct

## Architecture
- Hexagonal: `agents/` use `ports/` (Protocols), implemented by `tools/` adapters. DI everywhere.
- Repositories wrap SQLAlchemy. No sessions in agents/services.
- Pydantic v2 at every boundary. No bare dicts crossing modules.
- `Result[T, AgentError]` on fallible ops. No bare `except`. Log every fallback with reason.
- Idempotency keys on every side-effect (send, submit, DM).
- `SqlAlchemySaver` checkpointer. `MemorySaver` only in tests.

## Reuse before write — no over-engineering
1. **Check `INDEX.md`** for an existing symbol. Reuse.
2. **Check `pyproject.toml` deps** — if a lib does it, use it. Standard picks:
   - Retries: `tenacity`
   - Rate limit: `aiolimiter`
   - State machine: `python-statemachine`
   - Diff: `difflib` (stdlib)
   - HTTP: `httpx`
   - Time/tz: `zoneinfo` (stdlib)
   - Crypto: `cryptography` (AES-GCM)
   - CLI: `typer`
   - Validation: `pydantic` v2
   - PDF gen: Playwright `page.pdf()` — full Chrome CSS support (we already have Playwright)
   - Email parse: stdlib `email` + `html2text`
   - Embeddings + cosine: Chroma built-in
   - Console output: `rich`
3. Only write new code if both above fail.
4. DRY rule of two: extract on second occurrence, never on the first.
5. After adding any new public function/class → append one line to `INDEX.md` in the same commit.

## Code style
- Comments only for *why* (constraint, workaround, invariant). Never *what*.
- Names over comments. Rename rather than annotate.
- Split modules >300 lines. No dead code, no TODOs without an issue.

## LLM rules
- All calls via `tools/llm_router.py`. No direct LiteLLM elsewhere.
- Cache by sha256(model+messages+temperature). Anthropic prompt-caching on static prefixes.
- Every call logs: model, tokens_in/out, cost_usd, latency_ms, cache_hit, fallback_from.
- Resume + cover letter must pass AI-detector gate (<0.4) before save.
- New LLM agent? Add an eval task first.

## HITL (interrupt_before)
Resume diff, cover letter, outreach batch, apply confirm, referral picks, follow-up send, captcha failure. Test the resume path, not just the happy path.

## Commands
```
uv run ruff check . && uv run ruff format --check . && uv run mypy . && uv run pytest --cov
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "msg"
docker-compose up -d
uv run python -m job_agent.graph [--minimize] [--dry-run] [--agent <name>]
uv run python -m job_agent.eval --all
```

## Never
- Commit `.env`, cookies, resume PDFs, screenshots, `eval/results/`.
- Add features outside the active phase.
- Reinvent something a library does (see "Reuse before write").
- Hardcode a color hex, font size, or magic string in a component — use tokens / constants (see DESIGN.md).
- Write a `fetch()` call in a component — use `ui/lib/api.ts`.
- Write `useQuery` outside `ui/lib/queries.ts`.
- Repeat a class group across two components — extract to `cva` or a shared CSS class.
- `--no-verify` hooks — fix the failure.
- Auto-retry form submissions.
- Send real outreach in tests — use `DryRunOutreach`.
- Log PII, email bodies, message content.
- Bypass HITL outside `--dry-run`.
- Change `config.yaml` models without an eval backing it.
- Add `Co-Authored-By` or any AI attribution to commits or PRs.
- Auto-load any `.md` outside the auto-load set without explicit instruction.

## Session end
Update `STATE.md` (current task, next, blockers). If you added public symbols, ensure `INDEX.md` reflects them. One commit per task, prefix `phase-N:`.
