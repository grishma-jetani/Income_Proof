export default function StatCard({ label, value, sublabel, icon: Icon, iconColorClass = 'text-forest' }) {
  return (
    <div className="bg-white rounded-2xl shadow-card border border-border p-5 flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <span className="text-sm text-slate font-medium">{label}</span>
        {Icon && <Icon size={18} className={iconColorClass} />}
      </div>
      <span className="font-display text-2xl font-semibold text-ink">{value}</span>
      {sublabel && <span className="text-xs text-slate">{sublabel}</span>}
    </div>
  )
}