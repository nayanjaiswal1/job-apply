# Requirements

LangGraph multi-agent job hunting system: search → score → tailor → apply → track → follow up → prep.

## 1. Architecture

| Layer | Tech |
|---|---|
| Orchestration | LangGraph (stateful graph + checkpointer) |
| LLM | LangChain LCEL + output parsers |
| LLM router | LiteLLM |
| Providers | OpenAI, Anthropic, Google, Groq, Minimax, Mistral, Ollama, Together |
| Model config | Per-agent in `config.yaml` (primary, fallback, min_mode) |
| Eval | Custom runner — benchmark on actual tasks |
| Persistence | SQLite (dev) → Postgres (prod) via SQLAlchemy 2.x + Alembic |
| Queue | Celery + Redis |
| Vector | ChromaDB |
| Browser | Playwright + playwright-stealth |
| API | FastAPI |
| UI | Next.js |
| Obs | LangSmith + structlog + OTel |
| Scheduler | APScheduler (embedded) or Celery Beat |

## 2. Agents (12 LangGraph nodes)

| Agent | Responsibility |
|---|---|
| Orchestrator | Routes, manages state, fires HITL interrupts |
| Job Search | Multi-platform scrape/API → filter → dedup → LLM score |
| Company Research | Funding, tech stack, news, Glassdoor — cached per company |
| Resume | Parse → JD diff → ATS rewrite → version |
| Cover Letter | Per-job personalised letter |
| Referral Finder | Find + rank connections, draft DMs |
| Outreach | Recruiter email + LinkedIn DM via rate-limit queue |
| Form Filler | Playwright form submit for platforms with no API |
| Tracker | IMAP poll, classify replies, state machine |
| Follow-up | Scheduled nudges; escalates to ghosted |
| Prep | Interview Q gen + embedding dedup bank |
| Notifier | Email digest + Telegram alerts |

## 3. Resume parsing (input)

- PDF: pdfplumber (primary) → pymupdf (fallback for scanned)
- DOCX: python-docx
- Multi-column: detect + flatten column order
- Output: `summary, skills, experience[], education[], certifications[], links[]`
- Store raw + structured; re-parse only on new upload

## 4. Platform access

API-first; on failure (no API, 403, rate-limited) → Playwright fallback.

### 4a. Matrix

| Platform | Primary | Fallback |
|---|---|---|
| LinkedIn | OAuth2 REST | Playwright |
| Indeed | Publisher API | Playwright |
| Naukri | — | Playwright only |
| Wellfound | — | Playwright only |
| Internshala | — | Playwright only |
| Monster | Partner API (limited) | Playwright |
| Company pages | — | Playwright |

### 4b. Browser automation

- Headless Chromium + playwright-stealth
- Human-like: random mouse, 50–120 WPM typing, random scroll
- Delays: 1–4s between actions, 3–8s between pages
- Proxy rotation: one residential proxy per platform; never share IPs
- Cookie/session persistence per platform; auto re-login on expiry
- IP warm-up: low rate first 48h
- Screenshot on every failure → `logs/screenshots/`
- Respect robots.txt; log and skip if disallowed

### 4c. Captcha

- Stealth reduces triggers
- 2captcha / capsolver for reCAPTCHA v2/v3, hCaptcha
- On solver fail → pause + user alert
- Fingerprint randomisation: viewport, UA, timezone, language per session

### 4d. Unified Job schema

```python
Job(
  id: str,              # SHA-256(title + company + location)
  title: str,
  company: str,
  location: str,
  platform: str,        # "linkedin" | "naukri" | ...
  url: str,
  jd_text: str,
  salary_range: str | None,
  remote: bool,
  experience_level: str,  # intern|junior|mid|senior|lead
  posted_at: datetime,
  scraped_at: datetime,
  match_score: float,   # 0.0–1.0 LLM-scored vs resume
  status: str,
  source_type: str,     # "api" | "browser" | "linkedin_post"
)
```

## 5. LinkedIn post scraper

Captures roles posted informally before they hit job boards.

