import { useState, useEffect, useCallback } from "react"

interface User {
  id: number
  email: string
  name: string | null
  created_at: string
}

interface AuthState {
  user: User | null
  token: string | null
  loading: boolean
}

const API_BASE = "/api/auth"

export function useAuth() {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: localStorage.getItem("ll_token"),
    loading: true,
  })

  const setAuth = useCallback((token: string, user: User) => {
    localStorage.setItem("ll_token", token)
    setState({ token, user, loading: false })
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem("ll_token")
    setState({ token: null, user: null, loading: false })
  }, [])

  // Check token validity on mount
  useEffect(() => {
    const token = localStorage.getItem("ll_token")
    if (!token) {
      setState({ token: null, user: null, loading: false })
      return
    }

    fetch(`${API_BASE}/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => {
        if (!r.ok) throw new Error("Invalid token")
        return r.json()
      })
      .then((user) => setState({ token, user, loading: false }))
      .catch(() => {
        localStorage.removeItem("ll_token")
        setState({ token: null, user: null, loading: false })
      })
  }, [])

  const register = async (email: string, password: string, name?: string) => {
    const r = await fetch(`${API_BASE}/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, name }),
    })
    if (!r.ok) {
      const err = await r.json()
      throw new Error(err.detail || "Registration failed")
    }
    const data = await r.json()
    setAuth(data.access_token, data.user)
  }

  const login = async (email: string, password: string) => {
    const body = new URLSearchParams()
    body.append("username", email)
    body.append("password", password)

    const r = await fetch(`${API_BASE}/login`, {
      method: "POST",
      body,
    })
    if (!r.ok) {
      const err = await r.json()
      throw new Error(err.detail || "Login failed")
    }
    const data = await r.json()
    setAuth(data.access_token, data.user)
  }

  return { ...state, login, register, logout }
}

export function authHeaders(): Record<string, string> {
  const token = localStorage.getItem("ll_token")
  return token ? { Authorization: `Bearer ${token}` } : {}
}
