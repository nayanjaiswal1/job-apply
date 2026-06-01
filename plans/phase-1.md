# Phase 1 — Foundation

**Goal:** deployable empty graph + observability + CI + migrations + LLM router. No business logic yet.

**Exit:** `docker-compose up` boots stack; empty graph round-trips a checkpoint; `/health` returns; CI green; 100% coverage on state/db/config/llm_router.

## 1.1 Bootstrap
- [ ] `pyproject.toml` (uv, Python 3.12)
- [ ] `ruff.toml` (E,F,W,I,B,UP,SIM,RUF,ASYNC,TCH; len 100)
- [ ] `mypy.ini` (strict, warn_unreachable, disallow_any_explicit)
- [ ] `.pre-commit-config.yaml` (ruff, ruff-format, mypy, detect-secrets, check-yaml, no-large-files)
- [ ] `Dockerfile` (multi-stage, non-root, healthcheck)
- [ ] `docker-compose.yml` (postgres:16, redis:7, chromadb, ollama)
- [ ] `.github/workflows/ci.yml` (lint → typecheck → test → alembic dry-run → import-linter)
- [ ] `.env.example` — full key list:
  ```
  # LLM providers
  OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY, GROQ_API_KEY
  # LinkedIn OAuth2 (PKCE)
  LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET, LINKEDIN_REDIRECT_URI
  # Gmail OAuth2
  GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN
  # Captcha solvers
  TWOCAPTCHA_API_KEY, CAPSOLVER_API_KEY
  # Proxies
  PROXY_HTTP, PROXY_USERNAME, PROXY_PASSWORD
  # Notifications
  TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
  # Observability
  LANGSMITH_API_KEY, LANGSMITH_PROJECT
  # Search
  TAVILY_API_KEY, SERPAPI_API_KEY
  # DB / Queue
  DATABASE_URL, REDIS_URL
  # App
  APP_API_KEY, SECRET_KEY
  ```
- [ ] `config.yaml` initial file — full model assignments per REQUIREMENTS §24 + Chroma collection names:
  ```yaml
  chroma:
    job_embeddings_collection: "job_embeddings"
    question_embeddings_collection: "question_embeddings"
  models:
    # ... per REQUIREMENTS §24
  ```
- [ ] `job_agent/startup.py` — create `data/resumes/`, `data/cover_letters/`, `logs/screenshots/` if missing on boot

## 1.2 Config
- [ ] `config/settings.py` — pydantic-settings, frozen, validated; includes all `.env` keys
- [ ] `config/models.py` — pydantic model for `config.yaml` per-agent primary/fallback/min_mode + chroma collections
- [ ] `config/loader.py` — `load_config() -> (Settings, ModelConfig)`
- [ ] CLI: `--minimize`, `--dry-run`, `--agent <name>` (typer)

## 1.3 DB
- [ ] SQLAlchemy 2.x typed models (all tables below); Alembic init + baseline migration
- [ ] Tables per REQUIREMENTS §22 + additions:
  - `user_profile` — per PROFILE.md; add `onboarding_step INT DEFAULT 1` column; add `preferences JSONB` column (stores Preferences pydantic model, no separate table)
  - `jobs, companies, applications, outreach, questions, resume_versions` — per REQUIREMENTS §22
  - `follow_ups` — new table:
    ```sql
    CREATE TABLE follow_ups (
      id           TEXT PRIMARY KEY,
      application_id TEXT REFERENCES applications(id),
      day_offset   INT,   -- 7 | 14 | 21
      channel      TEXT,  -- "email" | "linkedin_dm"
      draft        TEXT,
      status       TEXT DEFAULT 'draft',  -- draft|approved|sent|skipped
      sent_at      TIMESTAMP,
      created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    ```
- [ ] `db/repositories/` — one per aggregate:
  `JobRepository, ApplicationRepository, CompanyRepository, OutreachRepository, QuestionRepository, ResumeVersionRepository, UserProfileRepository, FollowUpRepository`
- [ ] `db/session.py` — async session + UoW context manager

## 1.4 State + checkpointer
- [ ] `state/schema.py` — `JobAgentState` TypedDict with `Annotated[..., reducer]` on collections
- [ ] `state/checkpointer.py` — `SqlAlchemySaver` implementing `BaseCheckpointSaver`

## 1.5 LLM router
- [ ] `tools/llm_router.py` — `LLMRouter.complete(task, messages, **kw)`
- [ ] Resolves model per `--minimize`; auto fallback chain on error/timeout/rate-limit
- [ ] sha256 prompt cache (TTL per task); Anthropic prompt-caching on static prefix
- [ ] structlog per call: model, tokens, cost, latency, cache_hit, fallback_from

## 1.6 Graph skeleton
- [ ] `graph.py` — `StateGraph` wiring all 12 nodes as typed stubs
- [ ] `interrupt_before` on 7 HITL nodes (REQUIREMENTS §16)
- [ ] Entry = orchestrator, terminal = notifier

## 1.7 Observability
- [ ] `obs/logging.py` — structlog JSON, request-id contextvar, PII scrubber
- [ ] `obs/tracing.py` — OTel SDK, spans per agent
- [ ] LangSmith project tag via env

## 1.8 Errors
- [ ] `errors.py` — `AgentError, TransientError, PermanentError, HumanReviewNeeded, RateLimited, UpstreamUnavailable`
- [ ] `util/result.py` — `Result[T, E]`
- [ ] `@retry_transient` (tenacity, exp backoff, only on TransientError)

## 1.9 Health
- [ ] `api/health.py` — `GET /health` returns DB+Redis+Chroma ping, queue depth, last-run per agent; 503 if critical dep down

## 1.10 Import contracts
- [ ] `importlinter.ini` — agents ↛ tools/db direct; only via ports/repositories; state is leaf
- [ ] Wired into CI

## 1.11 Ports (Protocol interfaces) — define before Phase 2 builds adapters
- [ ] `ports/llm.py` — `LLMPort` protocol (what agents call; `LLMRouter` implements it)
- [ ] `ports/scraper.py` — `ScraperPort` (returns `list[Job]`; platform adapters implement)
- [ ] `ports/email.py` — `EmailPort` (send, poll_inbox, classify)
- [ ] `ports/captcha.py` — `CaptchaPort` (solve → str)
- [ ] `ports/embedder.py` — `EmbedderPort` (embed → list[float], cosine_similarity)
- [ ] `ports/storage.py` — `FileStoragePort` (save_pdf, save_txt, get_path)
- [ ] `ports/notifier.py` — `NotifierPort` (send_alert, send_digest)
- [ ] `ports/researcher.py` — `ResearchPort` (search → list[SearchResult])

## Tests (≥85% coverage; 100% on state/db/config/llm_router)
- Config: invalid YAML rejected, missing env rejected with clear errors; Chroma collection names loaded
- DB: every model round-trips, every repo method, alembic up+down on temp DB; follow_ups round-trips
- Checkpointer: write → restart → resume identical
- LLM router: mocked fallback ordering, cache hit on repeat, cost accounting
- Graph: compiles, stub run end-to-end, interrupt pauses, resume continues
- Logging: scrubber strips emails/phones/names
- Retry: stops on PermanentError, retries TransientError N times
- Health: simulated DB outage → 503; Chroma down → 503

Done: full CI green locally. Update `STATE.md` to phase 2.