- Hashtags: `#hiring`, `#jobopening`, `#wearehiring`, `#nowhiring`
- Also scrape target companies' LinkedIn pages
- LLM extracts: company, role, contact, apply instructions
- Dedup against jobs table
- `source_type="linkedin_post"` — often has a named contact
- Schedule: every 4h via Celery Beat

## 6. Preferences (pre-filter before LLM scoring)

```python
Preferences(
  min_salary: int | None,
  preferred_locations: list[str],
  remote: "remote" | "hybrid" | "onsite" | "any",
  role_levels: list[str],         # ["junior", "mid"]
  target_roles: list[str],
  blacklist_companies: list[str],
  blacklist_keywords: list[str],
  preferred_tech: list[str],
  max_applications_per_day: int,
)
```

Rule-based pre-filter; no LLM tokens spent on irrelevant jobs.

## 7. Company research

Once per company; 7-day cache.

- Sources: Crunchbase, LinkedIn company page, company tech blog, news (Tavily/SerpAPI), Glassdoor
- Output: funding stage, team size, tech stack, recent news, glassdoor rating, culture keywords
- Used by: resume (tone), cover letter (personalise), referral finder (talking points)
- Cache key = company slug

## 8. Resume agent

### 8a. Core principle
Output must be indistinguishable from human-written. Recruiters spot AI-generated resumes and discard. **The agent never writes new experience. It only reshapes, reorders, and refines what the candidate provided.**

### 8b. Banned patterns

| Pattern | Example | Why |
|---|---|---|
| Filler openers | Spearheaded, Leveraged, Orchestrated, Championed | Overused LLM vocab |
| Vague impact | "Improved performance significantly" | No number |
| Passive | "Was responsible for", "Helped to" | Weak |
| Em-dash abuse | "Built system — resulted in..." | LLM tell |
| Nested bullet symbols | • → ◦ → ▪ | Non-ATS |
| Unicode decorators | ✅ ➤ ★ ◆ | Red flag |
| Buzzword stacking | "Dynamic, results-driven, passionate" | Cliché |
| Uniform sentence length | Every bullet 12–15 words | LLM signal |
| Adjective inflation | "Exceptional", "Outstanding", "Cutting-edge" | Unverifiable |
| First-person | "I built", "I led" | Never in resumes |

### 8c. Human-written looks like
- Bullets vary in length (some 8 words, some 18) — not uniform
- Numbers specific: "reduced latency from 420ms to 180ms" not "improved by 50%"
- Plain verbs: built, wrote, migrated, fixed, cut, shipped, reviewed
- Some bullets intentionally imperfect — a real person doesn't polish every line equally
- Summary: 2 sentences max, role-specific, no adjectives
- Skills: plain comma-separated list — no bars, stars, icons
- Formatting: one font, standard headers, no tables/columns/text boxes

### 8d. Enforced prompt rules
- Allowed verbs only: built, wrote, designed, migrated, reduced, increased, shipped, reviewed, fixed, led, ran, set up, debugged, deployed, integrated, automated, documented, tested, refactored, cut, moved, added
- Every bullet contains one specific number OR a named technology
- No bullet starts with: Spearheaded, Leveraged, Orchestrated, Championed, Fostered, Utilized, Facilitated, Streamlined, Synergized, Revolutionized
- Vary sentence length: mix short (<10 words) with longer
- No Unicode symbols, no em-dashes, no decorative chars
- No adjectives unless factual ("distributed", "real-time")
- Plain text output — no markdown bold, no asterisks

### 8e. Modes

**Targeted edit (match score ≥ 0.55)**
1. Pull JD → extract required skills, keywords, tech, experience level
2. Diff: what's in JD but missing or weak in resume
3. Inject missing keywords naturally into existing bullets — never as a keyword dump
4. Rewrite weakest 1–2 bullets per role for specificity
5. Rewrite summary (2 sentences) for this role
6. Don't touch sections that already match

**Full regeneration (match score < 0.55)**
1. Pull all experience from parsed bank
2. Select/reorder most relevant roles/bullets for this JD
3. Reframe bullets to emphasise what the JD values — same facts, different angle
4. Rebuild summary
5. Choose format: ATS-plain or human-readable
6. Still uses only candidate-provided facts

