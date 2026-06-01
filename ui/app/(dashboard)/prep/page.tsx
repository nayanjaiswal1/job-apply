'use client'
import { useState } from 'react'
import { usePrepQuestions, useUpdateQuestion } from '@/lib/queries'
import { QUESTION_CATS, CONFIDENCE, type Confidence } from '@/lib/constants'
import { cn } from '@/lib/utils'

const CONFIDENCE_COLORS: Record<Confidence, string> = {
  unseen:      'bg-raised text-body border border-border',
  shaky:       'bg-red-50 text-red-800 dark:bg-red-950 dark:text-red-300',
  comfortable: 'bg-blue-50 text-blue-800 dark:bg-blue-950 dark:text-blue-300',
  confident:   'bg-green-50 text-green-800 dark:bg-green-950 dark:text-green-300',
}

export default function PrepPage() {
  const [cat, setCat] = useState<string>('')
  const [conf, setConf] = useState<string>('')
  const { data: questions = [], isLoading } = usePrepQuestions()
  const update = useUpdateQuestion()

  const filtered = (questions as any[]).filter((q) =>
    (!cat || q.category === cat) && (!conf || q.confidence === conf)
  )

  return (
    <div>
      <h1 className="text-heading-1 mb-4">Question Bank</h1>
      <div className="flex gap-3 mb-6 flex-wrap">
        <select className="text-body-sm border border-border rounded-md px-3 py-1.5 bg-surface" value={cat} onChange={(e) => setCat(e.target.value)}>
          <option value="">All categories</option>
          {QUESTION_CATS.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
        <select className="text-body-sm border border-border rounded-md px-3 py-1.5 bg-surface" value={conf} onChange={(e) => setConf(e.target.value)}>
          <option value="">All confidence</option>
          {CONFIDENCE.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      {isLoading ? <div className="text-muted text-body-sm">Loading...</div> : (
        <div className="flex flex-col gap-3">
          {filtered.map((q: any) => (
            <div key={q.id} className="rounded-lg border border-border bg-raised p-4">
              <div className="flex items-start justify-between gap-4">
                <p className="text-body font-medium">{q.text}</p>
                <span className={cn('text-label rounded-full px-2 py-0.5 shrink-0', CONFIDENCE_COLORS[q.confidence as Confidence])}>
                  {q.confidence}
                </span>
              </div>
              {q.model_answer && (
                <details className="mt-3">
                  <summary className="text-body-sm text-muted cursor-pointer">Answer</summary>
                  <pre className="mt-2 text-body-sm whitespace-pre-wrap">{q.model_answer}</pre>
                </details>
              )}
              <div className="flex gap-2 mt-3">
                {CONFIDENCE.filter((c) => c !== q.confidence).map((c) => (
                  <button
                    key={c}
                    className="text-caption text-muted hover:text-body border border-border rounded px-2 py-0.5"
                    onClick={() => update.mutate({ id: q.id, body: { confidence: c } })}
                  >
                    Mark {c}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
