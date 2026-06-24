import { Outlet, useNavigate } from 'react-router-dom'
import Sidebar from '../components/Sidebar'
import { useAuth } from '../context/AuthContext'
import { LogOut } from 'lucide-react'

export default function AppLayout() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()

  const handleSignOut = async () => {
    await signOut()
    navigate('/', { replace: true })
  }

  return (
    <div className="flex min-h-screen bg-cream">
      <aside className="w-64 bg-forest text-cream flex flex-col py-6 px-4 h-screen sticky top-0">
        {/* Sidebar content is inlined here so we can add the sign-out button at the bottom */}
        <Sidebar />

        {/* User + sign out at the very bottom */}
        <div className="mt-auto pt-4 border-t border-forest-light">
          <p className="text-xs text-cream/50 truncate px-2 mb-2">{user?.email}</p>
          <button
            onClick={handleSignOut}
            className="flex items-center gap-2 w-full px-3 py-2 rounded-xl text-sm
                       text-cream/70 hover:bg-forest-light hover:text-cream transition-colors"
          >
            <LogOut size={16} />
            Sign Out
          </button>
        </div>
      </aside>

      <main className="flex-1 p-8">
        <Outlet />
      </main>
    </div>
  )
}