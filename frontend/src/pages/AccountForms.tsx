import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'

// After logging in, send the shopper back to the page they came from (or home).
function useReturnTo() {
  const location = useLocation()
  const from = (location.state as { from?: string } | null)?.from
  return from && from !== '/login' && from !== '/create-account' ? from : '/'
}

function SignedInNotice() {
  const { user, logout } = useAuth()
  return (
    <div className="container page auth-page">
      <div className="auth-card">
        <h1>You're signed in</h1>
        <p className="auth-sub">
          Logged in as {user?.first_name} {user?.last_name} ({user?.email}).
        </p>
        <Link to="/products" className="btn btn-primary btn-block">
          Browse products
        </Link>
        <button className="btn btn-outline btn-block" onClick={() => void logout()}>
          Log out
        </button>
      </div>
    </div>
  )
}

export function Login() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const returnTo = useReturnTo()
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (user) return <SignedInNotice />

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const form = new FormData(e.currentTarget)
    setBusy(true)
    setError(null)
    try {
      await login(String(form.get('email')), String(form.get('password')))
      navigate(returnTo, { replace: true })
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="container page auth-page">
      <form className="auth-card" onSubmit={submit}>
        <h1>Log in</h1>
        <p className="auth-sub">Welcome back to Campus Customs.</p>
        <label>
          Email
          <input type="email" name="email" autoComplete="email" required />
        </label>
        <label>
          Password
          <input type="password" name="password" autoComplete="current-password" required />
        </label>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        <button type="submit" className="btn btn-primary btn-block" disabled={busy}>
          {busy ? 'Logging in…' : 'Log in'}
        </button>
        <p className="auth-switch">
          New here? <Link to="/create-account">Create an account</Link>
        </p>
      </form>
    </div>
  )
}

export function CreateAccount() {
  const { user, register } = useAuth()
  const navigate = useNavigate()
  const returnTo = useReturnTo()
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (user) return <SignedInNotice />

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const form = new FormData(e.currentTarget)
    const get = (name: string) => String(form.get(name) ?? '')
    if (get('password') !== get('confirm_password')) {
      setError('Passwords do not match.')
      return
    }
    setBusy(true)
    setError(null)
    try {
      await register({
        first_name: get('first_name'),
        last_name: get('last_name'),
        email: get('email'),
        password: get('password'),
        confirm_password: get('confirm_password'),
      })
      navigate(returnTo, { replace: true })
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="container page auth-page">
      <form className="auth-card" onSubmit={submit}>
        <h1>Create account</h1>
        <p className="auth-sub">Join Campus Customs to shop and chat with our assistant.</p>
        <div className="form-row">
          <label>
            First name
            <input name="first_name" autoComplete="given-name" maxLength={50} required />
          </label>
          <label>
            Last name
            <input name="last_name" autoComplete="family-name" maxLength={50} required />
          </label>
        </div>
        <label>
          Email
          <input type="email" name="email" autoComplete="email" required />
        </label>
        <label>
          Password
          <input
            type="password"
            name="password"
            autoComplete="new-password"
            minLength={8}
            maxLength={128}
            required
          />
          <span className="field-hint">At least 8 characters.</span>
        </label>
        <label>
          Confirm password
          <input
            type="password"
            name="confirm_password"
            autoComplete="new-password"
            minLength={8}
            maxLength={128}
            required
          />
        </label>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        <button type="submit" className="btn btn-primary btn-block" disabled={busy}>
          {busy ? 'Creating account…' : 'Create account'}
        </button>
        <p className="auth-switch">
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </form>
    </div>
  )
}
