const HIGH_EXPENSE_MULTIPLIER = 1.5
const HIGH_EXPENSE_CATEGORIES = ['Rent', 'Loan EMI']

export default function ChartTooltip({ active, payload, label, avgExpenses }) {
  if (!active || !payload || !payload.length) return null

  const income = payload.find((p) => p.dataKey === 'income')?.value ?? 0
  const expenses = payload.find((p) => p.dataKey === 'expenses')?.value ?? 0
  const isHighExpense = avgExpenses > 0 && expenses > avgExpenses * HIGH_EXPENSE_MULTIPLIER

  return (
    <div className="bg-white rounded-xl border border-border shadow-cardHover p-3 text-xs min-w-[170px]">
      <p className="font-semibold text-ink mb-2">{label}</p>

      <div className="flex items-center justify-between gap-4 mb-1">
        <span className="text-slate flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-forest inline-block" />
          Income
        </span>
        <span className="font-medium text-ink">₹{income.toLocaleString('en-IN')}</span>
      </div>

      <div className="flex items-center justify-between gap-4">
        <span className="text-slate flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-rust inline-block" />
          Expenses
        </span>
        <span className="font-medium text-ink">₹{expenses.toLocaleString('en-IN')}</span>
      </div>

      {isHighExpense && (
        <div className="mt-2 pt-2 border-t border-border">
          <p className="text-rust font-medium">⚠ High expenses this week</p>
          <p className="text-slate mt-0.5 leading-relaxed">
            Likely {HIGH_EXPENSE_CATEGORIES.join(' or ')} — a fixed recurring cost,
            not a sign of overspending.
          </p>
        </div>
      )}

      {income > 0 && expenses > income && !isHighExpense && (
        <div className="mt-2 pt-2 border-t border-border">
          <p className="text-rust font-medium">Expenses exceeded income</p>
          <p className="text-slate mt-0.5">Check for one-off large payments this week.</p>
        </div>
      )}
    </div>
  )
}