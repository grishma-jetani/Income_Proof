const FACTOR_META = {
  regularity: {
    label: 'Income Regularity',
    weight: '30%',
    method: 'MAD/median Robust CV',
    tooltip: 'Uses Median Absolute Deviation — robust to outliers at small sample sizes. Inspired by Farrell & Greig (2016).',
  },
  income_floor: {
    label: 'Income Floor',
    weight: '25%',
    method: 'P25/median (adaptive)',
    tooltip: 'P25/median at N<30, P10/median at N≥30. Inspired by US Financial Diaries floor methodology.',
  },
  trend_momentum: {
    label: 'Trend Momentum',
    weight: '20%',
    method: 'OLS slope × R²',
    tooltip: 'Slope weighted by goodness-of-fit. Normalised to 0.8%/week as exceptional gig-worker growth.',
  },
  concentration_risk: {
    label: 'Platform Concentration Risk',
    weight: '15%',
    method: 'Inverted HHI',
    tooltip: 'Herfindahl-Hirschman Index applied to income sources. Experimental — directionally correct, novel application.',
    experimental: true,
  },
  consistency_rate: {
    label: 'Income Consistency Rate',
    weight: '10%',
    method: 'Weeks-with-income / covered weeks',
    tooltip: 'Replaces lag-1 autocorrelation, which requires N≥20. Simple, transparent, and robust at any sample size.',
  },
}

const BAND_COLORS = {
  Consistent:    '#5B8A72',
  Variable:      '#C8A560',
  Developing:    '#C2654A',
  'Early Stage': '#9CA3AF',
}

function ScoreBar({ score }) {
  const color =
    score >= 70 ? '#5B8A72'
    : score >= 45 ? '#C8A560'
    : '#C2654A'
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-2 bg-border rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${score}%`, backgroundColor: color }}
        />
      </div>
      <span className="text-sm font-semibold w-9 text-right" style={{ color }}>
        {score.toFixed(0)}
      </span>
    </div>
  )
}

export default function FactorBreakdown({ factorDetail }) {
  if (!factorDetail?.factor_scores) return null

  const {
    factor_scores,
    factor_meta,
    score_band,
    band_description,
    num_weeks_analysed,
    below_minimum_income,
    adequacy_note,
    raw_score_before_cap,
    known_limitations,
    weights,
  } = factorDetail

  const bandColor = BAND_COLORS[score_band] || '#9CA3AF'

  return (
    <div className="bg-white rounded-2xl shadow-card border border-border p-5 flex flex-col gap-5">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-display text-lg font-semibold text-ink">Score Breakdown</h3>
          <p className="text-xs text-slate mt-0.5">
            Five-factor weighted composite · {num_weeks_analysed} weeks analysed
          </p>
        </div>
        <div
          className="text-xs font-semibold px-3 py-1 rounded-full"
          style={{ backgroundColor: `${bandColor}20`, color: bandColor }}
        >
          {score_band}
        </div>
      </div>

      {below_minimum_income && adequacy_note && (
        <div className="bg-rust/10 border border-rust/30 rounded-xl p-3">
          <p className="text-xs font-semibold text-rust mb-0.5">
            Income level below minimum threshold
          </p>
          <p className="text-xs text-ink/80 leading-relaxed">{adequacy_note}</p>
          {raw_score_before_cap !== undefined && (
            <p className="text-xs text-slate mt-1">
              Pattern quality score (uncapped): {raw_score_before_cap.toFixed(0)}/100
            </p>
          )}
        </div>
      )}

      <div className="flex flex-col gap-4">
        {Object.entries(FACTOR_META).map(([key, meta]) => {
          const score = factor_scores?.[key] ?? null
          const detail = factor_meta?.[key] ?? {}
          const isExperimental = meta.experimental === true

          if (score === null) return null

          return (
            <div key={key}>
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-1.5 flex-wrap">
                  <span className="text-sm font-medium text-ink">{meta.label}</span>
                  {isExperimental && (
                    <span className="text-xs bg-gold/15 text-gold px-1.5 py-0.5 rounded font-medium">
                      experimental
                    </span>
                  )}
                  <span className="text-xs text-slate">· {meta.weight}</span>
                </div>
                <span className="text-xs text-slate ml-2 flex-shrink-0">{meta.method}</span>
              </div>
              <ScoreBar score={score} />
              <p className="text-xs text-slate mt-1 leading-relaxed">
                {detail.interpretation || meta.tooltip}
              </p>
              {detail.limitation && (
                <p className="text-xs text-gold mt-0.5">⚠ {detail.limitation}</p>
              )}
            </div>
          )
        })}
      </div>

      {/* Weight summary */}
      <div className="bg-cream rounded-xl border border-border p-3">
        <p className="text-xs font-semibold text-ink mb-2">Factor Weights</p>
        <div className="grid grid-cols-5 gap-1 text-center">
          {Object.entries(FACTOR_META).map(([key, meta]) => (
            <div key={key}>
              <div className="text-xs font-semibold text-forest">{meta.weight}</div>
              <div className="text-xs text-slate leading-tight mt-0.5 truncate">
                {meta.label.split(' ')[0]}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Methodology */}
      <div className="border-t border-border pt-3">
        <p className="text-xs font-semibold text-ink mb-1">Methodology</p>
        <p className="text-xs text-slate leading-relaxed">
          Structural form inspired by Farrell &amp; Greig (2016) — JPMC Institute;
          Morduch &amp; Schneider (2017) — US Financial Diaries;
          Dynan, Elmendorf &amp; Sichel (2012) — income persistence.
          Scaling constants are design priors pending calibration against
          loan repayment outcome data.
        </p>

        {known_limitations?.length > 0 && (
          <details className="mt-2">
            <summary className="text-xs text-slate cursor-pointer hover:text-ink select-none">
              Known limitations ({known_limitations.length})
            </summary>
            <ul className="mt-1 space-y-1">
              {known_limitations.map((lim, i) => (
                <li key={i} className="text-xs text-slate leading-relaxed">· {lim}</li>
              ))}
            </ul>
          </details>
        )}
      </div>
    </div>
  )
}