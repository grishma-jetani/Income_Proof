import { useEffect, useState } from 'react'
import { Wallet, TrendingDown, PiggyBank, Loader2 } from 'lucide-react'
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid,
  PieChart, Pie, Cell,
} from 'recharts'
import StatCard from '../components/StatCard'
import StabilityScoreCard from '../components/StabilityScoreCard'
import ChartTooltip from '../components/ChartTooltip'
import ActionTipCard from '../components/ActionTipCard'
import { getDashboard, getStability } from '../api/incomeproof'
import FactorBreakdown from '../components/FactorBreakdown'

export default function DashboardPage() {
  const [dashboard, setDashboard] = useState(null)
  const [stability, setStability] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getDashboard(), getStability()])
      .then(([dash, stab]) => {
        setDashboard(dash)
        setStability(stab)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 size={28} className="text-forest animate-spin" />
      </div>
    )
  }

  const isEmpty = !dashboard || dashboard.total_income === 0
  const avgExpenses =
    dashboard?.weekly_trend?.length > 0
      ? dashboard.weekly_trend.reduce((s, w) => s + w.expenses, 0) / dashboard.weekly_trend.length
      : 0

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="font-display text-2xl font-semibold text-ink">Dashboard</h2>
        <p className="text-sm text-slate mt-1">
          {isEmpty
            ? 'Upload your first statement to see your financial identity.'
            : `Showing data from ${stability?.period_start ?? '—'} to ${stability?.period_end ?? '—'}.`}
        </p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Income"
          value={isEmpty ? '—' : `₹${dashboard.total_income.toLocaleString('en-IN')}`}
          sublabel="All statements"
          icon={Wallet}
          iconColorClass="text-forest"
        />
        <StatCard
          label="Total Expenses"
          value={isEmpty ? '—' : `₹${dashboard.total_expenses.toLocaleString('en-IN')}`}
          sublabel="All statements"
          icon={TrendingDown}
          iconColorClass="text-rust"
        />
        <StatCard
          label="Net Savings"
          value={isEmpty ? '—' : `₹${dashboard.net_savings.toLocaleString('en-IN')}`}
          sublabel="All statements"
          icon={PiggyBank}
          iconColorClass="text-sage"
        />
        <StabilityScoreCard score={isEmpty ? 0 : stability?.stability_score ?? 0} />
      </div>

      {isEmpty ? (
        <div className="bg-white rounded-2xl shadow-card border border-border p-12 flex flex-col items-center gap-4 text-center">
          <div className="w-14 h-14 rounded-full bg-forest/10 flex items-center justify-center">
            <Wallet size={24} className="text-forest" />
          </div>
          <div>
            <p className="text-base font-semibold text-ink">No data yet</p>
            <p className="text-sm text-slate mt-1 max-w-xs">
              Go to Upload Statements and add your bank PDFs or UPI exports to populate this dashboard.
            </p>
          </div>
        </div>
      ) : (
        <>
          {/* Charts row */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="lg:col-span-2 bg-white rounded-2xl shadow-card border border-border p-5">
              <h3 className="font-display text-lg font-semibold text-ink mb-4">
                Income vs Expenses
              </h3>
              <ResponsiveContainer width="100%" height={260}>
                <AreaChart data={dashboard.weekly_trend}>
                  <defs>
                    <linearGradient id="incomeFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#2D4A43" stopOpacity={0.25} />
                      <stop offset="100%" stopColor="#2D4A43" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="expenseFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#C2654A" stopOpacity={0.2} />
                      <stop offset="100%" stopColor="#C2654A" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="#E8E5DE" strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="week" tick={{ fontSize: 11, fill: '#6B7280' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: '#6B7280' }} axisLine={false} tickLine={false} />
                  <Tooltip
                    content={(props) => (
                      <ChartTooltip {...props} avgExpenses={avgExpenses} />
                    )}
                  />
                  <Area type="monotone" dataKey="income" stroke="#2D4A43" fill="url(#incomeFill)" strokeWidth={2} name="Income" />
                  <Area type="monotone" dataKey="expenses" stroke="#C2654A" fill="url(#expenseFill)" strokeWidth={2} name="Expenses" />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-white rounded-2xl shadow-card border border-border p-5">
              <h3 className="font-display text-lg font-semibold text-ink mb-4">
                Income by Source
              </h3>
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie
                    data={dashboard.category_breakdown}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={55}
                    outerRadius={80}
                    paddingAngle={2}
                  >
                    {dashboard.category_breakdown.map((entry) => (
                      <Cell key={entry.name} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(val) => `${val}%`}
                    contentStyle={{ borderRadius: '0.75rem', border: '1px solid #E8E5DE', fontSize: '12px' }}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex flex-col gap-1.5 mt-2">
                {dashboard.category_breakdown.map((c) => (
                  <div key={c.name} className="flex items-center justify-between text-xs">
                    <span className="flex items-center gap-2 text-ink">
                      <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: c.color }} />
                      {c.name}
                    </span>
                    <span className="text-slate">{c.value}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Stability + action tip */}
          <div className="bg-white rounded-2xl shadow-card border border-border p-5">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-display text-lg font-semibold text-ink">What this score means</h3>
              <span className="text-xs text-slate bg-cream rounded-lg px-3 py-1 border border-border">
                CV: {stability?.cv_pct?.toFixed(1)}%
                · Trend: {stability?.trend_pct > 0 ? '+' : ''}{((stability?.trend_pct ?? 0) * 100).toFixed(1)}%/week
              </span>
            </div>
            <p className="text-sm text-slate leading-relaxed mb-4">{stability?.explanation}</p>
            <ActionTipCard tip={stability?.action_tip} />
          </div>
          
          {/* Factor breakdown */}
          <FactorBreakdown factorDetail={stability?.factor_detail} />
          
          {/* Recent transactions */}
          <div className="bg-white rounded-2xl shadow-card border border-border p-5">
            <h3 className="font-display text-lg font-semibold text-ink mb-4">Recent Transactions</h3>
            <div className="flex flex-col">
              {dashboard.recent_transactions.map((t, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between py-3 border-b border-border last:border-0"
                >
                  <div>
                    <p className="text-sm text-ink font-medium truncate max-w-xs">{t.description}</p>
                    <p className="text-xs text-slate mt-0.5">{t.date} · {t.category}</p>
                  </div>
                  <span className={`text-sm font-semibold ${t.type === 'credit' ? 'text-sage' : 'text-rust'}`}>
                    {t.type === 'credit' ? '+' : '-'}₹{parseFloat(t.amount).toLocaleString('en-IN')}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}