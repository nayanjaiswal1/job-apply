# Phase 2 — Data Ingestion

**Goal:** structured candidate data + job listings from every platform, with stealth, captcha, dedup.

**Exit:** end-to-end ingest from all platforms into Postgres; dedup verified; sessions restore across restarts; failure screenshots archived; ≥85% scraper coverage via contract tests (no live calls in CI).

## 2.0 Profile + onboarding (backend only — UI in Phase 5)
- [ ] `UserProfileRepository` — get/upsert profile row; `onboarding_step` read/write; `preferences` JSON read/write
- [ ] `GET /api/v1/onboarding/status` — `{step: 1..4 | "complete"}`
- [ ] Profile + preferences endpoints per PROFILE.md
- [ ] First-run guard: redirect to `/onboarding` if no profile row (FastAPI middleware)
- [ ] Parse preferences JSON column → `Preferences` pydantic on read; validate on write

## 2.1 Resume parser
- [ ] `tools/resume_parser.py` — pdfplumber → pymupdf fallback, multi-column detect, python-docx
- [ ] Output: `Resume` pydantic (`summary, skills, experience[], education[], certifications[], links[]`)
- [ ] Store raw text + structured JSON in `resume_versions`
- [ ] Golden tests on ≥10 fixtures (PDFs gitignored, content hashes pinned)

## 2.2 Preferences + pre-filter
- [ ] `models/preferences.py` — pydantic per REQUIREMENTS §6
- [ ] `services/pre_filter.py` — rule-based, reads `Preferences` from profile; no LLM
- [ ] Tests: every preference field has + and − case; DB round-trip (write JSON → read back → pydantic model intact)

## 2.3 Shared adapter tools (build before scrapers — scrapers depend on these)
- [ ] `tools/embedder.py` — `Embedder` implementing `EmbedderPort`; wraps Chroma's embedding + cosine_similarity; collection names from `config.yaml`
- [ ] `tools/captcha_solver.py` — `CaptchaSolver` implementing `CaptchaPort`; 2captcha + capsolver; circuit breaker (open after 3 fails → `HumanReviewNeeded`)
- [ ] `tools/session_store.py` — AES-GCM encrypted cookie jars, per-platform files
- [ ] `tools/proxy_pool.py` — residential pool, warm-up tracking, per-platform pinning

## 2.4 Playwright base scraper
- [ ] `tools/scrapers/base.py` — async base: stealth plugin, fingerprint random, human-input simulation, exp backoff, robots.txt check, screenshot on failure, session restore, proxy injection
- [ ] Inherits `ScraperPort`; all platform adapters subclass this

## 2.5 Platform adapters (each returns unified `Job` schema per REQUIREMENTS §4d)
- [ ] LinkedIn — OAuth2 first (`tools/linkedin_api.py`, see 2.6), Playwright fallback
- [ ] Indeed — Publisher API + Playwright fallback
- [ ] Naukri — Playwright only
- [ ] Wellfound — Playwright only
- [ ] Internshala — Playwright only
- [ ] Monster — Partner API + Playwright fallback
- [ ] Company career pages — Playwright only (generic form-detect + JD scrape)
- [ ] Contract tests: respx + recorded Playwright fixtures; no live calls in CI

## 2.6 Auth clients (LinkedIn + Gmail — both needed before Phase 4 outreach/tracker)
- [ ] `tools/linkedin_api.py` — `LinkedInClient` implementing OAuth2 PKCE flow; token stored AES-encrypted; auto-refresh; exposes `search_jobs()`, `send_dm()`, `get_connections()`
- [ ] `tools/email_tool.py` — `EmailTool` implementing `EmailPort`; Gmail OAuth2 for SMTP send + IMAP poll over TLS; `send()`, `poll_inbox() -> list[RawEmail]`

## 2.7 Research tool
- [ ] `tools/research_tool.py` — `ResearchTool` implementing `ResearchPort`; Tavily primary, SerpAPI fallback; returns `list[SearchResult(title, url, snippet, source)]`

## 2.8 LinkedIn post scraper
- [ ] `tools/scrapers/linkedin_posts.py` — hashtag feed + target company pages
- [ ] LLM extracts company, role, contact, apply instructions → `Job` with `source_type="linkedin_post"`

## 2.9 Dedup service
- [ ] `services/dedup.py` — SHA-256 exact match (DB lookup) + Chroma cosine via `Embedder` (>0.92 → skip)
- [ ] Idempotent inserts via `JobRepository.upsert_job`

## 2.10 Eval fixtures (collect before Phase 3 eval runner)
- [ ] `eval/data/sample_jds/` — collect 5–10 real JDs covering target roles (save as `.txt`)
- [ ] `eval/data/sample_jobs.json` — 20+ job objects in unified schema for scoring eval
- [ ] `eval/data/sample_emails/` — 10–15 real reply emails covering all classifier labels
- [ ] These are static fixtures; commit them (no secrets); used by every eval task

## Tests
- Resume parser: golden snapshot per fixture, multi-column ordering correct
- Pre-filter: every field has + and − case; preferences JSON DB round-trip
- Embedder: cosine similarity returns expected order on known vectors; collection name from config
- Captcha: circuit breaker opens after 3 fails; interrupt fires on open
- Scraper base: stealth headers present, screenshot saved on raise, session restore round-trip
- Platform adapters: every platform produces valid `Job`; dedup catches near-duplicates
- LinkedIn OAuth: token refresh flow tested with mocked responses
- Email tool: SMTP send mocked, IMAP poll returns `RawEmail` list
- Post scraper: LLM extraction output schema-validated

Done: ingest run on real account produces ≥50 deduped jobs. Update `STATE.md`.
