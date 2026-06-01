# Symbol Index

One line per public symbol. AI reads this instead of grepping the codebase.

**Format:** `path/file.py:Symbol — purpose (sig)`

**Skip:** private (`_foo`), tests, generated code.

**Update rule:** every new public function or class adds one line here in the same commit. No exceptions.

**Order:** group by folder, then alphabetical inside a group.

---

## config/

- `job_agent/config/settings.py:Settings` — frozen pydantic-settings root; reads all env vars
- `job_agent/config/models.py:AgentModelConfig` — primary/fallback/min_mode per agent
- `job_agent/config/models.py:AppConfig` — root config.yaml model (chroma + models + schedule + notifications)
- `job_agent/config/loader.py:load_config` — `(config_path: Path) -> tuple[Settings, AppConfig]`; cached

## state/

- `job_agent/state/schema.py:JobAgentState` — root LangGraph TypedDict with annotated reducers
- `job_agent/state/checkpointer.py:build_checkpointer` — `() -> AsyncPostgresSaver`; wires Postgres checkpointer

## db/

- `job_agent/db/models.py:Job` — SQLAlchemy ORM model for jobs table
- `job_agent/db/models.py:Company` — SQLAlchemy ORM model for companies table
- `job_agent/db/models.py:Application` — SQLAlchemy ORM model for applications table
- `job_agent/db/models.py:Outreach` — SQLAlchemy ORM model for outreach table
- `job_agent/db/models.py:Question` — SQLAlchemy ORM model for questions table
- `job_agent/db/models.py:ResumeVersion` — SQLAlchemy ORM model for resume_versions table
- `job_agent/db/models.py:UserProfile` — SQLAlchemy ORM model for user_profile table
- `job_agent/db/models.py:FollowUp` — SQLAlchemy ORM model for follow_ups table
- `job_agent/db/session.py:get_session` — `() -> AsyncGenerator[AsyncSession]`; async context manager with UoW
- `job_agent/db/repositories/job_repo.py:JobRepository.upsert_job` — insert/update by SHA-256 id
- `job_agent/db/repositories/job_repo.py:JobRepository.list_by_status` — `(status, limit) -> list[Job]`
- `job_agent/db/repositories/application_repo.py:ApplicationRepository.save` — persist Application row
- `job_agent/db/repositories/company_repo.py:CompanyRepository.upsert` — upsert Company; summary is authoritative JSON
- `job_agent/db/repositories/outreach_repo.py:OutreachRepository.already_contacted` — `(person, company) -> bool`
- `job_agent/db/repositories/question_repo.py:QuestionRepository.list_by_job` — questions matching a job_id in source_jds
- `job_agent/db/repositories/resume_version_repo.py:ResumeVersionRepository.latest` — most recent resume version
- `job_agent/db/repositories/user_profile_repo.py:UserProfileRepository.get` — single-row profile fetch
- `job_agent/db/repositories/followup_repo.py:FollowUpRepository.list_by_application` — follow-ups for one application

## tools/

- `job_agent/tools/llm_router.py:LLMRouter.complete` — entry for every LLM call. `(task, messages, **kw) -> Result[LLMResponse, AgentError]`
- `job_agent/tools/llm_router.py:CostTracker.record` — `(model, tokens_in, tokens_out) -> Decimal`

## ports/

- `job_agent/ports/llm.py:LLMPort` — Protocol: what agents call; LLMRouter implements it
- `job_agent/ports/scraper.py:ScraperPort` — Protocol: `search(query, prefs) -> list[Job]`
- `job_agent/ports/scraper.py:Job` — unified job dataclass (platform-agnostic)
- `job_agent/ports/email.py:EmailPort` — Protocol: send + poll_inbox
- `job_agent/ports/email.py:RawEmail` — raw email dataclass from IMAP
- `job_agent/ports/captcha.py:CaptchaPort` — Protocol: `solve(site_key, url) -> str`
- `job_agent/ports/embedder.py:EmbedderPort` — Protocol: embed + cosine_similarity
- `job_agent/ports/storage.py:FileStoragePort` — Protocol: save_pdf, save_txt, get_path
- `job_agent/ports/notifier.py:NotifierPort` — Protocol: send_alert, send_digest
- `job_agent/ports/researcher.py:ResearchPort` — Protocol: `search(query) -> list[SearchResult]`
- `job_agent/ports/researcher.py:SearchResult` — title/url/snippet/source dataclass

## tools (Phase 2 continued)

