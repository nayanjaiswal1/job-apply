# Document Generation

**Renderer: Playwright `page.pdf()`** — not WeasyPrint. We already have Playwright; it runs full Chromium so every CSS feature works. Remove `weasyprint` from deps.

```python
# tools/doc_generator.py
async def _html_to_pdf(html: str, margins: dict) -> bytes:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page    = await browser.new_page()
        await page.set_content(html, wait_until="networkidle")
        pdf = await page.pdf(format="A4", print_background=True, margin=margins)
        await browser.close()
        return pdf
```

All templates are Jinja2 HTML → rendered by Playwright → saved as PDF.

---

## Template folder

```
job_agent/templates/
├── resume/
│   ├── base.css              # shared reset + typography
│   ├── ats_plain.html + .css
│   ├── human_readable.html + .css
│   └── one_pager.css         # overrides on top of human_readable
└── cover_letter/
    └── cover_letter.html + .css
```

---

## 1. ATS Plain

**Goal:** passes every ATS parser. Zero decoration. Looks like Jake's Resume (LaTeX style) in HTML.

### Visual spec
```
┌─────────────────────────────────────────────┐
│  FULL NAME                                  │
│  email · phone · linkedin · github          │
├─────────────────────────────────────────────│  ← 1px solid #000 rule
│  EXPERIENCE                                 │  ← uppercase, bold, 11pt
├─────────────────────────────────────────────│
│  Job Title                     Jan 22–Now   │
│  Company Name, City                         │
│    • bullet one                             │
│    • bullet two                             │
│                                             │
│  EDUCATION                                  │
├─────────────────────────────────────────────│
│  Degree · School               Year         │
│  SKILLS                                     │
├─────────────────────────────────────────────│
│  Python, SQL, Docker, ...                   │
└─────────────────────────────────────────────┘
```

### CSS rules (ats_plain.css)
- Font: `font-family: "Times New Roman", Times, serif` body; `Arial, Helvetica, sans-serif` headings
- Page: A4, margins 0.75in all sides
- Name: 18pt, bold, centered
- Contact line: 10pt, centered, `·` separator
- Section header: 11pt, bold, uppercase, `border-bottom: 1.5px solid #000`, `margin-top: 12pt`
- Job header: flex row, title left bold, date right normal — no tables
- Company line: 10pt normal, immediately below title
- Bullets: `padding-left: 1.2em`, `list-style-type: disc`, 10.5pt, line-height 1.3
- Skills: plain comma-separated text, 10.5pt
- **Banned CSS**: `border-radius`, `background-color`, `box-shadow`, `color` (all black), any image, icon font

---

## 2. Human Readable

**Goal:** clean and modern. Sent directly to humans — startup founders, referrals, direct recruiters.

### Visual spec
```
┌─────────────────────────────────────────────┐
│  FULL NAME                  email           │
│  Current Title              phone           │
│                             linkedin        │
├─────────────────────────────────────────────│  ← 2px #1a1a2e
│ ▌ EXPERIENCE                                │  ← accent bar left
│                                             │
│  Job Title                      Jan 22–Now  │
│  Company · City                             │
│  • bullet one                               │
│  • bullet two                               │
│                                             │
│ ▌ EDUCATION                                 │
│  Degree · School · Year                     │
│                                             │
│ ▌ SKILLS                                    │
│  Python · SQL · Docker · React              │
└─────────────────────────────────────────────┘
```

### CSS rules (human_readable.css)
- Font: Inter (embedded local), fallback `system-ui, sans-serif` — download Inter Regular/Medium/SemiBold, store in `templates/fonts/`
- Page: A4, margins 0.6in sides, 0.7in top/bottom
- Name: 22pt, font-weight 600, color `#1a1a2e`
- Sub-header (title, contact): 10pt, color `#4a4a6a`, line-height 1.6
- Two-column header: name/title left (65%), contact right (35%), flexbox
- Section header: 10.5pt, font-weight 600, uppercase, letter-spacing 0.08em, `border-left: 3px solid #1a1a2e`, padding-left 8px, color `#1a1a2e`
- Job title: 11pt, font-weight 500, color `#1a1a2e`
- Company + location: 10pt, color `#666`
- Date: 10pt, color `#666`, float right
- Bullets: 10pt, line-height 1.45, color `#2c2c2c`, `padding-left: 1.1em`
- Skills: 10pt, `·` separator, color `#2c2c2c`
- Subtle section spacing: `margin-top: 14pt` between sections

