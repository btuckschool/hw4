import { useEffect, useState, type ReactNode } from 'react'
import { AuthContext, type AuthState, type RegisterInput, type User } from './context'

// The session lives in an HttpOnly cookie set by the backend, so the browser
// sends it automatically and page code never sees the token.
async function postJson<T>(url: string, body?: unknown): Promise<T> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (!res.ok) {
    const data = (await res.json().catch(() => null)) as { detail?: unknown } | null
    throw new Error(typeof data?.detail === 'string' ? data.detail : 'Something went wrong. Please try again.')
  }
  return (res.status === 204 ? undefined : await res.json()) as T
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    fetch('/api/auth/me')
      .then((res) => (res.ok ? (res.json() as Promise<User | null>) : null))
      .then(setUser, () => setUser(null))
      .finally(() => setReady(true))
  }, [])

  const value: AuthState = {
    user,
    ready,
    async login(email, password) {
      const u = await postJson<User>('/api/auth/login', { email, password })
      setUser(u)
      return u
    },
    async register(input: RegisterInput) {
      const u = await postJson<User>('/api/auth/register', input)
      setUser(u)
      return u
    },
    async logout() {
      await postJson<void>('/api/auth/logout')
      setUser(null)
    },
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
