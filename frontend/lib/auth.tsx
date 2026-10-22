"use client"

import * as React from "react"
import { api, setAuthToken } from "@/lib/api"

export type User = {
  username: string
  name: string
  role: "admin" | "requester" | "officer" | "approver" | "auditor"
  role_label: string
  title: string
  description: string
  approval_limit: number | null
}

type AuthContextValue = {
  user: User | null
  loading: boolean
  login: (username: string, password: string) => Promise<User>
  logout: () => void
}

const USER_KEY = "buywise_user"
const AuthContext = React.createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = React.useState<User | null>(null)
  const [loading, setLoading] = React.useState(true)

  React.useEffect(() => {
    const storedToken = typeof window !== "undefined" ? localStorage.getItem("buywise_token") : null
    if (!storedToken) {
      setLoading(false)
      return
    }

    const cached = typeof window !== "undefined" ? localStorage.getItem(USER_KEY) : null
    if (cached) {
      try {
        setUser(JSON.parse(cached))
      } catch {
        // ignore malformed cache
      }
    }

    api.get<User>("/auth/me")
      .then((fresh) => {
        setUser(fresh)
        localStorage.setItem(USER_KEY, JSON.stringify(fresh))
      })
      .catch(() => {
        setAuthToken(null)
        localStorage.removeItem(USER_KEY)
        setUser(null)
      })
      .finally(() => setLoading(false))
  }, [])

  const login = React.useCallback(async (username: string, password: string) => {
    const result = await api.post<{ token: string; user: User }>("/auth/login", {
      username,
      password,
    })
    setAuthToken(result.token)
    localStorage.setItem(USER_KEY, JSON.stringify(result.user))
    setUser(result.user)
    return result.user
  }, [])

  const logout = React.useCallback(() => {
    setAuthToken(null)
    if (typeof window !== "undefined") {
      localStorage.removeItem(USER_KEY)
    }
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const context = React.useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider")
  }
  return context
}
