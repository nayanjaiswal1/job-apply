'use client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'
import Nav from '@/components/shared/Nav'
import { useSSE } from '@/lib/sse'

function SSEBridge() {
  useSSE()
  return null
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [qc] = useState(() => new QueryClient({ defaultOptions: { queries: { staleTime: 30_000 } } }))
  return (
    <QueryClientProvider client={qc}>
      <SSEBridge />
      <div className="flex min-h-screen flex-col">
        <Nav />
        <main className="flex-1 p-6">{children}</main>
      </div>
    </QueryClientProvider>
  )
}
