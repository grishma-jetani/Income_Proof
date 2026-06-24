import { Lightbulb } from 'lucide-react'

export default function ActionTipCard({ tip }) {
  if (!tip) return null
  return (
    <div className="flex items-start gap-3 bg-gold/10 border border-gold/40 rounded-2xl p-4">
      <div className="w-8 h-8 rounded-full bg-gold/20 flex items-center justify-center flex-shrink-0 mt-0.5">
        <Lightbulb size={15} className="text-gold" />
      </div>
      <div>
        <p className="text-xs font-semibold text-gold uppercase tracking-wide mb-1">Action Tip</p>
        <p className="text-sm text-ink leading-relaxed">{tip}</p>
      </div>
    </div>
  )
}