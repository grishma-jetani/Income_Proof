import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Loader2, AlertCircle } from 'lucide-react'

export default function LoginPage() {
  const { signIn, signUp, user } = useAuth()
  const navigate = useNavigate()

  const [mode, setMode] = useState('signin')   // 'signin' | 'signup'
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [signupSuccess, setSignupSuccess] = useState(false)

  // If already logged in, redirect immediately
  if (user) {
    navigate('/dashboard', { replace: true })
    return null
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      if (mode === 'signup') {
        await signUp(email, password)
        setSignupSuccess(true)
      } else {
        await signIn(email, password)
        navigate('/dashboard', { replace: true })
      }
    } catch (err) {
      setError(err.message || 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-cream px-4">
      <div className="w-full max-w-sm bg-white rounded-2xl shadow-card border border-border p-8">

        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="font-display text-3xl font-semibold text-ink">IncomeProof</h1>
          <p className="text-sm text-slate mt-2">
            Turn irregular income into a clear financial identity.
          </p>
        </div>

        {/* Signup success message */}
        {signupSuccess ? (
          <div className="flex flex-col items-center gap-4 text-center py-4">
            <div className="w-12 h-12 rounded-full bg-sage/15 flex items-center justify-center">
              <span className="text-2xl">✉️</span>
            </div>
            <div>
              <p className="text-sm font-semibold text-ink">Check your email</p>
              <p className="text-sm text-slate mt-1">
                We sent a confirmation link to <span className="font-medium">{email}</span>.
                Click it to activate your account, then sign in.
              </p>
            </div>
            <button
              onClick={() => { setMode('signin'); setSignupSuccess(false) }}
              className="text-sm text-forest font-medium underline"
            >
              Back to Sign In
            </button>
          </div>
        ) : (
          <>
            {/* Mode toggle */}
            <div className="flex bg-cream rounded-xl border border-border p-1 mb-6">
              {['signin', 'signup'].map((m) => (
                <button
                  key={m}
                  onClick={() => { setMode(m); setError(null) }}
                  className={`flex-1 rounded-lg py-1.5 text-sm font-medium transition-colors ${
                    mode === m
                      ? 'bg-white text-ink shadow-sm'
                      : 'text-slate hover:text-ink'
                  }`}
                >
                  {m === 'signin' ? 'Sign In' : 'Sign Up'}
                </button>
              ))}
            </div>

            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <div>
                <label className="block text-sm font-medium text-ink mb-1">Email</label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="w-full rounded-xl border border-border px-4 py-2.5 text-sm
                             focus:outline-none focus:ring-2 focus:ring-forest/30 focus:border-forest"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-ink mb-1">Password</label>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={mode === 'signup' ? 'At least 6 characters' : '••••••••'}
                  className="w-full rounded-xl border border-border px-4 py-2.5 text-sm
                             focus:outline-none focus:ring-2 focus:ring-forest/30 focus:border-forest"
                />
              </div>

              {error && (
                <div className="flex items-start gap-2 bg-rust/10 border border-rust/30 rounded-xl p-3">
                  <AlertCircle size={15} className="text-rust flex-shrink-0 mt-0.5" />
                  <p className="text-xs text-rust">{error}</p>
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="mt-1 bg-forest text-cream rounded-xl py-2.5 text-sm font-medium
                           hover:bg-forest-dark transition-colors
                           disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loading ? (
                  <><Loader2 size={15} className="animate-spin" /> {mode === 'signup' ? 'Creating account…' : 'Signing in…'}</>
                ) : (
                  mode === 'signup' ? 'Create Account' : 'Sign In'
                )}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  )
}