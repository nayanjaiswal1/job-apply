# User Profile

Single-user system. One profile row. Everything else (resume, preferences, applications) hangs off it.

## Data model

```sql
CREATE TABLE user_profile (
  id               TEXT PRIMARY KEY DEFAULT 'me',  -- always one row
  full_name        TEXT NOT NULL,
  email            TEXT NOT NULL,
  phone            TEXT,
  linkedin_url     TEXT,
  github_url       TEXT,
  portfolio_url    TEXT,
  current_title    TEXT,
  current_company  TEXT,
  years_exp        INTEGER,
  notice_period    TEXT,       -- "immediate" | "2 weeks" | "1 month" | "3 months"
  current_location TEXT,
  target_locations TEXT,       -- JSON array
  expected_salary  INTEGER,
  currency         TEXT DEFAULT 'INR',
  onboarding_step  INTEGER DEFAULT 1,
  preferences      JSONB,
  updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Resume content lives in `resume_versions` (already in §22). Profile = contact + work context. Resume = full structured content.

## First-run onboarding (4 steps, wizard UI)

Triggered when `user_profile` row doesn't exist. Redirects to `/onboarding`.

```
Step 1 — Basics
  full_name, email, phone, LinkedIn URL, GitHub URL, portfolio URL

Step 2 — Work context
  current_title, current_company, years_exp, notice_period, current_location, expected_salary, currency

Step 3 — Upload resume
  Drag-drop PDF or DOCX → parser runs → structured preview shows
  User edits any section inline (experience bullets, skills, education)
  Approve → saved as resume_version v1

Step 4 — Job preferences
  Same as Preferences model in REQUIREMENTS §6
  target_roles, preferred_locations, remote preference, blacklists, max_applications_per_day

Done → redirect to dashboard
```

Wizard state persisted in DB as it progresses — refresh-safe.

## Resume update flow

`/profile/resume` page:

1. Upload new PDF/DOCX
2. Parser runs → shows diff: old structured data vs new
3. User reviews, edits inline if needed
4. Approve → new `resume_versions` entry (v{n+1})
5. Old versions remain; each linked to the applications that used them

## Profile edit

`/profile` page — always editable. Separate from resume.

Fields: all user_profile columns. Save is instant (no approval needed — not sent anywhere yet).

Notice period + salary are used as defaults in form filler answers. User can override per-application.

## What depends on profile

| Depends on | Uses |
|---|---|
| Resume agent | resume_versions latest |
| Cover letter agent | full_name, current_title |
| Form filler | all profile fields as defaults |
| Outreach | email for sent-from |
| Job scoring | preferences (target_roles, salary, remote) |
| Tracker | email for IMAP match |

## API endpoints (FastAPI)

```
GET  /api/v1/profile
PUT  /api/v1/profile
GET  /api/v1/profile/resume          — current + version history
POST /api/v1/profile/resume          — upload new file → triggers parse
PUT  /api/v1/profile/resume/[id]     — edit parsed sections
POST /api/v1/profile/resume/[id]/approve — save as active version
GET  /api/v1/profile/preferences
PUT  /api/v1/profile/preferences
GET  /api/v1/onboarding/status       — {step: 1..4 | "complete"}
```