**Skills gap report (both modes)**
- List JD skills missing from resume: critical / important / nice-to-have
- Suggest where adjacent experience could be surfaced
- Flag uncoverable gaps so candidate knows before applying

### 8f. Formats

| Format | When | Structure |
|---|---|---|
| ATS-plain | Big portals, Naukri, Indeed | Single column, no tables, standard fonts |
| Human-readable | Direct recruiter email, Wellfound, startups | Light visual structure, no icons |
| One-pager | Startups, < 3y experience | Strict 1 page, tightest bullets |

### 8g. AI detection (pre-save)
- gptzero API — flag if score > 0.4
- Internal pattern check: banned verb count, uniform length, em-dash count
- If flagged → rewrite with stricter constraints
- Log detection score per version

### 8h. HITL
- Show unified diff (only changed lines highlighted)
- Show ATS score before/after
- Show AI detection score
- User can edit any bullet inline
- User must explicitly approve — never auto-save

### 8i. Versioning
- Filename: `resume_v{n}_{company}_{role}.pdf` + `.txt` (ATS plain copy)
- Store: version number, ATS score, AI detection score, application link

### 8j. Feedback loop
- After 10+ rejections same version → flag for review
- Surface JD keywords consistently missing in rejected apps
- Compare ATS scores rejected vs interviewed → identify threshold
- Suggest consistently weakest bullets

## 9. Cover letter agent

One personalised letter per application. Same human-writing rules as resume.

- Inputs: structured resume + JD text + `CompanyProfile`
- Tone: detect culture → startup (direct, informal) vs enterprise (professional, not stiff)
- Structure: specific hook (why this company, not "I am excited") → 2 experience points with numbers → clear ask
- Length: 180–240 words
- Banned: "I am passionate about", "I would be a great fit", "Please find attached", "To whom it may concern", "I am writing to express my interest", "leverage my skills", "dynamic team"
- No exclamation marks, no "thrilled/excited/delighted", no hollow flattery
- AI detection check before saving
- HITL preview
- Versioned + linked to application

## 10. Referral finder

Per target company before outreach.

- Query LinkedIn connections filtered by company
- Rank: 1st > 2nd degree, same college/city, recent activity, role relevance
- Exclude HR/recruiter titles (use email channel)
- Per-person draft DM:
  - Reference mutual or shared background
  - One line on role fit
  - Specific ask: "Would you be open to referring me or sharing context about the team?"
- HITL pick list

## 11. Outreach

### Recruiter email
- Personalise: company name, role, one company-research insight
- SMTP via Gmail OAuth2
- Max 50/day; 5–15min stagger
- Track: sent → opened (if read receipt) → replied

### LinkedIn DM (referral)
- Max 20/day; 60–180s delay between
- LinkedIn OAuth2 first; Playwright fallback
- Never DM same person twice for same role

### Rate-limit queue
```
job scored → outreach_queue (Celery)
  → token bucket check
  → if allowed: send → log → update state
  → if blocked: requeue with delay
```

## 12. Form filler

For platforms with no email/API path.

- Playwright fills from structured resume
- Field mapping: name, email, phone, years exp, notice period, salary expectation, current location
- Upload correct resume version
- Screening Qs: LLM answers from resume + preferences
- Captcha: solver API
- Post-submit screenshot → proof of application
- On failure: log + alert; **no auto-retry** (avoid duplicates)

## 13. Tracker

### State machine
```
discovered → applied → outreach_sent → interview_scheduled → offer_received
                                    ↘ rejected
                                    ↘ ghosted (14-day rule)
                                    ↘ withdrawn
```

### Mail watcher (IMAP)
- Poll every 30 min via `imaplib2`; Gmail OAuth2
- Match by sender domain + subject keywords

| Label | Trigger keywords |
|---|---|
| `interview_invite` | schedule, interview, call, meet |
| `rejection` | not moving forward, other candidates, unfortunately |
| `assessment` | assignment, test, coding challenge, hackerrank |
| `follow_up_needed` | vague reply with no next step |
| `auto_reply` | thank you for applying, we received |

