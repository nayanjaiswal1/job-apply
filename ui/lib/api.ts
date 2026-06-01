const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

async function get<T>(path: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(`${BASE}${path}`)
  if (params) Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v))
  const res = await fetch(url.toString(), { credentials: 'include' })
  if (!res.ok) throw new Error(`GET ${path} → ${res.status}`)
  return res.json()
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST', credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) throw new Error(`POST ${path} → ${res.status}`)
  return res.json()
}

async function put<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'PUT', credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`PUT ${path} → ${res.status}`)
  return res.json()
}

async function patch<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'PATCH', credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`PATCH ${path} → ${res.status}`)
  return res.json()
}

export const api = {
  jobs: {
    list:   (params?: Record<string, string>) => get('/api/v1/jobs', params),
    get:    (id: string) => get(`/api/v1/jobs/${id}`),
  },
  applications: {
    list:        () => get('/api/v1/applications'),
    patchStatus: (id: string, status: string) => patch(`/api/v1/applications/${id}/status`, { status }),
  },
  prep: {
    list:      (params?: Record<string, string>) => get('/api/v1/prep/questions', params),
    get:       (id: string) => get(`/api/v1/prep/questions/${id}`),
    update:    (id: string, body: unknown) => put(`/api/v1/prep/questions/${id}`, body),
    forJob:    (jobId: string) => get(`/api/v1/prep/jobs/${jobId}`),
  },
  profile: {
    get:    () => get('/api/v1/profile'),
    update: (d: unknown) => put('/api/v1/profile', d),
    prefs:  { get: () => get('/api/v1/profile/preferences'), update: (d: unknown) => put('/api/v1/profile/preferences', d) },
  },
  onboarding: { status: () => get('/api/v1/onboarding/status') },
  approvals: {
    resume:  (id: string, body: unknown) => post(`/api/v1/approvals/resume/${id}`, body),
    followup:(id: string, body: unknown) => post(`/api/v1/approvals/followup/${id}`, body),
    dlq:     () => get('/api/v1/approvals/queue/dlq'),
  },
  health: () => get('/health'),
}
