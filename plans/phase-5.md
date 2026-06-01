# Phase 5 — Interface, Hardening, Launch

**Goal:** humans drive it, ops monitor it, security review passes.

**Exit:** 7-day unattended run on real account; ghost/reply rates + cost tracked; security checklist signed; rollback rehearsed.

## 5.1 FastAPI — complete all routers
- [ ] Routers: `jobs, applications, outreach, prep, config, eval, hitl-approvals, profile, onboarding, queue`
- [ ] OpenAPI at `/openapi.json` (drives UI type gen)
- [ ] API-key auth via `Depends(verify_api_key)`; key in httpOnly cookie for browser; Bearer for scripts
- [ ] Per-route rate limits (fastapi-limiter + Redis)
- [ ] SSE endpoint `GET /api/v1/events` — streams LangGraph node-complete events
- [ ] `GET /api/v1/queue/dlq` — inspect dead letter queue entries
- [ ] All endpoints from PROFILE.md (`/api/v1/profile/*`, `/api/v1/onboarding/status`)
- [ ] All prep endpoints from PREP.md (`/api/v1/prep/*`)

## 5.2 Next.js dashboard — design system first, then routes
See **`UI.md`** for libs/routes. See **`DESIGN.md`** for tokens/variants/shared utils.

**Foundation (build first — nothing else can start)**
- [ ] `styles/tokens.css` — all CSS vars per DESIGN.md
- [ ] `styles/globals.css` — imports tokens, shadcn overrides, body reset
- [ ] `styles/typography.css` — text utility classes per DESIGN.md
- [ ] `tailwind.config.ts` — Tailwind → CSS var mappings
- [ ] Inter font via `next/font/local` from `styles/fonts/`
- [ ] `lib/constants.ts` — all status/category/enum strings (JOB_STATUSES, CONFIDENCE, etc.)
- [ ] `lib/utils.ts` — `cn()`, `formatDate()`, `formatRelative()`, `slugify()`
- [ ] `lib/api.ts` — typed fetch wrapper; every endpoint covered
- [ ] `lib/queries.ts` — all `queryKeys` + `useQuery` / `useMutation` hooks
- [ ] shadcn init + install only needed components per DESIGN.md list
- [ ] OpenAPI → TS client codegen: `npm run gen:api` wired into CI

**Onboarding + profile (moved from Phase 2 backend — UI lives here)**
- [ ] `/onboarding` — 4-step wizard with `onboarding_step` polling `GET /api/v1/onboarding/status`; refresh-safe (step from DB)
- [ ] `/profile` — profile edit form; saves via `PUT /api/v1/profile`
- [ ] `/profile/resume` — drag-drop upload → parse → diff old vs new → inline bullet edit → approve

**Core routes**
- [ ] `/` — tracker kanban; drag card = `PATCH /api/v1/applications/{id}/status`
- [ ] `/jobs` — sortable filterable table (TanStack Table)
- [ ] `/approvals` — HITL queue, badge count = pending interrupts from SSE
- [ ] `/approvals/resume/[id]` — diff viewer (react-diff-viewer-continued) + per-bullet edit + approve
- [ ] `/approvals/cover/[id]` — preview + edit + approve
- [ ] `/approvals/outreach/[id]` — batch preview + per-row approve/skip
- [ ] `/approvals/referrals/[id]` — connection picker

**Prep routes**
- [ ] `/prep` — full question bank; filter category/difficulty/confidence/company
- [ ] `/prep/[job_id]` — per-application questions; company-specific first
- [ ] `/prep/session` — card flip; confidence rating (shaky/comfortable/confident); session state is ephemeral (React state only)
- [ ] `/prep/[question_id]` — edit user_answer; view source_jds list; export Anki CSV

**Analytics + settings**
- [ ] `/analytics` — ATS-score-vs-outcome (Recharts scatter), LLM cost/day (line), ghost rate (bar)
- [ ] `/settings/models` — model picker reads/writes `config.yaml` via API
- [ ] `/settings/preferences` — preferences form

**SSE integration**
- [ ] `lib/sse.ts` — EventSource wrapper; reconnects on disconnect; fires query invalidation on event type

## 5.3 Security pass
- [ ] `docs/SECURITY.md` — threat model
- [ ] `pip-audit` + `npm audit` in CI
- [ ] CSP headers on dashboard (next.config.js `headers()`)
- [ ] AES-GCM at-rest for cookies, LinkedIn tokens, Gmail refresh token
- [ ] Log scrubber unit tests prove no PII leaks on 10 PII-laden inputs
- [ ] `gitleaks` in CI
- [ ] Verify `data/resumes/` and `logs/screenshots/` are in `.gitignore`

## 5.4 Load + chaos
- [ ] Synthetic 500-job ingest — measure throughput, queue saturation
- [ ] Kill Postgres mid-run → LangGraph checkpoint recovery verified
- [ ] Kill Redis mid-run → Celery queue replay, no duplicate sends
- [ ] Captcha-solver-down drill → HITL interrupt fires; no silent skip
- [ ] Results documented in `docs/CHAOS.md`

## 5.5 Ops
- [ ] Grafana dashboard: queue depth, LLM cost/day, success per platform, ghost rate, DLQ depth
- [ ] Alert rules → Telegram: queue stuck >5min, error rate >5%, daily LLM cost >budget, DLQ non-empty
- [ ] `docs/RUNBOOK.md` — restart procedures, common errors, manual state fixes
- [ ] Backup script: Postgres dump + Chroma snapshot + `data/resumes/` rsync; store 7 days

## 5.6 Release
- [ ] Tag `v1.0`
- [ ] `docs/DEPLOY.md` with rollback procedure
- [ ] `--minimize` mode: verify cost/day on a real 6h run
- [ ] Eval baseline locked in `eval/results/baseline.json`

## Tests
- API: every router — happy path + 401 + 422 + 503
- Dashboard: vitest for shared lib functions; playwright e2e for onboarding wizard + approve resume + tracker drag
- SSE: EventSource reconnects; correct query invalidated per event type
- Chaos: results in `docs/CHAOS.md`
- Security: gitleaks clean; scrubber passes; CSP header present

Done: v1.0 tagged, rollback literally rehearsed, 7-day run passed. Update `STATE.md`.
