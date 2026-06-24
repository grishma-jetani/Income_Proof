import { useState } from 'react'
import { FileDown, FileText, Home, Loader2, CheckCircle2, AlertCircle } from 'lucide-react'
import { mockTotals, mockStability } from '../mock/mockData'
import { generateReport } from '../api/incomeproof'
import { getDashboard, getStability } from '../api/incomeproof'
import { useEffect } from 'react'

const TEMPLATES = [
  {
    id: 'loan',
    label: 'Loan Application',
    icon: FileText,
    description: 'Emphasizes income stability, trend, and average monthly earnings — formatted for lender review.',
  },
  {
    id: 'rental',
    label: 'Rental Application',
    icon: Home,
    description: 'Emphasizes consistent monthly income and affordability ratio — formatted for landlord review.',
  },
]

export default function ReportPage() {
  const [template, setTemplate] = useState('loan')
  const [startDate, setStartDate] = useState('2026-01-01')
  const [endDate, setEndDate] = useState('2026-04-30')
  const [status, setStatus] = useState(null) // null | 'loading' | 'success' | 'error'
  const [errorMsg, setErrorMsg] = useState('')
  const [dashboard, setDashboard] = useState(null)
  const [stability, setStability] = useState(null)

  useEffect(() => {
    Promise.all([getDashboard(), getStability()])
      .then(([dash, stab]) => {
        setDashboard(dash)
        setStability(stab)
      })
      .catch(() => {})
  }, [])

  const handleDownload = async () => {
    setStatus('loading')
    setErrorMsg('')
    try {
      const blob = await generateReport(startDate, endDate, template)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `incomeproof_${template}_${startDate}_${endDate}.pdf`
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
      setStatus('success')
      setTimeout(() => setStatus(null), 3000)
    } catch (err) {
      const msg = err?.response?.status === 404
        ? 'No transactions found for this date range. Upload statements first.'
        : 'Could not generate report. Make sure the backend is running.'
      setErrorMsg(msg)
      setStatus('error')
    }
  }

  const totalIncome = dashboard?.total_income ?? mockTotals.totalIncome
  const netSavings = dashboard?.net_savings ?? mockTotals.netSavings
  const score = stability?.stability_score ?? mockStability.score
  const hasRealData = dashboard && dashboard.total_income > 0

  return (
    <div className="flex flex-col gap-6 max-w-3xl">
      <div>
        <h2 className="font-display text-2xl font-semibold text-ink">Generate Income Report</h2>
        <p className="text-sm text-slate mt-1">
          Create a shareable PDF summary of your income and stability for lenders or landlords.
        </p>
      </div>

      {!hasRealData && (
        <div className="bg-gold/10 border border-gold/30 rounded-2xl p-4">
          <p className="text-sm text-ink">
            <span className="font-medium">No statements processed yet.</span>{' '}
            The report preview shows demo figures. Upload statements from the sidebar to generate a real report.
          </p>
        </div>
      )}

      <div className="bg-white rounded-2xl shadow-card border border-border p-5 flex flex-col gap-5">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-ink mb-1">From</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full rounded-xl border border-border px-3 py-2 text-sm
                         focus:outline-none focus:ring-2 focus:ring-forest/30 focus:border-forest"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-ink mb-1">To</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full rounded-xl border border-border px-3 py-2 text-sm
                         focus:outline-none focus:ring-2 focus:ring-forest/30 focus:border-forest"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-ink mb-2">Report Template</label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {TEMPLATES.map(({ id, label, icon: Icon, description }) => (
              <button
                key={id}
                onClick={() => setTemplate(id)}
                className={`text-left rounded-xl border p-4 transition-colors
                  ${template === id ? 'border-forest bg-forest/5' : 'border-border hover:border-forest/30'}`}
              >
                <div className="flex items-center gap-2 mb-1.5">
                  <Icon size={16} className={template === id ? 'text-forest' : 'text-slate'} />
                  <span className="text-sm font-semibold text-ink">{label}</span>
                </div>
                <p className="text-xs text-slate leading-relaxed">{description}</p>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Preview */}
      <div className="bg-white rounded-2xl shadow-card border border-border p-5">
        <h3 className="font-display text-lg font-semibold text-ink mb-4">Report Preview</h3>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-xs text-slate">Total Income</p>
            <p className="font-display text-xl font-semibold text-ink mt-1">
              ₹{totalIncome.toLocaleString('en-IN')}
            </p>
          </div>
          <div>
            <p className="text-xs text-slate">Net Savings</p>
            <p className="font-display text-xl font-semibold text-ink mt-1">
              ₹{netSavings.toLocaleString('en-IN')}
            </p>
          </div>
          <div>
            <p className="text-xs text-slate">Stability Score</p>
            <p className="font-display text-xl font-semibold text-gold mt-1">{score} / 100</p>
          </div>
        </div>
        <p className="text-xs text-slate mt-4 leading-relaxed">
          The full report includes a platform-by-platform income breakdown, the stability
          explanation, an actionable tip, and a transaction detail table — all formatted as a
          clean downloadable PDF.
        </p>
      </div>

      {/* Status + button */}
      <div className="flex justify-end items-center gap-3">
        {status === 'success' && (
          <span className="flex items-center gap-1.5 text-sm text-sage font-medium">
            <CheckCircle2 size={16} />
            Report downloaded
          </span>
        )}
        {status === 'error' && (
          <span className="flex items-center gap-1.5 text-sm text-rust font-medium">
            <AlertCircle size={16} />
            {errorMsg}
          </span>
        )}
        <button
          onClick={handleDownload}
          disabled={status === 'loading'}
          className="bg-forest text-cream rounded-xl px-6 py-2.5 text-sm font-medium
                     hover:bg-forest-dark transition-colors
                     disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {status === 'loading' ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              Generating…
            </>
          ) : (
            <>
              <FileDown size={16} />
              Download PDF
            </>
          )}
        </button>
      </div>
    </div>
  )
}