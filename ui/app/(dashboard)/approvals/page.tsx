'use client'
import Link from 'next/link'

export default function ApprovalsPage() {
  return (
    <div>
      <h1 className="text-heading-1 mb-6">Approvals</h1>
      <div className="grid gap-4">
        <ApprovalSection title="Resume Diffs" href="/approvals/resume" />
        <ApprovalSection title="Cover Letters" href="/approvals/cover" />
        <ApprovalSection title="Outreach Batch" href="/approvals/outreach" />
        <ApprovalSection title="Referral Picks" href="/approvals/referrals" />
      </div>
    </div>
  )
}

function ApprovalSection({ title, href }: { title: string; href: string }) {
  return (
    <Link href={href} className="flex items-center justify-between rounded-lg border border-border bg-raised p-4 hover:shadow transition-shadow">
      <span className="text-body font-medium">{title}</span>
      <span className="text-caption text-muted">View</span>
    </Link>
  )
}
