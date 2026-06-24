import { NavLink } from 'react-router-dom'
import { LayoutDashboard, UploadCloud, Receipt, FileText } from 'lucide-react'

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/upload', label: 'Upload Statements', icon: UploadCloud },
  { to: '/transactions', label: 'Transactions', icon: Receipt },
  { to: '/report', label: 'Report', icon: FileText },
]

export default function Sidebar() {
  return (
    <div className="flex flex-col flex-1">
      <div className="px-2 mb-10">
        <h1 className="font-display text-2xl font-semibold">IncomeProof</h1>
        <p className="text-xs text-cream/60 mt-1">Financial identity, simplified</p>
      </div>

      <nav className="flex flex-col gap-1">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all duration-200 ${
                isActive
                  ? 'bg-white/20 text-white font-semibold shadow-sm' 
                  : 'text-cream/70 font-medium hover:bg-white/10 hover:text-white'
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>
    </div>
  )
}