- Update status on match
- Staleness: no reply +14d → tag `ghosted`, draft follow-up

## 14. Follow-up sequencer

Daily check.

| Day | Action |
|---|---|
| +7 | Draft polite nudge → HITL → send |
| +14 | Tag `ghosted`; draft 2nd LinkedIn DM to referral (optional) |
| +21 | Tag `archived`; stop |

Each follow-up references original thread subject.

## 15. Prep agent

- Pull JD + company tech blog + Glassdoor interview reports
- Generate questions per category: technical, behavioural, system design, role-specific
- Embed → cosine > 0.88 → skip (dedup)
- Store: `question, model_answer, tags, difficulty, source_jds`
- Output per role: markdown + PDF
- Bank persists across roles

## 16. HITL checkpoints (interrupt_before)

| Checkpoint | Trigger | Action |
|---|---|---|
| Resume diff | Before saving modified resume | Approve / edit |
| Cover letter | Before attaching | Approve / rewrite |
| Outreach preview | Before queuing | Approve batch / edit individual |
| Apply confirm | Before form submission | Confirm resume version + cover |
| Referral list | Before LinkedIn DM sweep | Pick targets |
| Follow-up | Before sending nudge | Approve / skip |
| Captcha failed | Solver gives up | Manual solve or skip |

## 17. Schedule

| Task | Frequency |
|---|---|
| Job search (all) | Every 6h |
| LinkedIn post scraper | Every 4h |
| Mail watcher | Every 30 min |
| Follow-up sequencer | Daily 09:00 |
| Stale check | Daily 08:00 |
| Company research cleanup | Weekly |

Skip re-scrape if already in DB within 24h.

## 18. Notifications

| Event | Channel |
|---|---|
| Interview invite | Email + Telegram (immediate) |
| Daily digest | Email 08:00 |
| Outreach batch ready | Email / Telegram |
| Application submitted | Telegram |
| Captcha solver failed | Telegram (immediate) |
| Agent error / queue stuck | Telegram (immediate) |

- Email: Jinja2 HTML via SMTP
- Telegram: python-telegram-bot
- All opt-in in `config.yaml`

## 19. Dedup

| Target | Method | Rule |
|---|---|---|
| Job listings — exact | SHA-256(title+company+location) | Exact match → skip |
| Job listings — fuzzy | Cosine on JD embedding | > 0.92 → skip |
| Interview questions | Cosine on Q embedding | > 0.88 → skip |
| Outreach targets | SHA-256(person+company) | Already contacted this role → skip |
| Cover letters | Not deduped — unique per app | — |

## 20. Errors & observability

- LangSmith: trace every agent run (inputs, outputs, tokens, latency)
- structlog: JSON with `job_id, agent, action, status` — no PII, no message content
- tenacity: exp backoff on LLM, SMTP, IMAP, scrape
- DLQ: failed sends → Redis DLQ → user alert
- Health: `GET /health` — agent status, queue depth, last successful run per agent
- Screenshots: every Playwright failure → `logs/screenshots/{ts}_{platform}.png`
- Scrape: log → retry → after 3 fails → alert + skip platform for run

## 21. Security

| Concern | Solution |
|---|---|
| API keys | `.env` via pydantic-settings; never hardcoded |
| LinkedIn OAuth | PKCE; refresh token AES-encrypted |
| Email auth | Gmail OAuth2 or app password; IMAP over TLS |
| Playwright sessions | Cookie files AES-encrypted; not committed |
| Proxies | Residential pool; creds in `.env` |
| Resume / cover files | Local in `data/resumes/`; never cloud |
| Logs | Scrubbed: no PII, no email content |
| Config | `config.yaml` (non-secret) + `.env` (secrets) |

## 22. Data models (SQL)

