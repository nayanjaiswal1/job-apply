# Design System

Single source of truth: **`ui/styles/tokens.css`**. Change one variable, every component updates.

## How it connects

```
tokens.css (CSS vars)
  └─► tailwind.config.ts (maps Tailwind classes to CSS vars)
        └─► shadcn/ui components (already read CSS vars)
              └─► every component in the app
```

Change `--color-brand` in `tokens.css` → every button, badge, link, and accent updates. No other file changes.

## File structure

```
ui/styles/
├── tokens.css       # ALL design tokens — only file to edit for full retheme
├── globals.css      # imports tokens.css + shadcn overrides + body reset
└── typography.css   # reusable text classes (.text-heading, .text-body, etc.)
```

---

## tokens.css

```css
:root {
  /* ── Colors (semantic names, never hardcode hex in components) ── */
  --color-brand:         #1a1a2e;  /* primary: CTAs, section accents */
  --color-brand-muted:   #4a4a6a;  /* subtitles on brand surfaces */
  --color-body:          #2c2c2c;  /* body text */
  --color-muted:         #666666;  /* dates, secondary labels */
  --color-border:        #e2e2e8;
  --color-surface:       #ffffff;
  --color-raised:        #f7f7fb;  /* card / elevated backgrounds */
  --color-danger:        #d92b2b;
  --color-success:       #1e7d4a;
  --color-warning:       #b45309;

  /* ── shadcn expects these names (keep them, shadcn reads them) ── */
  --background:            220 27% 98%;   /* HSL — shadcn format */
  --foreground:            224 10% 17%;
  --primary:               232 27% 14%;
  --primary-foreground:    0 0% 100%;
  --secondary:             220 14% 96%;
  --secondary-foreground:  224 10% 17%;
  --muted:                 220 14% 96%;
  --muted-foreground:      220 9% 46%;
  --border:                220 13% 91%;
  --input:                 220 13% 91%;
  --ring:                  232 27% 14%;
  --destructive:           0 72% 51%;
  --destructive-foreground: 0 0% 100%;
  --radius: 0.5rem;

  /* ── Typography ── */
  --font-sans: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;

  /* ── Shadows ── */
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow:    0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);

  /* ── Motion ── */
  --ease:     cubic-bezier(0.4, 0, 0.2, 1);
  --duration: 150ms;
}

/* Dark mode — edit these to retheme dark ── */
.dark {
  --color-brand:        #7b8cde;
  --color-body:         #e8e8f0;
  --color-muted:        #9999aa;
  --color-border:       #2c2c40;
  --color-surface:      #0f0f1a;
  --color-raised:       #1a1a2e;

  --background:         232 27% 7%;
  --foreground:         220 14% 92%;
  --primary:            232 60% 67%;
  --primary-foreground: 232 27% 7%;
  --secondary:          232 20% 14%;
  --secondary-foreground: 220 14% 92%;
  --muted:              232 20% 14%;
  --muted-foreground:   220 9% 60%;
  --border:             232 20% 20%;
}
```

---

## tailwind.config.ts

Maps Tailwind classes to our CSS vars. Tailwind classes = typed aliases for tokens.

```typescript
import type { Config } from 'tailwindcss'

export default {
  darkMode: ['class'],
  theme: {
    extend: {
      colors: {
        // Custom semantic tokens
        brand:   'var(--color-brand)',
        'brand-muted': 'var(--color-brand-muted)',
        body:    'var(--color-body)',
        muted:   'var(--color-muted)',
        raised:  'var(--color-raised)',
        danger:  'var(--color-danger)',
        success: 'var(--color-success)',
        warning: 'var(--color-warning)',
        // shadcn tokens (keep these exact names)
        border:     'hsl(var(--border))',
        input:      'hsl(var(--input))',
        ring:       'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT:    'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT:    'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        muted: {
          DEFAULT:    'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        destructive: {
          DEFAULT:    'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
      },
      fontFamily: {
        sans: ['var(--font-sans)'],
        mono: ['var(--font-mono)'],
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      boxShadow: {
        sm: 'var(--shadow-sm)',
        DEFAULT: 'var(--shadow)',
        lg: 'var(--shadow-lg)',
      },
    },
  },
} satisfies Config
```

---

## typography.css

Define text styles once. Use class names in components, never raw font-size/weight values.

```css
.text-display   { @apply text-3xl font-bold leading-tight tracking-tight; }
.text-heading-1 { @apply text-2xl font-semibold leading-tight; }
.text-heading-2 { @apply text-xl  font-semibold leading-tight; }
.text-heading-3 { @apply text-lg  font-medium  leading-snug; }
.text-body      { @apply text-base font-normal leading-relaxed; }
.text-body-sm   { @apply text-sm   font-normal leading-relaxed; }
.text-caption   { @apply text-xs   font-normal text-muted-foreground; }
.text-label     { @apply text-xs   font-semibold uppercase tracking-widest; }
.text-code      { @apply text-sm   font-mono; }
```

---

## Component variants (cva)

