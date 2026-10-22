const DEFAULT_API_BASE = "http://127.0.0.1:8000/api"
const TOKEN_KEY = "buywise_token"

let authToken: string | null = null

export function setAuthToken(token: string | null) {
  authToken = token
  if (typeof window === "undefined") return
  if (token) {
    localStorage.setItem(TOKEN_KEY, token)
  } else {
    localStorage.removeItem(TOKEN_KEY)
  }
}

function getAuthToken(): string | null {
  if (authToken) return authToken
  if (typeof window !== "undefined") {
    authToken = localStorage.getItem(TOKEN_KEY)
  }
  return authToken
}

export function getApiBase(): string {
  const configured = process.env.NEXT_PUBLIC_API_URL || DEFAULT_API_BASE
  if (typeof window === "undefined") return configured

  try {
    const url = new URL(configured)
    const configuredHost = url.hostname
    const pageHost = window.location.hostname
    const loopback = configuredHost === "localhost" || configuredHost === "127.0.0.1"
    const pageLoopback = pageHost === "localhost" || pageHost === "127.0.0.1"

    if (loopback && !pageLoopback) {
      url.hostname = pageHost
    }
    return url.toString().replace(/\/$/, "")
  } catch {
    return configured
  }
}

async function apiRequest<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const base = getApiBase()
  const token = getAuthToken()

  let res: Response
  try {
    res = await fetch(`${base}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
      },
      ...options,
    })
  } catch {
    throw new Error(
      `Cannot reach the BuyWise backend at ${base}. Make sure it is running and reachable from this browser.`
    )
  }

  if (res.status === 401 && !path.startsWith("/auth/")) {
    setAuthToken(null)
    if (typeof window !== "undefined") {
      window.location.href = "/login"
    }
    throw new Error("Your session expired. Please sign in again.")
  }

  if (!res.ok) {
    let errorDetail = "Unknown error"
    try {
      const body = await res.json()
      errorDetail = body.detail || errorDetail
    } catch {
      errorDetail = res.statusText
    }
    throw new Error(errorDetail)
  }

  if (res.status === 204) return undefined as unknown as T
  return res.json()
}

export const api = {
  get: <T>(path: string, params?: Record<string, string>): Promise<T> => {
    let url = path
    if (params) {
      const search = new URLSearchParams(params).toString()
      url += `?${search}`
    }
    return apiRequest<T>(url)
  },
  post: <T>(path: string, body: any): Promise<T> =>
    apiRequest<T>(path, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  put: <T>(path: string, body: any): Promise<T> =>
    apiRequest<T>(path, {
      method: "PUT",
      body: JSON.stringify(body),
    }),
}

export function createEventSource(path: string): EventSource {
  const token = getAuthToken()
  const separator = path.includes("?") ? "&" : "?"
  const url = `${getApiBase()}${path}${token ? `${separator}token=${encodeURIComponent(token)}` : ""}`
  return new EventSource(url)
}