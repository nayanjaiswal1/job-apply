# Phase 3 — Intelligence Layer

**Goal:** every LLM-driven agent — scoring, research, resume, cover letter, prep — with eval gating model choices before production.

**Exit:** every agent meets eval thresholds (REQUIREMENTS §25); HITL resumes cleanly from checkpoint; agents stay within `config.yaml` budget envelopes.

## 3.1 Eval runner (build first — needs Phase 2 fixtures)
- [ ] Confirm `eval/data/` fixtures exist (Phase 2 task 2.10) before starting
- [ ] `eval/eval.py` — candidate models × fixed task fixtures
- [ ] Score dims: AI detectability (<0.2), ATS keyword % (>85), banned-pattern count (0), bullet length variance (>3.5)
- [ ] Tasks: `resume_rewrite, cover_letter, job_scoring, mail_classify`
- [ ] `--auto-update-config` writes winners to `config.yaml`
- [ ] Baseline at `eval/results/baseline.json`; CI fails on >5% regression

## 3.2 Scoring + analysis tools (build before agents that use them)
- [ ] `tools/ats_scorer.py` — `AtsScorer.score(resume_txt, jd_txt) -> float` (0–100); keyword overlap + section coverage; fast, no LLM; used by resume agent HITL diff + `resume_versions.ats_score`
- [ ] `tools/ai_detector.py` — `AiDetector.score(text) -> float` (0–1); gptzero API primary + internal pattern check (banned verb count, uniform bullet length, em-dash density) always-on fallback; never block pipeline on API outage — fall back to pattern-only score

## 3.3 Job-search agent
- [ ] `agents/job_search.py` — pre-filter → batched LLM scoring via `LLMRouter` → write `match_score`
- [ ] Score cached on `job.id`; cheap model per `config.yaml`

## 3.4 Company-research agent
- [ ] `agents/company_research.py` — uses `ResearchTool` (Tavily/SerpAPI) + Glassdoor scrape + tech blog
- [ ] Cache = `companies` table; check `researched_at`; re-research if >7 days old
- [ ] Output: `CompanyProfile` pydantic stored as JSON in `companies.summary`; parsed back on read
- [ ] `CompanyRepository.get_or_research(company_slug)` — returns cached or triggers fresh research

## 3.5 Document generator (build before resume agent — DOCS.md)
- [ ] `tools/doc_generator.py` — `render_resume(data, fmt) -> (pdf_bytes, txt_bytes)` and `render_cover_letter(body, profile) -> bytes`
- [ ] 3 resume HTML/CSS templates (`ats_plain`, `human_readable`, `one_pager`) per DOCS.md
- [ ] 1 cover letter HTML/CSS template per DOCS.md
- [ ] ATS plain text renderer (no markdown, no symbols)
- [ ] Inter font in `templates/fonts/`; renders via `Playwright page.pdf()`
- [ ] `render_prep_markdown(job_id)` and `render_anki_csv(job_id)` also in this module

## 3.6 Resume agent (REQUIREMENTS §8)
- [ ] JD diff → targeted-edit (match_score ≥ 0.55) or full-regen (< 0.55)
- [ ] System prompt enforces banned verbs/phrases, length variance, no em-dash, no first person
- [ ] After rewrite: `AiDetector.score()` gate (<0.4); reject → stricter retry (max 3); log each attempt
- [ ] `AtsScorer.score()` before + after; both stored in HITL diff payload
- [ ] Skills gap report emitted alongside resume output
- [ ] Versioned save via `doc_generator.render_resume()` → `ResumeVersionRepository.save()`
- [ ] HITL: unified diff + ATS before/after + AI score; user can edit bullets; explicit approve required

## 3.7 Cover letter agent
- [ ] 180–240 words; banned-phrase enforcement; tone matched to `CompanyProfile.culture_keywords`
- [ ] `AiDetector.score()` gate (<0.4)
- [ ] `CompanyProfile` fetched via `CompanyRepository.get_or_research()` — same cache used by all agents
- [ ] HITL: preview before save

## 3.8 Prep agent (PREP.md)
- [ ] `agents/prep.py` — triggered on `status=applied`; generates questions per PREP.md categories
- [ ] Embed via `Embedder` → Chroma cosine (>0.88 = merge, append source_jds; else insert)
- [ ] Model answer uses resume facts only (STAR / technical / system_design format per PREP.md)
- [ ] System design questions only for mid/senior roles
- [ ] Export: `doc_generator.render_prep_markdown()` and `render_anki_csv()`
- [ ] Prep focus session state is **ephemeral** (React state only, no DB) — intentional, sessions are short

## 3.9 Regression gates
- [ ] CI runs eval against `eval/data/` fixtures; fails on >5% drop vs baseline
- [ ] Golden snapshots per agent against sample JDs

## Tests
- ATS scorer: known high-match resume scores >85; known low-match scores <40
- AI detector: obvious AI text scores >0.5; API outage falls back to pattern check (no error thrown)
- Doc generator: PDF renders warning-free per template; one-pager == 1 page on max fixture; ATS txt ≥90% keyword coverage; missing optional fields don't crash
- Eval: scoring deterministic, leaderboard stable
- Company research: cache hit on second call within 7 days; re-researches after 7 days
- Resume: mode selection correct; banned verbs never appear; AI detector retry path covered; ATS score written to DB
- Cover letter: word count 180–240; banned phrase rejected; CompanyProfile fetched from cache
- Prep: near-dupe merges; distinct inserts; model answer never invents facts outside resume; system design absent for intern/junior
- HITL: resume from checkpoint after edit replays identically

Done: eval baseline locked; all agents pass thresholds. Update `STATE.md`.
