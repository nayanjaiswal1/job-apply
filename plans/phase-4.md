# Phase 4 — Action Layer

**Goal:** system can send, submit, parse — with rate limits, idempotency, durable state machine.

**Exit:** end-to-end happy path runs against sandbox Gmail (job → applied → reply tracked → follow-up drafted); rate limits empirically verified; state machine 100% branch coverage; idempotency proven via replay test.

## 4.1 Rate-limit queue + DLQ
- [ ] `queue/tasks.py` — Celery tasks: `send_email`, `send_linkedin_dm`, `submit_form`, `poll_inbox`
- [ ] `queue/rate_limiter.py` — token-bucket per channel: email (50/day, 5–15min stagger), linkedin_dm (20/day, 60–180s); idempotency keys on every task (SHA-256 of payload → Redis SET NX)
- [ ] `queue/dlq.py` — `DeadLetterQueue`: after 3 failures move task to DLQ; persist failed payload to Redis list; expose `GET /api/v1/queue/dlq` for inspection; fire Telegram alert on any DLQ entry
- [ ] Tests: bucket enforces stagger; idempotency key replays as no-op; DLQ entry fires alert

## 4.2 Referral finder
- [ ] `agents/referral_finder.py` — `LinkedInClient.get_connections()` filtered by company
- [ ] Rank: 1st > 2nd degree, shared college/city, recent post activity, role relevance
- [ ] Exclude HR/recruiter titles (use email channel instead)
- [ ] Per-contact DM draft: mutual context + one-line role fit + specific ask
- [ ] HITL: user picks which contacts to message

## 4.3 Outreach agent
- [ ] `agents/outreach.py` — email via `EmailTool.send()`; LinkedIn DM via `LinkedInClient.send_dm()`
- [ ] Personalises email with: company name, role, one insight from `CompanyProfile` (fetched via `CompanyRepository.get_or_research()`)
- [ ] Per-send audit row in `outreach` table; never DM same (person + role) pair twice
- [ ] Uses `outreach_queue` Celery tasks — never sends synchronously

## 4.4 Form filler
- [ ] `agents/form_filler.py` — Playwright fills mapped fields from `UserProfile`; uploads correct `ResumeVersion` PDF
- [ ] LLM answers screening Qs from `Resume` facts only (no invention); answers in `form_screening` model per `config.yaml`
- [ ] `CaptchaSolver` integration via `CaptchaPort`
- [ ] Post-submit screenshot saved via `FileStoragePort`; path stored in `applications.submit_screenshot`
- [ ] On any failure: log, fire Telegram alert, set `applications.status = "form_failed"` — no auto-retry

## 4.5 Tracker
- [ ] `agents/tracker.py` — `EmailTool.poll_inbox()` every 30 min via Celery Beat
- [ ] Classifier LLM via `LLMRouter` (`mail_classifier` task): `interview_invite | rejection | assessment | follow_up_needed | auto_reply` with confidence score
- [ ] Match to application: sender domain + subject thread-id; update `applications.status` + `last_reply`
- [ ] State machine in `services/application_state.py` as pure function: `transition(current, event) -> new_status`; `events = {email_label} ∪ {manual_actions}`
- [ ] `ghosted` rule: no reply after 14 days → scheduler fires `ghost_check` task daily

## 4.6 Follow-up sequencer
- [ ] `agents/followup.py` — daily scheduler task checks `applications` + `follow_ups` table
- [ ] +7d: draft nudge → write `follow_ups` row (status=draft) → HITL → on approve set status=approved → `send_email` queued
- [ ] +14d: tag application `ghosted`; draft second DM to referral contact → `follow_ups` row
- [ ] +21d: tag `archived`; stop; no further follow_ups rows created
- [ ] Each draft references original `outreach.message` thread subject for context

## 4.7 Notifier
- [ ] `notifications/email_digest.py` — Jinja2 `notifications/templates/digest.html` + `digest_plain.txt`; sent daily at 08:00; covers: jobs found, applied, replies, follow-ups needed
- [ ] `notifications/templates/` — create all templates:
  - `digest.html` + `digest_plain.txt` — daily summary
  - `interview_invite.html` — immediate alert
  - `outreach_ready.html` — batch approval waiting
  - `error_alert.html` — agent error / queue stuck
- [ ] `notifications/telegram_bot.py` — `TelegramBot` implementing `NotifierPort`; `send_alert(event, payload)`; per-event opt-in from `config.yaml`
- [ ] All Telegram messages plain text (no HTML formatting); include deep link to approval URL

## 4.8 Scheduler
- [ ] `scheduler/jobs.py` — `Scheduler` Protocol; APScheduler embedded (default); Celery Beat behind same protocol for prod
- [ ] Wires all jobs per REQUIREMENTS §17:
  - Job search: every 6h
  - LinkedIn post scraper: every 4h
  - Mail watcher: every 30 min
  - Follow-up sequencer: daily 09:00
  - Stale application check (ghost rule): daily 08:00
  - Company research cache cleanup: weekly

## Tests
- Queue: bucket enforces stagger; idempotency key replays no-op; DLQ entry triggers alert
- Outreach: `CompanyProfile` insight appears in sent email body; per mocked `EmailTool`
- Tracker: classifier confusion matrix on `eval/data/sample_emails/` fixtures; state machine 100% branch; ghost tag at +14 verified
- Form filler: dry-run fills fields correctly; captcha failure interrupts; failure sets `form_failed`
- Follow-up: day-7/14/21 transitions correct; +21 stops creating new rows
- DLQ: 3 consecutive failures → DLQ entry → alert fired (mocked Telegram)
- Notifier: digest renders both HTML and plain text; Telegram dry-run sends no real messages

Done: 24h unattended run on sandbox Gmail, no duplicates, no missed replies. Update `STATE.md`.
