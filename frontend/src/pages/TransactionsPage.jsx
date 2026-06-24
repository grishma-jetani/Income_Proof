import { useState, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { CheckCircle2, AlertTriangle, Flag, Loader2,Info  } from 'lucide-react'
import { getTransactions, updateTransactionCategory } from '../api/incomeproof'
import { categoryOptions } from '../mock/mockData'

export default function TransactionsPage() {
  const location = useLocation()
  const navigate = useNavigate()

  const anyTampered = location.state?.anyTampered ?? false
  const balanceDetails = location.state?.balanceDetails ?? []
  // All statement status objects — used for authenticity + overlap banners
  const allStatuses = location.state?.allStatuses ?? []

  const [transactions, setTransactions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [updatingId, setUpdatingId] = useState(null)

  useEffect(() => {
    getTransactions()
      .then((data) => {
        setTransactions(data)
        setLoading(false)
      })
      .catch(() => {
        setError('Could not load transactions.')
        setLoading(false)
      })
  }, [])

  const handleCategoryChange = async (txnId, category) => {
    setUpdatingId(txnId)
    try {
      await updateTransactionCategory(txnId, category)
      setTransactions((prev) =>
        prev.map((t) => (t.id === txnId ? { ...t, category } : t))
      )
    } catch {
      // silently ignore — category stays as-is in the UI
    } finally {
      setUpdatingId(null)
    }
  }

  // Find which statement IDs failed the balance check
  const failedStatementIds = new Set(
    balanceDetails.filter((d) => d.passed === false).map((d) => d.statementId)
  )

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 size={28} className="text-forest animate-spin" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <p className="text-sm text-rust">{error}</p>
      </div>
    )
  }

  const nonDuplicates = transactions.filter((t) => !t.is_duplicate)
  const duplicateCount = transactions.length - nonDuplicates.length

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="font-display text-2xl font-semibold text-ink">Review Transactions</h2>
        <p className="text-sm text-slate mt-1">
          {nonDuplicates.length} unique transactions extracted
          {duplicateCount > 0 && ` · ${duplicateCount} duplicate${duplicateCount > 1 ? 's' : ''} hidden`}.
          Correct any miscategorized rows below.
        </p>
      </div>

      {/* Balance continuity banner */}
      {anyTampered ? (
        <div className="bg-rust/10 border border-rust/30 rounded-2xl p-4 flex items-start gap-3">
          <AlertTriangle size={20} className="text-rust flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-rust">Possible tampering detected</p>
            {balanceDetails
              .filter((d) => d.passed === false)
              .map((d) => {
                const firstIssue = d.details?.issues?.[0]
                return (
                  <p key={d.statementId} className="text-sm text-ink/80 mt-1">
                    Statement balance continuity check failed
                    {firstIssue && (
                      <>
                        {' '}on row {firstIssue.row}: expected&nbsp;
                        <span className="font-medium">₹{firstIssue.expected.toLocaleString('en-IN')}</span>,
                        printed&nbsp;
                        <span className="font-medium">₹{firstIssue.actual.toLocaleString('en-IN')}</span>&nbsp;
                        (discrepancy ₹{Math.abs(firstIssue.discrepancy).toLocaleString('en-IN')}).
                      </>
                    )}{' '}
                    This statement should be flagged for manual review before inclusion in any income report.
                  </p>
                )
              })}
          </div>
        </div>
      ) : (
        <div className="bg-sage/10 border border-sage/30 rounded-2xl p-4 flex items-center gap-3">
          <CheckCircle2 size={20} className="text-sage flex-shrink-0" />
          <p className="text-sm font-medium text-ink">
            All uploaded statements passed the balance continuity check.
          </p>
        </div>
      )}

      {/* Authenticity banners */}
      {allStatuses
        .filter((s) => s.authenticity_signals)
        .map((s) => {
          const sig = s.authenticity_signals
          const signal = sig?.overall_signal
          if (!signal || signal === 'verified') return null

          const isAlert = signal === 'suspicious'
          const Icon = isAlert ? AlertTriangle : Info
          const colorClass = isAlert
            ? 'bg-rust/10 border-rust/30 text-rust'
            : 'bg-gold/10 border-gold/40 text-gold'
          const labelClass = isAlert ? 'text-rust' : 'text-gold'

          return (
            <div
              key={s.statement_id}
              className={`flex items-start gap-3 rounded-2xl p-4 border ${colorClass}`}
            >
              <Icon size={20} className="flex-shrink-0 mt-0.5" />
              <div>
                <p className={`text-sm font-semibold ${labelClass}`}>
                  {signal === 'suspicious'
                    ? 'Statement authenticity warning'
                    : 'Statement authenticity — limited confidence'}
                </p>
                <p className="text-sm text-ink/80 mt-1">{sig.overall_explanation}</p>
                {sig.checks?.filter((c) => c.passed === false).map((c) => (
                  <p key={c.check} className="text-xs text-slate mt-1">
                    ⚠ {c.detail}
                  </p>
                ))}
              </div>
            </div>
          )
        })}

      {/* Cross-source overlap banner */}
      {allStatuses.some((s) => s.has_cross_source_overlap) && (
        <div className="bg-gold/10 border border-gold/40 rounded-2xl p-4 flex items-start gap-3">
          <Info size={20} className="text-gold flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-gold">
              Cross-source date overlap detected
            </p>
            {allStatuses
              .filter((s) => s.has_cross_source_overlap && s.overlap_details?.conflicts)
              .map((s) =>
                s.overlap_details.conflicts.map((conflict, i) => (
                  <p key={i} className="text-sm text-ink/80 mt-1">
                    {s.overlap_details.new_source} overlaps with {conflict.existing_source} during{' '}
                    <span className="font-medium">{conflict.overlap_range}</span>.{' '}
                    {conflict.risk}
                  </p>
                ))
              )}
            <p className="text-xs text-slate mt-2">
              Income in the overlapping period may appear in multiple statements. Review the amounts carefully before sharing this report with lenders.
            </p>
          </div>
        </div>
      )}
      
      <div className="bg-white rounded-2xl shadow-card border border-border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-cream text-left text-xs text-slate uppercase tracking-wide">
                <th className="px-4 py-3 font-medium">Date</th>
                <th className="px-4 py-3 font-medium">Description</th>
                <th className="px-4 py-3 font-medium">Source</th>
                <th className="px-4 py-3 font-medium">Category</th>
                <th className="px-4 py-3 font-medium text-right">Amount</th>
              </tr>
            </thead>
            <tbody>
              {nonDuplicates.map((t) => {
                const isFlaggedStatement = failedStatementIds.has(t.statement_id)
                return (
                  <tr
                    key={t.id}
                    className={`border-t border-border ${isFlaggedStatement ? 'bg-rust/5' : ''}`}
                  >
                    <td className="px-4 py-3 whitespace-nowrap text-ink">{t.txn_date}</td>
                    <td className="px-4 py-3 text-ink">
                      <div className="flex items-center gap-2">
                        {isFlaggedStatement && (
                          <Flag size={13} className="text-rust flex-shrink-0" />
                        )}
                        <span className="truncate max-w-[260px]">{t.description}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-slate whitespace-nowrap">{t.source_format}</td>
                    <td className="px-4 py-3">
                      <div className="relative">
                        <select
                          value={t.category || 'Personal / Other'}
                          onChange={(e) => handleCategoryChange(t.id, e.target.value)}
                          disabled={updatingId === t.id}
                          className="text-xs rounded-lg border border-border px-2 py-1.5 bg-cream
                                     focus:outline-none focus:ring-2 focus:ring-forest/30
                                     disabled:opacity-50"
                        >
                          {categoryOptions.map((c) => (
                            <option key={c} value={c}>{c}</option>
                          ))}
                        </select>
                        {updatingId === t.id && (
                          <Loader2 size={12} className="absolute right-6 top-2 text-slate animate-spin" />
                        )}
                      </div>
                    </td>
                    <td className={`px-4 py-3 text-right font-medium whitespace-nowrap
                      ${parseFloat(t.credit) > 0 ? 'text-sage' : 'text-rust'}`}>
                      {parseFloat(t.credit) > 0
                        ? `+₹${parseFloat(t.credit).toLocaleString('en-IN')}`
                        : `-₹${parseFloat(t.debit).toLocaleString('en-IN')}`}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      <div className="flex justify-end">
        <button
          onClick={() => navigate('/dashboard')}
          className="bg-forest text-cream rounded-xl px-6 py-2.5 text-sm font-medium
                     hover:bg-forest-dark transition-colors"
        >
          View Dashboard
        </button>
      </div>
    </div>
  )
}