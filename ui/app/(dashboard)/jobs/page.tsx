'use client'
import { useState } from 'react'
import { useJobs } from '@/lib/queries'
import { JOB_STATUSES } from '@/lib/constants'
import { formatRelative } from '@/lib/utils'

export default function JobsPage() {
  const [status, setStatus] = useState('')
  const { data: jobs = [], isLoading } = useJobs(status ? { status } : undefined)

  return (
    <div>
      <h1 className="text-heading-1 mb-4">Jobs</h1>
      <div className="flex gap-3 mb-6">
        <select
          className="text-body-sm border border-border rounded-md px-3 py-1.5 bg-surface"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          <option value="">All statuses</option>
          {JOB_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {isLoading ? <div className="text-muted text-body-sm">Loading...</div> : (
        <div className="rounded-lg border border-border overflow-hidden">
          <table className="w-full text-body-sm">
            <thead className="bg-raised border-b border-border">
              <tr>
                {['Title', 'Company', 'Location', 'Score', 'Status', 'Posted'].map((h) => (
                  <th key={h} className="text-left text-label text-muted px-4 py-2">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(jobs as any[]).map((job) => (
                <tr key={job.id} className="border-b border-border hover:bg-raised transition-colors">
                  <td className="px-4 py-3 font-medium">{job.title}</td>
                  <td className="px-4 py-3 text-muted">{job.company}</td>
                  <td className="px-4 py-3 text-muted">{job.location}</td>
                  <td className="px-4 py-3">{job.match_score ? `${Math.round(job.match_score * 100)}%` : '—'}</td>
                  <td className="px-4 py-3">
                    <span className="text-label bg-raised border border-border rounded-full px-2 py-0.5">{job.status}</span>
                  </td>
                  <td className="px-4 py-3 text-muted">{job.posted_at ? formatRelative(job.posted_at) : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
