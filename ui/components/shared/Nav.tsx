'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'

const links = [
  { href: '/',             label: 'Tracker' },
  { href: '/jobs',         label: 'Jobs' },
  { href: '/approvals',    label: 'Approvals' },
  { href: '/prep',         label: 'Prep' },
  { href: '/analytics',    label: 'Analytics' },
  { href: '/settings/models', label: 'Settings' },
]

export default function Nav() {
  const path = usePathname()
  return (
    <header className="border-b border-border bg-surface px-6 py-3 flex items-center gap-6">
      <span className="text-heading-3 text-brand font-semibold">Job Agent</span>
      <nav className="flex gap-4">
        {links.map(({ href, label }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              'text-body-sm transition-colors',
              path === href ? 'text-brand font-medium' : 'text-muted hover:text-body'
            )}
          >
            {label}
          </Link>
        ))}
      </nav>
    </header>
  )
}
