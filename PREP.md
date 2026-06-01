# Interview Prep

Questions generated per JD → embedded → deduplicated into one growing personal bank → study with confidence tracking.

## How it works

```
You apply to a job
  → prep agent pulls JD + company tech blog + Glassdoor interview reports
  → LLM generates questions per category
  → each question embedded + checked against bank (cosine > 0.88 → merge, not insert)
  → new questions added; merged ones gain another source_jds pointer
  → bank grows, never duplicates
```

When the same question appears across 5 JDs, it appears once in the bank — tagged as relevant to all 5 companies. Study it once, you're prepared for all five.

---

## Question categories

| Category | What it covers |
|---|---|
| `technical` | Coding, debugging, language-specific, tools |
| `system_design` | Architecture, scale, trade-offs — generated for mid/senior roles only |
| `behavioural` | STAR-format situations (conflict, failure, leadership, ownership) |
| `role_specific` | Skills specific to the JD (e.g. "describe your CI/CD setup") |
| `company_specific` | Why this company, culture fit, product knowledge |

---

## DB schema (extended from REQUIREMENTS §22)

```sql
CREATE TABLE questions (
  id              TEXT PRIMARY KEY,
  text            TEXT NOT NULL,
  embedding       BLOB NOT NULL,
  category        TEXT NOT NULL,  -- see categories above
  difficulty      TEXT,           -- easy | medium | hard
  model_answer    TEXT,           -- AI-generated starting point (STAR / technical walkthrough)
  user_answer     TEXT,           -- user's own notes, refined answer
  tags            TEXT,           -- JSON array: ["python", "distributed systems"]
  source_jds      TEXT,           -- JSON array of job IDs this came from
  confidence      TEXT DEFAULT 'unseen',  -- unseen | shaky | comfortable | confident
  practice_count  INTEGER DEFAULT 0,
  last_practiced  TIMESTAMP,
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

`source_jds` is a JSON array — starts as `["job_abc"]`, becomes `["job_abc", "job_xyz"]` when a near-duplicate merges in.

---

## Deduplication (merge, not skip)

```
new question generated
  → embed
  → query Chroma: top-3 similar from bank
  → if similarity > 0.88:
      append new job_id to existing question.source_jds
      if new question has harder difficulty → update difficulty
      discard new, keep existing
  → else:
      insert as new question
```

Result: one question covers many companies. Study view shows "also relevant for: Google, Stripe, Razorpay".

---

## Model answer format

### Behavioural (STAR)
```
Situation: [1-2 sentences, specific context from resume]
Task: [what you were responsible for]
Action: [what you did — use resume bullets as source material]
Result: [specific outcome with number if possible]
```

AI uses only the candidate's actual experience (from resume_versions). Never invents.

### Technical
```
Short direct answer (1-2 sentences)
→ Key points:
  - point 1
  - point 2
→ Example from my experience: [if applicable, from resume]
→ Edge cases / trade-offs: [if relevant]
```

### System design
```
→ Clarify: what to ask before designing
→ High-level design: components + data flow
→ Deep dive: the component the JD cares about most
→ Trade-offs: what you'd do differently at 10x scale
```

---

## Confidence levels

User updates confidence after each practice session.

| Level | Meaning | Study priority |
|---|---|---|
| `unseen` | Never practiced | Always show first |
| `shaky` | Tried but not solid | High |
| `comfortable` | Can answer well | Medium |
| `confident` | Could answer half-asleep | Low (review occasionally) |

---

## Study modes (UI)

### 1. By job (`/prep/[job_id]`)
All questions for one specific application. Useful right before an interview.
- Shows company-specific questions first
- Then technical + system_design
- Then behavioural

### 2. Full bank (`/prep`)
All questions across all jobs, deduplicated.
- Filter: category, difficulty, confidence, tags, company
- Sort: confidence asc (default — worst first), created_at, difficulty
- Search: keyword in question text

### 3. Focus session (`/prep/session`)
Timed study mode.
- Pick: category filter + number of questions (default 10)
- Cards shown one at a time — question first, flip to see model answer
- After flip: user rates `shaky / comfortable / confident`
- Session summary: N practiced, N improved, N still shaky

---

## UI routes (add to UI.md)

| Route | Purpose |
|---|---|
| `/prep` | Full question bank — filter, sort, search |
| `/prep/[job_id]` | Questions for one specific application |
| `/prep/session` | Focus session — card flip + confidence rating |
| `/prep/[question_id]` | Single question — edit user_answer, view source JDs |

---

## Export

| Format | When |
|---|---|
| Markdown `prep_{role}.md` | Per-job quick reference, night before interview |
| Anki CSV (`.csv`) | Import into Anki for spaced repetition |

Anki CSV format:
```
"Question text","Model answer","Tags","Difficulty"
```

Export button on `/prep/[job_id]` and `/prep` (filtered view).

---

## API endpoints (FastAPI)

```
GET  /api/v1/prep/questions              — full bank, supports filter/sort/search QPs
GET  /api/v1/prep/questions/[id]
PUT  /api/v1/prep/questions/[id]         — update user_answer, confidence
GET  /api/v1/prep/jobs/[job_id]          — questions for one application
POST /api/v1/prep/session                — start session {category, n}
PUT  /api/v1/prep/session/[id]/answer    — submit confidence rating
GET  /api/v1/prep/export/[job_id]        — download markdown
GET  /api/v1/prep/export/[job_id]/anki  — download Anki CSV
```

---

## Generation trigger

Runs automatically when `status` changes to `applied`.
Can also be triggered manually from the job detail page.

Generates: 3–5 technical, 2–3 system_design (mid/senior only), 4–5 behavioural, 3–4 role_specific, 2 company_specific.

Total: 14–19 questions per job before dedup. After dedup with existing bank, typically 4–8 net new questions.

---

## Tests

- Dedup: near-duplicate question merges into existing, source_jds updated
- Dedup: distinct question inserts as new
- Model answer: behavioural always has STAR structure; never references facts not in resume
- Generation: correct categories per experience level (no system_design for intern)
- Confidence update: practice_count increments, last_practiced set
- Export: markdown renders all questions; Anki CSV is valid format
- Session: low-confidence questions shown before high-confidence
