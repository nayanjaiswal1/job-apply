import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from './api'

export const queryKeys = {
  jobs:         (f?: Record<string, string>) => ['jobs', f] as const,
  job:          (id: string)                 => ['jobs', id] as const,
  applications: ()                           => ['applications'] as const,
  prep:         (jobId?: string)             => ['prep', jobId] as const,
  prepQ:        (id: string)                 => ['prep', 'q', id] as const,
  profile:      ()                           => ['profile'] as const,
  prefs:        ()                           => ['preferences'] as const,
  onboarding:   ()                           => ['onboarding'] as const,
  dlq:          ()                           => ['dlq'] as const,
}

export const useJobs        = (f?: Record<string, string>) => useQuery({ queryKey: queryKeys.jobs(f), queryFn: () => api.jobs.list(f) })
export const useJob         = (id: string)                 => useQuery({ queryKey: queryKeys.job(id),  queryFn: () => api.jobs.get(id) })
export const useApplications= ()                           => useQuery({ queryKey: queryKeys.applications(), queryFn: api.applications.list })
export const usePrepQuestions=(jobId?: string)             => useQuery({ queryKey: queryKeys.prep(jobId), queryFn: () => api.prep.list(jobId ? { job_id: jobId } : undefined) })
export const useProfile     = ()                           => useQuery({ queryKey: queryKeys.profile(), queryFn: api.profile.get })
export const useOnboarding  = ()                           => useQuery({ queryKey: queryKeys.onboarding(), queryFn: api.onboarding.status })

export const usePatchStatus = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => api.applications.patchStatus(id, status),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.applications() }),
  })
}

export const useUpdateQuestion = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: unknown }) => api.prep.update(id, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.prep() }),
  })
}