### Color palette
```
Primary text:   #1a1a2e   (near-black navy)
Secondary:      #4a4a6a   (muted purple-gray)
Body text:      #2c2c2c   (soft black)
Light text:     #666666   (dates, company)
Accent:         #1a1a2e   (section bars — same as primary)
Background:     #ffffff
```

---

## 3. One Pager

Applied as a CSS override on top of `human_readable.html`.

```css
/* one_pager.css — import after human_readable.css */
@page { margin: 0.45in 0.5in; }
body  { font-size: 9.5pt; }

h1.name       { font-size: 18pt; }
.section-head { font-size: 9.5pt; margin-top: 8pt; }
.job-title    { font-size: 10pt; }
li            { line-height: 1.3; margin-bottom: 1pt; }
.section      { margin-top: 8pt; }
```

If content still overflows 1 page:
1. Truncate least-relevant experience role (log which one dropped)
2. If still over: log warning `"one_pager overflow: {name} {role}"` — do not silently shrink text below 9pt

---

## 4. Cover Letter

### Visual spec
```
┌─────────────────────────────────────────────┐
│  FULL NAME                                  │
│  email · phone · linkedin                   │
│                                             │
│  June 1, 2026                               │
│                                             │
│  Dear [Hiring Manager / Name],              │
│                                             │
│  [paragraph 1 — hook]                       │
│                                             │
│  [paragraph 2 — experience points]          │
│                                             │
│  [paragraph 3 — ask]                        │
│                                             │
│  Regards,                                   │
│  Full Name                                  │
└─────────────────────────────────────────────┘
```

- Same Inter font + color palette as human_readable
- No section bars — letter style
- Body: 11pt, line-height 1.6, `#2c2c2c`
- Paragraph spacing: `margin-bottom: 14pt`
- Max width: 5.5in (readable line length, centered on A4)

---

## Jinja2 context (same for all templates)

```python
{
  "name":           str,
  "email":          str,
  "phone":          str,
  "linkedin":       str | None,
  "github":         str | None,
  "portfolio":      str | None,
  "current_title":  str | None,
  "summary":        str | None,
  "skills":         list[str],
  "experience": [
    { "title": str, "company": str, "location": str | None,
      "start": str, "end": str, "bullets": list[str] }
  ],
  "education": [
    { "degree": str, "school": str, "year": str, "gpa": str | None }
  ],
  "certifications": list[str],
  # cover letter only:
  "letter_body":    str | None,   # rendered paragraphs
  "date":           str,          # "June 1, 2026"
  "salutation":     str,          # "Dear Sarah," or "Dear Hiring Manager,"
}
```

---

## Generator API

```python
# tools/doc_generator.py

async def render_resume(
    data: ResumeData,
    fmt: Literal["ats_plain", "human_readable", "one_pager"],
) -> tuple[bytes, str]:
    """Returns (pdf_bytes, plain_txt)."""

async def render_cover_letter(
    body: str,
    profile: UserProfile,
    salutation: str = "Dear Hiring Manager,",
) -> bytes:
    """Returns pdf_bytes."""

async def render_prep_markdown(job_id: str) -> str:
    """Returns markdown of all prep questions for a job."""

async def render_anki_csv(job_id: str) -> str:
    """Returns Anki-format CSV (Question, Answer, Tags, Difficulty)."""
```

---

## ATS plain text (.txt) — alongside every PDF

No markdown. No symbols except `-` bullets.

```
FULL NAME
email | phone | linkedin.com/in/...

SUMMARY
<two sentences>

EXPERIENCE

Job Title — Company (Jan 2022 – Mar 2024)
- bullet one
- bullet two

EDUCATION

Degree, School (Year)

SKILLS
Python, SQL, Docker, ...
```

Saved alongside every PDF: `resume_v2_google_swe.pdf` + `resume_v2_google_swe.txt`

---

## File save paths

```
data/resumes/resume_v{n}_{company_slug}_{role_slug}.pdf
data/resumes/resume_v{n}_{company_slug}_{role_slug}.txt
data/cover_letters/cover_v{n}_{company_slug}_{role_slug}.pdf
```

---

## Tests

- `ats_plain` renders without CSS warnings; no color values; no decorative elements
- `human_readable` PDF is visually verified against a fixture screenshot (Playwright screenshot diff)
- `one_pager` page count == 1 on a max-length fixture resume
- Cover letter word count 180–240 in extracted text
- Missing optional fields (no GitHub, no summary) don't crash any template
- ATS txt: ≥90% of expected keywords present after stripping
