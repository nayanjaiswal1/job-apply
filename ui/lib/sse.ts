import { useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { queryKeys } from './queries'

const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

export function useSSE() {
  const qc = useQueryClient()
  useEffect(() => {
    let es: EventSource
    function connect() {
      es = new EventSource(`${BASE}/api/v1/events`, { withCredentials: true })
      es.onmessage = (e) => {
        try {
          const { type } = JSON.parse(e.data)
          if (type === 'application_updated') qc.invalidateQueries({ queryKey: queryKeys.applications() })
          if (type === 'job_found')           qc.invalidateQueries({ queryKey: queryKeys.jobs() })
          if (type === 'prep_generated')      qc.invalidateQueries({ queryKey: queryKeys.prep() })
        } catch {}
      }
      es.onerror = () => { es.close(); setTimeout(connect, 3000) }
    }
    connect()
    return () => es?.close()
  }, [qc])
}
