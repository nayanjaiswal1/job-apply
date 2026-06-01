'use client'
import { useApplications, useJobs } from '@/lib/queries'
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

export default function AnalyticsPage() {
  const { data: applications = [] } = useApplications()
  const { data: jobs = [] } = useJobs()

  const statusCounts = (applications as any[]).reduce((acc: Record<string, number>, a: any) => {
    acc[a.status] = (acc[a.status] ?? 0) + 1
    return acc
  }, {})

  const chartData = Object.entries(statusCounts).map(([status, count]) => ({ status, count }))

  return (
    <div>
      <h1 className="text-heading-1 mb-6">Analytics</h1>
      <div className="grid grid-cols-3 gap-4 mb-8">
        <StatCard label="Total jobs found" value={(jobs as any[]).length} />
        <StatCard label="Applications sent" value={(applications as any[]).filter((a: any) => a.status !== 'discovered').length} />
        <StatCard label="Interviews" value={(applications as any[]).filter((a: any) => a.status === 'interview_scheduled').length} />
      </div>
      <div className="rounded-lg border border-border bg-raised p-4">
        <div className="text-heading-3 mb-4">Application Status Distribution</div>
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={chartData}>
            <XAxis dataKey="status" tick={{ fontSize: 11 }} />
            <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
            <Tooltip />
            <Bar dataKey="count" fill="var(--color-brand)" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-border bg-raised p-4">
      <div className="text-caption text-muted">{label}</div>
      <div className="text-display mt-1">{value}</div>
    </div>
  )
}
