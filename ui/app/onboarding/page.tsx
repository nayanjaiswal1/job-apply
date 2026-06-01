'use client'
import { useEffect, useState } from 'react'
import { api } from '@/lib/api'

const STEPS = ['Basics', 'Work Context', 'Resume', 'Preferences']

export default function OnboardingPage() {
  const [step, setStep] = useState(1)

  useEffect(() => {
    api.onboarding.status().then((s: any) => {
      if (s.step === 'complete') window.location.href = '/'
      else setStep(Number(s.step))
    })
  }, [])

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-full max-w-lg px-6">
        <h1 className="text-heading-1 mb-2 text-brand">Welcome to Job Agent</h1>
        <p className="text-body-sm text-muted mb-8">Step {step} of {STEPS.length} — {STEPS[step - 1]}</p>
        <div className="flex gap-2 mb-8">
          {STEPS.map((_, i) => (
            <div
              key={i}
              className={`h-1.5 flex-1 rounded-full transition-colors ${i < step ? 'bg-brand' : 'bg-border'}`}
            />
          ))}
        </div>
        <div className="rounded-lg border border-border bg-raised p-6">
          <p className="text-body text-muted">Step {step}: {STEPS[step - 1]} form goes here.</p>
          {step < STEPS.length && (
            <button
              className="mt-4 bg-brand text-white rounded-lg px-4 py-2 text-body-sm hover:opacity-90 transition-opacity"
              onClick={() => setStep((s) => s + 1)}
            >
              Continue
            </button>
          )}
          {step === STEPS.length && (
            <button
              className="mt-4 bg-brand text-white rounded-lg px-4 py-2 text-body-sm hover:opacity-90 transition-opacity"
              onClick={() => (window.location.href = '/')}
            >
              Get Started
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
