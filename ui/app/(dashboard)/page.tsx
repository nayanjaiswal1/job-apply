'use client'
import { useApplications, usePatchStatus } from '@/lib/queries'
import { JOB_STATUSES, type JobStatus } from '@/lib/constants'
import { cn } from '@/lib/utils'

const COLUMNS: JobStatus[] = ['applied', 'outreach_sent', 'interview_scheduled', 'offer_received', 'rejected']

export default function TrackerPage() {
  const { data: applications = [], isLoading } = useApplications()
  const patchStatus = usePatchStatus()

  if (isLoading) return <div className="text-body-sm text-muted">Loading...</div>

  return (
    <div>
      <h1 className="text-heading-1 mb-6">Applications</h1>
      <div className="grid grid-cols-5 gap-4 overflow-x-auto">
        {COLUMNS.map((col) => (
          <div key={col} className="min-w-[180px]">
            <div className="text-label text-muted mb-3 uppercase">{col.replace(/_/g, ' ')}</div>
            <div className="flex flex-col gap-2">
              {(applications as any[])
                .filter((a) => a.status === col)
                .map((app) => (
                  <div
                    key={app.id}
                    className="rounded-lg border border-border bg-raised p-3 cursor-pointer hover:shadow transition-shadow"
                    draggable
                  >
                    <div className="text-body-sm font-medium truncate">{app.job_id}</div>
                    <div className="text-caption mt-1">{app.sent_at ? new Date(app.sent_at).toLocaleDateString() : '—'}</div>
                  </div>
                ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
