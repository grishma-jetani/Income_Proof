import { useEffect, useState, useRef } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { FileSearch, Layers, Tags, Activity, CheckCircle2, AlertCircle } from 'lucide-react'
import { getStatementStatus } from '../api/incomeproof'

const STEPS = [
  { label: 'Parsing statements', icon: FileSearch },
  { label: 'Deduplicating transactions', icon: Layers },
  { label: 'Categorizing transactions', icon: Tags },
  { label: 'Computing stability metrics', icon: Activity },
]

// Visual step transitions: each status update advances the indicator
// so the UI feels responsive even though backend is one atomic task.
const STATUS_TO_STEP = {
  pending: 0,
  processing: 2,
  done: 4,
  failed: 4,
}

export default function ProcessingPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const statementIds = location.state?.statementIds ?? []

  const [displayStep, setDisplayStep] = useState(0)
  const [error, setError] = useState(null)
  const [statuses, setStatuses] = useState([])
  const pollRef = useRef(null)

  // Smoothly animate the step indicator forward
  const advanceStepTo = (target) => {
    setDisplayStep((prev) => {
      if (prev < target) return prev + 1
      return prev
    })
  }

  useEffect(() => {
    if (statementIds.length === 0) {
      navigate('/upload')
      return
    }

    const poll = async () => {
      try {
        const results = await Promise.all(
          statementIds.map((id) => getStatementStatus(id))
        )
        setStatuses(results)

        const allDone = results.every((r) => r.status === 'done')
        const anyFailed = results.some((r) => r.status === 'failed')

        // Advance visual indicator based on earliest/latest status
        const minStep = Math.min(...results.map((r) => STATUS_TO_STEP[r.status] ?? 0))
        advanceStepTo(minStep)

        if (anyFailed) {
          clearInterval(pollRef.current)
          setError('One or more statements failed to process. Check that the file format is supported.')
          return
        }

        if (allDone) {
          clearInterval(pollRef.current)
          // Build the balance check result to pass to Transactions page
          const anyTampered = results.some((r) => r.balance_check_passed === false)
          const balanceDetails = results.map((r) => ({
            statementId: r.statement_id,
            passed: r.balance_check_passed,
            details: r.balance_check_details,
          }))
          setTimeout(() => {
            navigate('/transactions', {
              state: {
                balanceDetails,
                anyTampered,
                allStatuses: results,  // full status objects including authenticity_signals
              },
            })
          }, 600)
        }
      } catch (err) {
        clearInterval(pollRef.current)
        setError('Could not reach the backend. Make sure uvicorn is running on port 8000.')
      }
    }

    // Animate step 0→1 immediately so the screen doesn't look frozen
    const animTimer = setInterval(() => {
      setDisplayStep((prev) => (prev < STATUS_TO_STEP.processing ? prev + 1 : prev))
    }, 700)

    // Poll every 2.5 seconds
    poll() // first call immediately
    pollRef.current = setInterval(poll, 2500)

    return () => {
      clearInterval(pollRef.current)
      clearInterval(animTimer)
    }
  }, [statementIds, navigate])

  const progress = Math.min((displayStep / STEPS.length) * 100, 100)

  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh]">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-card border border-border p-8 flex flex-col gap-6">
        <div className="text-center">
          <h2 className="font-display text-xl font-semibold text-ink">
            Processing {statementIds.length > 1 ? `${statementIds.length} statements` : 'your statement'}
          </h2>
          <p className="text-sm text-slate mt-1">This usually takes less than a minute.</p>
        </div>

        {error ? (
          <div className="flex items-start gap-3 bg-rust/10 border border-rust/30 rounded-xl p-4">
            <AlertCircle size={18} className="text-rust flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-rust">Processing failed</p>
              <p className="text-sm text-ink/80 mt-1">{error}</p>
              <button
                onClick={() => navigate('/upload')}
                className="mt-3 text-xs font-medium text-forest underline"
              >
                Go back and try again
              </button>
            </div>
          </div>
        ) : (
          <>
            <div className="w-full h-1.5 bg-border rounded-full overflow-hidden">
              <div
                className="h-full bg-gold transition-all duration-500 ease-out"
                style={{ width: `${progress}%` }}
              />
            </div>

            <div className="flex flex-col gap-3">
              {STEPS.map((step, i) => {
                const Icon = step.icon
                const isDone = i < displayStep
                const isActive = i === displayStep
                return (
                  <div
                    key={step.label}
                    className={`flex items-center gap-3 px-3 py-2 rounded-xl transition-colors
                      ${isActive ? 'bg-forest/5' : ''}`}
                  >
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0
                        ${isDone ? 'bg-sage/15 text-sage'
                          : isActive ? 'bg-forest/10 text-forest'
                          : 'bg-border text-slate'}`}
                    >
                      {isDone
                        ? <CheckCircle2 size={16} />
                        : isActive
                          ? <Icon size={16} className="animate-pulse" />
                          : <Icon size={16} />}
                    </div>
                    <span className={`text-sm ${isDone || isActive ? 'text-ink font-medium' : 'text-slate'}`}>
                      {step.label}
                    </span>
                  </div>
                )
              })}
            </div>

            {statuses.length > 0 && (
              <p className="text-xs text-slate text-center">
                {statuses.filter((s) => s.status === 'done').length} of {statuses.length} complete
                {statuses[0]?.transaction_count > 0 && ` · ${statuses[0].transaction_count} transactions found`}
              </p>
            )}
          </>
        )}
      </div>
    </div>
  )
}