```sql
CREATE TABLE jobs (
  id           TEXT PRIMARY KEY,  -- SHA-256
  title        TEXT NOT NULL,
  company      TEXT NOT NULL,
  location     TEXT,
  platform     TEXT,
  url          TEXT,
  jd_text      TEXT,
  salary_range TEXT,
  remote       BOOLEAN,
  exp_level    TEXT,
  match_score  REAL,
  status       TEXT DEFAULT 'discovered',
  source_type  TEXT,
  posted_at    TIMESTAMP,
  scraped_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE companies (
  id               TEXT PRIMARY KEY,
  name             TEXT,
  funding_stage    TEXT,
  team_size        TEXT,
  tech_stack       TEXT,           -- individual columns for SQL filters only
  glassdoor_rating REAL,
  summary          TEXT,           -- JSON CompanyProfile; authoritative source of truth
  researched_at    TIMESTAMP
);

CREATE TABLE applications (
  id              TEXT PRIMARY KEY,
  job_id          TEXT REFERENCES jobs(id),
  resume_version  TEXT,
  cover_letter    TEXT,
  sent_at         TIMESTAMP,
  status          TEXT DEFAULT 'applied',
  last_reply      TEXT,
  last_reply_at   TIMESTAMP,
  submit_screenshot TEXT
);

CREATE TABLE outreach (
  id         TEXT PRIMARY KEY,
  job_id     TEXT REFERENCES jobs(id),
  person     TEXT,
  company    TEXT,
  channel    TEXT,    -- email | linkedin_dm
  message    TEXT,
  sent_at    TIMESTAMP,
  reply      TEXT,
  reply_at   TIMESTAMP
);

CREATE TABLE questions (
  id              TEXT PRIMARY KEY,
  text            TEXT NOT NULL,
  embedding       BLOB NOT NULL,
  category        TEXT NOT NULL,  -- technical|system_design|behavioural|role_specific|company_specific
  difficulty      TEXT,           -- easy|medium|hard
  model_answer    TEXT,
  user_answer     TEXT,
  tags            TEXT,           -- JSON array
  source_jds      TEXT,           -- JSON array of job IDs; grows as near-dupes merge in
  confidence      TEXT DEFAULT 'unseen',  -- unseen|shaky|comfortable|confident
  practice_count  INTEGER DEFAULT 0,
  last_practiced  TIMESTAMP,
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE resume_versions (
  id              TEXT PRIMARY KEY,
  filename        TEXT,
  sections        TEXT,   -- JSON
  ats_score       REAL,
  ai_detect_score REAL,   -- reject if > 0.4
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE follow_ups (
  id             TEXT PRIMARY KEY,
  application_id TEXT REFERENCES applications(id),
  day_offset     INT,   -- 7 | 14 | 21
  channel        TEXT,  -- "email" | "linkedin_dm"
  draft          TEXT,
  status         TEXT DEFAULT 'draft',  -- draft|approved|sent|skipped
  sent_at        TIMESTAMP,
  created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 23. Folder structure

```
job-agent/
├── agents/                     # 12 LangGraph nodes
├── tools/
│   ├── scrapers/               # base, session_store, proxy_pool, per-platform
│   ├── resume_parser.py
│   ├── email_tool.py
│   ├── linkedin_api.py
│   ├── ats_scorer.py
│   ├── ai_detector.py
│   ├── embedder.py
│   ├── captcha_solver.py
│   ├── research_tool.py
│   └── llm_router.py
├── ports/                      # Protocol interfaces (hexagonal)
├── state/                      # TypedDict schema + checkpointer
├── db/                         # models, repositories, migrations
├── queue/                      # Celery tasks, rate_limiter, dlq
├── scheduler/
├── notifications/
├── api/                        # FastAPI
├── ui/                         # Next.js
├── data/
│   ├── resumes/
│   └── cover_letters/
├── logs/screenshots/
├── eval/
├── config.yaml
├── .env.example
└── pyproject.toml
```

## 24. LLM config (LiteLLM)

```yaml
models:
  orchestrator:    { primary: claude-sonnet-4-6, fallback: gpt-4o,                 min_mode: gpt-4o-mini }
  resume_rewrite:  { primary: claude-sonnet-4-6, fallback: gpt-4o,                 min_mode: ollama/llama3.1:8b }
  cover_letter:    { primary: claude-sonnet-4-6, fallback: minimax/abab6.5s-chat,  min_mode: ollama/mistral:7b }
  job_scoring:     { primary: gpt-4o-mini,                fallback: gemini/gemini-1.5-flash, min_mode: groq/llama3-8b-8192 }
  company_research:{ primary: gpt-4o,                     fallback: claude-sonnet-4-6, min_mode: gpt-4o-mini }
  referral_dm:     { primary: claude-sonnet-4-6, fallback: gpt-4o,                 min_mode: ollama/mistral:7b }
  mail_classifier: { primary: gpt-4o-mini,                fallback: groq/llama3-8b-8192,    min_mode: groq/llama3-8b-8192 }
  form_screening:  { primary: gpt-4o-mini,                fallback: gemini/gemini-1.5-flash, min_mode: ollama/llama3.1:8b }
  interview_prep:  { primary: gpt-4o,                     fallback: claude-sonnet-4-6, min_mode: gpt-4o-mini }
