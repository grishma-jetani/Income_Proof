const BANDS = [
  { min: 78, label: 'Prime', color: '#5B8A72' },
  { min: 62, label: 'Standard', color: '#C8A560' },
  { min: 45, label: 'Developing', color: '#C2654A' },
  { min: 0,  label: 'Limited', color: '#9CA3AF' },
]

function getBand(score) {
  return BANDS.find((b) => score >= b.min) || BANDS[BANDS.length - 1]
}

export default function StabilityScoreCard({ score }) {
  const angle = (score / 100) * 360
  const band = getBand(score)

  return (
    <div className="bg-white rounded-2xl shadow-card border border-border p-5 flex flex-col items-center gap-2">
      <span className="text-sm text-slate font-medium self-start">Income Stability Score</span>

      <div className="relative w-28 h-28 my-2">
        <div
          className="absolute inset-0 rounded-full"
          style={{
            background: `conic-gradient(${band.color} ${angle}deg, #E8E5DE ${angle}deg)`,
          }}
        />
        <div className="absolute inset-2 rounded-full bg-white flex flex-col items-center justify-center">
          <span className="font-display text-3xl font-semibold" style={{ color: band.color }}>
            {score}
          </span>
          <span className="text-xs text-slate">/ 100</span>
        </div>
      </div>

      <span
        className="text-xs font-semibold px-2.5 py-0.5 rounded-full"
        style={{ backgroundColor: `${band.color}20`, color: band.color }}
      >
        {band.label}
      </span>
    </div>
  )
}