- `job_agent/tools/resume_parser.py:parse` — `(path: Path) -> Resume`; pdfplumber → pymupdf fallback, python-docx
- `job_agent/tools/resume_parser.py:Resume` — parsed resume pydantic (summary, skills, experience[], education[], certifications[], links[])
- `job_agent/api/routers/profile.py:router` — GET/PUT /profile, preferences, onboarding/status, POST /profile/resume
- `job_agent/api/main.py:onboarding_guard` — middleware: 307 to /onboarding if no profile row

## errors / util

- `job_agent/errors.py:AgentError` — base class for all agent failures
- `job_agent/errors.py:TransientError` — retryable (network, rate limit)
- `job_agent/errors.py:PermanentError` — not retryable
- `job_agent/errors.py:HumanReviewNeeded` — pause graph, fire HITL
- `job_agent/errors.py:RateLimited` — provider rate limit; subclass of TransientError
- `job_agent/errors.py:UpstreamUnavailable` — third-party down; subclass of TransientError
- `job_agent/util/result.py:Result` — `Result[T, E]` with .ok, .err, .unwrap, .map, .is_err
- `job_agent/util/retry.py:retry_transient` — tenacity decorator; only retries TransientError

## obs/

- `job_agent/obs/logging.py:configure_logging` — sets up structlog JSON renderer + PII scrubber
- `job_agent/obs/logging.py:new_request_id` — generates UUID, binds to structlog contextvar
- `job_agent/obs/tracing.py:configure_tracing` — sets up OTel SDK + OTLP exporter
- `job_agent/obs/tracing.py:get_tracer` — `(name) -> trace.Tracer`

## api/

- `job_agent/api/health.py:health` — `GET /health`; returns DB+Redis+Chroma status; 503 if critical dep down
- `job_agent/api/main.py:app` — FastAPI application instance

## graph

- `job_agent/graph.py:build_graph` — constructs StateGraph with 12 nodes + 7 HITL interrupt stubs
- `job_agent/graph.py:run_graph` — `(minimize, dry_run, agent) -> None`; entry for CLI

## Phase 2 — tools / services

- `job_agent/tools/session_store.py:SessionStore` — AES-GCM encrypted per-platform cookie storage; `save/load/delete(platform)`
- `job_agent/tools/proxy_pool.py:ProxyPool` — residential proxy pool; `get_for_platform`, `record_request`, `is_warmed_up`
- `job_agent/tools/embedder.py:Embedder` — EmbedderPort impl; wraps Chroma embedding + `cosine_similarity`
- `job_agent/tools/captcha_solver.py:CaptchaSolver` — CaptchaPort impl; 2captcha + capsolver; circuit breaker after 3 fails → HumanReviewNeeded
- `job_agent/tools/scrapers/base.py:BaseScraper` — async Playwright base; stealth, human input, session restore, proxy, screenshot on fail
- `job_agent/tools/scrapers/naukri.py:NaukriScraper` — Naukri Playwright scraper → unified Job
- `job_agent/tools/scrapers/wellfound.py:WellfoundScraper` — Wellfound Playwright scraper → unified Job
- `job_agent/tools/scrapers/internshala.py:IntershalaScraper` — Internshala Playwright scraper → unified Job
- `job_agent/tools/scrapers/linkedin_scraper.py:LinkedInScraper` — LinkedIn Playwright fallback scraper → unified Job
- `job_agent/tools/scrapers/linkedin_posts.py:LinkedInPostScraper` — hashtag post scraper + LLM extraction → unified Job (source_type=linkedin_post)
- `job_agent/tools/linkedin_api.py:LinkedInClient` — OAuth2 PKCE; `search_jobs`, `send_dm`, `get_connections`; auto-refresh
- `job_agent/tools/email_tool.py:EmailTool` — EmailPort impl; Gmail OAuth2 SMTP send + imaplib2 IMAP poll
- `job_agent/tools/research_tool.py:ResearchTool` — ResearchPort impl; Tavily primary, SerpAPI fallback
- `job_agent/models/preferences.py:Preferences` — pydantic model per REQUIREMENTS §6
- `job_agent/services/pre_filter.py:passes_pre_filter` — `(job, prefs) -> bool`; rule-based, no LLM
- `job_agent/services/dedup.py:DedupService` — exact SHA-256 + cosine >0.92 fuzzy dedup
- `job_agent/services/dedup.py:job_id` — `(title, company, location) -> str`; SHA-256 canonical id

## startup

- `job_agent/startup.py:ensure_dirs` — creates data/resumes/, data/cover_letters/, logs/screenshots/ on boot
