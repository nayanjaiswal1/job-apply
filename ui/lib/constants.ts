export const JOB_STATUSES = [
  'discovered', 'applied', 'outreach_sent', 'interview_scheduled',
  'offer_received', 'rejected', 'ghosted', 'withdrawn', 'archived', 'form_failed',
] as const
export type JobStatus = typeof JOB_STATUSES[number]

export const CONFIDENCE = ['unseen', 'shaky', 'comfortable', 'confident'] as const
export type Confidence = typeof CONFIDENCE[number]

export const QUESTION_CATS = [
  'technical', 'system_design', 'behavioural', 'role_specific', 'company_specific',
] as const

export const REMOTE_PREFS = ['remote', 'hybrid', 'onsite', 'any'] as const

export const RESUME_FORMATS = ['ats_plain', 'human_readable', 'one_pager'] as const
