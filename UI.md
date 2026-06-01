# UI

Next.js dashboard: tracker, HITL approvals, prep bank, analytics, model picker.

## Stack — use these, don't substitute

- Next.js 15 App Router, React 19, TypeScript strict
- shadcn/ui — design system, copy-paste components, no runtime dep
- Tailwind CSS
- TanStack Query — server state + caching
- TanStack Table — tracker board + tables
- TanStack Form + Zod — forms + validation
- Recharts — analytics charts
- react-diff-viewer-continued — resume diff
- EventSource (native) — SSE from FastAPI, no socket lib
- next-themes — dark mode
- openapi-typescript — generate TS types from FastAPI OpenAPI

## Don't add
- Redux / Zustand / Jotai — TanStack Query + `useState` is enough
- Custom design system — shadcn is the design system
- Storybook — out of scope for personal tool
- i18n — single-user, English

## Routes

| Path | Purpose |
|---|---|
| `/onboarding` | 4-step first-run wizard (basics → work context → upload resume → preferences) |
| `/profile` | Edit contact + work context |
| `/profile/resume` | Upload new resume → diff → inline edit → approve |
| `/` | Tracker kanban — drag between columns = state machine action via API |
| `/approvals` | HITL queue, badge = pending interrupts |
| `/approvals/resume/[id]` | Diff viewer + per-bullet edit + approve |
| `/approvals/cover/[id]` | Preview + edit + approve |
| `/approvals/outreach/[id]` | Batch preview + per-row approve |
| `/approvals/referrals/[id]` | Connection picker |
| `/jobs` | Sortable filterable table |
| `/prep` | Full question bank — filter category/difficulty/confidence/company |
| `/prep/[job_id]` | Questions for one application (pre-interview view) |
| `/prep/session` | Focus session — card flip + confidence rating |
| `/prep/[question_id]` | Edit personal answer, view which companies asked it |
| `/analytics` | ATS-vs-outcome, cost/day, ghost rate (Recharts) |
| `/settings/models` | Model picker → `config.yaml` |
| `/settings/preferences` | Preferences form |

## Data flow

- Server state: TanStack Query against FastAPI (`/api/v1/*`)
- Mutations: optimistic update + invalidate on success
- Real-time: SSE at `/api/v1/events` → invalidates affected queries
- Auth: API key in httpOnly cookie

## shadcn components — install only what you use

`Card, Badge, Button, Dialog, Toast, Tabs, Table, Form, Input, Select, Checkbox, DropdownMenu, Sheet, Skeleton`. Don't install the rest until needed.

## Folder

```
ui/
├── app/
│   ├── (dashboard)/        # route group, shared layout
│   ├── api/                # proxy to FastAPI when needed
│   └── layout.tsx
├── components/
│   ├── ui/                 # shadcn (copy-pasted)
│   ├── tracker/            # board, column, card
│   ├── approvals/          # diff viewer wrapper, approve form
│   ├── prep/               # markdown render
│   └── shared/             # nav, theme toggle
├── lib/
│   ├── api.ts              # fetch wrapper
│   ├── queries.ts          # TanStack Query keys + hooks
│   └── types.ts            # generated from FastAPI OpenAPI
└── package.json
```

## API codegen

- FastAPI publishes `/openapi.json`
- `npm run gen:api` runs `openapi-typescript` → `lib/types.ts`
- Wired into CI: backend PR must regen client

## Tests

- `vitest` for components
- `playwright` for e2e: tracker drag, approve resume, approve cover letter
- Mock SSE with EventSource polyfill in test env

## Design system
See **`DESIGN.md`** for the full token system, Tailwind config, cva variants, and shared utility rules. Summary:
- Colors/typography/shadows → `tokens.css` CSS vars only. No hardcoded hex in JSX.
- Text styles → `.text-heading-2`, `.text-body` etc. No raw `text-xl font-semibold` scattered.
- Component variants → `cva` block. One place per component, not parallel class strings.
- API calls → `lib/api.ts` only. No raw `fetch()`.
- Query hooks → `lib/queries.ts` only. No standalone `useQuery` calls.
- Status/category strings → `lib/constants.ts`. No magic string literals.
- Dates/slugs → `lib/utils.ts`. No inline `new Date()` formatting.

## Reuse before write
shadcn covers nearly all primitives (`npx shadcn@latest add <component>`). Check `INDEX.md` for existing hooks and utilities before writing new ones.