```

Providers: OpenAI, Anthropic, Google, Groq, Minimax, Mistral, Ollama (local), Together, Cohere.

### Minimize mode
`--minimize` → every agent uses `min_mode`. For bulk testing, dev, cost cuts.

```
python -m job_agent.graph --minimize
python -m job_agent.graph --agent resume
python -m job_agent.graph --dry-run
```

### Fallback
LiteLLM retries on fallback on error/rate-limit/timeout. Every fallback logged with model, reason, latency.

## 25. LLM evaluator

Benchmark on **actual tasks** before trusting in prod.

### Flow
```
real resume + 5 real JDs → same prompt to each candidate model → score on 4 dims → rank → optionally write winners to config.yaml
```

### Scoring dims

| Dim | Measure | Target |
|---|---|---|
| AI detectability | GPTZero | < 0.2 |
| ATS keyword match | % of JD keywords in output | > 85% |
| Banned violations | Count of blacklisted words/phrases | 0 |
| Bullet length variance | Std dev of word counts | > 3.5 |

### Commands
```
python eval.py --task resume_rewrite --jds data/sample_jds/
python eval.py --task cover_letter   --jds data/sample_jds/
python eval.py --task job_scoring    --jobs data/sample_jobs.json
python eval.py --task mail_classify  --emails data/sample_emails/
python eval.py --task resume_rewrite --models claude-sonnet-4-6,gpt-4o
python eval.py --all
python eval.py --all --auto-update-config
python eval.py --all --auto-update-config --log eval/results/$(date +%Y-%m).json
```

`--auto-update-config` writes winners into `config.yaml` as `primary`. Run monthly.

### Folder
```
eval/
├── eval.py
├── tasks/                # resume_rewrite, cover_letter, job_scoring, mail_classify
├── data/                 # sample_jds/, sample_jobs.json, sample_emails/
└── results/              # timestamped JSON (gitignored)
```

## 26. Dependencies

```
# Core
langgraph>=0.2
langchain>=0.3
langchain-openai
langchain-anthropic

# Router + providers
litellm>=1.40
ollama

# Browser
playwright
playwright-stealth

# Resume parsing
pdfplumber
pymupdf
python-docx

# Queue + scheduling
celery[redis]
redis
apscheduler

# Vector
chromadb

# DB
sqlalchemy
alembic

# Email
imaplib2
google-auth-oauthlib

# Scrape / search
beautifulsoup4
httpx
tavily-python

# Captcha
2captcha-python

# Notifications
python-telegram-bot

# Obs
langsmith
structlog
opentelemetry-sdk

# Resilience
tenacity

# AI detection (Phase 3 optional dep)
gptzero>=1.0

# Utils
python-dotenv
pydantic
pyyaml
cryptography
jinja2
# PDF generation via Playwright page.pdf() — no weasyprint needed

# Quality
ruff
mypy
black
pytest
pytest-asyncio
pytest-cov
respx
hypothesis
import-linter
detect-secrets
```

## 27. Build order

See `plans/phase-{1..5}.md`. Active phase pointer in `STATE.md`.