Never repeat class strings across components. Use `cva` for variants — shadcn already does this for all its components.

```typescript
// Example: custom StatusBadge component
import { cva, type VariantProps } from 'class-variance-authority'

const statusBadge = cva(
  'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-label transition-colors',
  {
    variants: {
      status: {
        discovered:  'bg-raised text-body border border-border',
        applied:     'bg-blue-50   text-blue-800  dark:bg-blue-950  dark:text-blue-300',
        interview:   'bg-green-50  text-green-800 dark:bg-green-950 dark:text-green-300',
        rejected:    'bg-red-50    text-red-800   dark:bg-red-950   dark:text-red-300',
        ghosted:     'bg-amber-50  text-amber-800 dark:bg-amber-950 dark:text-amber-300',
        offer:       'bg-purple-50 text-purple-800 dark:bg-purple-950 dark:text-purple-300',
      },
    },
  }
)
```

New status? Add one line to `cva`. Nothing else changes.

---

## Rules — enforced in code review

| Rule | Good | Bad |
|---|---|---|
| Colors | `text-brand`, `bg-raised`, `text-muted-foreground` | `text-[#1a1a2e]`, `style={{ color: '#666' }}` |
| Typography | `className="text-heading-2"` | `className="text-xl font-semibold"` scattered |
| Variants | Add to existing `cva` block | Create parallel classes for a new variant |
| Spacing | Tailwind scale (`p-4`, `gap-6`) | Arbitrary `p-[13px]` |
| Retheme | Edit `tokens.css` | Find-replace hex codes across files |
| Dark mode | `.dark` in `tokens.css` | `dark:text-[#9999aa]` scattered in JSX |

Banned: arbitrary Tailwind values, inline styles, `@apply` outside `typography.css`, Emotion/CSS-in-JS.

---

## How to retheme entirely

1. Open `tokens.css`
2. Change colors under `/* Colors */` and `.dark`
3. Change `--font-sans` if switching fonts
4. Done — every component, every page, every PDF template updates

PDF templates (DOCS.md) use the same hex values as `--color-brand` etc. Update both `tokens.css` and the corresponding CSS vars in `templates/resume/base.css` together. They should always match.

---

## Shared utilities — no duplication

These live in `ui/lib/`. Check INDEX.md before writing anything new.

### `ui/lib/utils.ts`
```typescript
// shadcn's cn() — merge Tailwind classes without conflicts
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
export function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)) }

// Date formatting — one function, used everywhere
export const formatDate  = (d: string) => ...      // "Jan 2025"
export const formatRelative = (d: string) => ...   // "3 days ago"

// Slug
export const slugify = (s: string) => ...
```

### `ui/lib/constants.ts`
```typescript
// No magic strings anywhere in the app — import from here
export const JOB_STATUSES   = ['discovered','applied','interview_scheduled','offer','rejected','ghosted','withdrawn'] as const
export const CONFIDENCE      = ['unseen','shaky','comfortable','confident'] as const
export const QUESTION_CATS   = ['technical','system_design','behavioural','role_specific','company_specific'] as const
export const REMOTE_PREFS    = ['remote','hybrid','onsite','any'] as const
export const RESUME_FORMATS  = ['ats_plain','human_readable','one_pager'] as const
```

### `ui/lib/queries.ts`
All TanStack Query keys and hooks in one file. No `useQuery` calls scattered across pages.

```typescript
export const queryKeys = {
  jobs:        (filters?) => ['jobs', filters],
  job:         (id: string) => ['jobs', id],
  applications:()           => ['applications'],
  prep:        (jobId?)     => ['prep', jobId],
  profile:     ()           => ['profile'],
  ...
}

// Every query hook exported from here
export const useJobs        = (filters) => useQuery({ queryKey: queryKeys.jobs(filters), ... })
export const useJob         = (id)      => useQuery({ queryKey: queryKeys.job(id), ... })
export const usePrepQuestions = (jobId) => useQuery(...)
export const useProfile     = ()        => useQuery(...)
```

### `ui/lib/api.ts`
Single fetch wrapper. All API calls go through this — no raw `fetch()` in components.

```typescript
// Typed against generated OpenAPI types (lib/types.ts)
export const api = {
  jobs:         { list: (f) => get('/api/v1/jobs', f),    get: (id) => get(`/api/v1/jobs/${id}`) },
  applications: { list: () => get('/api/v1/applications'), ... },
  prep:         { list: (jobId?) => get('/api/v1/prep/questions', { jobId }), ... },
  profile:      { get: () => get('/api/v1/profile'), update: (d) => put('/api/v1/profile', d) },
  ...
}
```

### Rules for shared code
- New API call? Add to `api.ts` + `queries.ts`. Never inline `fetch()`.
- New status/category string? Add to `constants.ts`. Never hardcode a string literal.
- New date format? Add to `utils.ts`. Never call `new Date()` formatting inline.
- New shared component? Check if shadcn already has it first (`npx shadcn@latest add`).
- After adding: one line in `INDEX.md`.
