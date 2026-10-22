"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import { ArrowRight, Loader2, LockKeyhole, ShieldCheck, User as UserIcon } from "lucide-react"
import { useAuth } from "@/lib/auth"
import { Button } from "@/components/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/badge"

const DEMO_ACCOUNTS = [
  {
    role: "Admin",
    username: "owner",
    password: "owner-pass-123",
    ability: "Manages accounts and everything",
    color: "default" as const,
  },
  {
    role: "Requester",
    username: "req.alice",
    password: "alice-pass-1",
    ability: "Creates procurement requests",
    color: "secondary" as const,
  },
  {
    role: "Officer",
    username: "off.bob",
    password: "bob-pass-22",
    ability: "Runs the agent pipeline + demo",
    color: "pending" as const,
  },
  {
    role: "Approver",
    username: "app.cara",
    password: "cara-pass-33",
    ability: "Approves up to 500,000",
    color: "success" as const,
  },
  {
    role: "Auditor",
    username: "aud.dan",
    password: "dan-pass-44",
    ability: "View-only access",
    color: "warning" as const,
  },
]

export default function LoginPage() {
  const router = useRouter()
  const { user, loading, login } = useAuth()
  const [username, setUsername] = React.useState("")
  const [password, setPassword] = React.useState("")
  const [submitting, setSubmitting] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)

  React.useEffect(() => {
    if (!loading && user) {
      router.replace("/")
    }
  }, [loading, user, router])

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      await login(username.trim(), password)
      router.replace("/")
    } catch (err: any) {
      setError(err?.message || "Unable to sign in")
    } finally {
      setSubmitting(false)
    }
  }

  function useAccount(account: (typeof DEMO_ACCOUNTS)[number]) {
    setUsername(account.username)
    setPassword(account.password)
    setError(null)
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto grid min-h-screen max-w-7xl grid-cols-1 lg:grid-cols-[1.05fr_0.95fr]">
        <section className="relative hidden flex-col justify-between overflow-hidden border-r border-white/10 bg-gradient-to-br from-slate-950 via-slate-900 to-blue-950 p-12 lg:flex">
          <div className="absolute -left-24 top-24 h-72 w-72 rounded-full bg-blue-500/20 blur-3xl" />
          <div className="absolute bottom-0 right-0 h-96 w-96 rounded-full bg-emerald-500/10 blur-3xl" />
          <div className="relative">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-500 font-bold text-white">
                BW
              </div>
              <div>
                <p className="text-lg font-semibold tracking-tight">BuyWise</p>
                <p className="text-xs text-slate-400">Multi-Agent Procurement</p>
              </div>
            </div>

            <h1 className="mt-16 max-w-xl text-5xl font-bold leading-tight tracking-tight">
              Watch every agent think, negotiate and decide.
            </h1>
            <p className="mt-5 max-w-lg text-base leading-7 text-slate-400">
              Eight specialist agents research products, compare vendors, negotiate
              better terms and prepare a recommendation for the right human to approve.
            </p>

            <div className="mt-10 grid max-w-lg grid-cols-2 gap-3">
              {[
                "Product research",
                "Vendor discovery",
                "Quality review",
                "Quote comparison",
                "Decision making",
                "Negotiation",
                "Re-evaluation",
                "Human approval",
              ].map((step, index) => (
                <div
                  key={step}
                  className="flex items-center gap-3 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-300"
                >
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-500/20 text-xs font-semibold text-blue-300">
                    {index + 1}
                  </span>
                  {step}
                </div>
              ))}
            </div>
          </div>

          <div className="relative flex items-center gap-3 text-sm text-slate-400">
            <ShieldCheck className="h-5 w-5 text-emerald-400" />
            Role-based access: requester, officer, approver, auditor and admin.
          </div>
        </section>

        <section className="flex items-center justify-center bg-slate-50 px-5 py-10 text-slate-900 sm:px-8">
          <div className="w-full max-w-xl">
            <div className="mb-6 lg:hidden">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 font-bold text-white">
                  BW
                </div>
                <div>
                  <p className="text-lg font-semibold">BuyWise</p>
                  <p className="text-xs text-slate-500">Multi-Agent Procurement</p>
                </div>
              </div>
            </div>

            <Card className="border-slate-200 shadow-xl shadow-slate-200/60">
              <CardHeader>
                <CardTitle className="text-2xl">Sign in to BuyWise</CardTitle>
                <CardDescription>
                  Use a demo account below or enter your credentials.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="username">Username</Label>
                    <div className="relative">
                      <UserIcon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                      <Input
                        id="username"
                        autoComplete="username"
                        value={username}
                        onChange={(event) => setUsername(event.target.value)}
                        placeholder="req.alice"
                        className="pl-9"
                        required
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="password">Password</Label>
                    <div className="relative">
                      <LockKeyhole className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                      <Input
                        id="password"
                        type="password"
                        autoComplete="current-password"
                        value={password}
                        onChange={(event) => setPassword(event.target.value)}
                        placeholder="••••••••"
                        className="pl-9"
                        required
                      />
                    </div>
                  </div>

                  {error && (
                    <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                      {error}
                    </div>
                  )}

                  <Button type="submit" className="w-full" disabled={submitting}>
                    {submitting ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Signing in...
                      </>
                    ) : (
                      <>
                        Sign in
                        <ArrowRight className="ml-2 h-4 w-4" />
                      </>
                    )}
                  </Button>
                </form>

                <div className="mt-7 border-t border-slate-200 pt-5">
                  <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
                    Demo accounts (click to fill)
                  </p>
                  <div className="space-y-2">
                    {DEMO_ACCOUNTS.map((account) => (
                      <button
                        key={account.username}
                        type="button"
                        onClick={() => useAccount(account)}
                        className="flex w-full items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-left transition hover:border-blue-300 hover:bg-blue-50"
                      >
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <Badge variant={account.color} className="text-[10px]">
                              {account.role}
                            </Badge>
                            <span className="truncate font-mono text-sm font-medium text-slate-900">
                              {account.username}
                            </span>
                          </div>
                          <p className="mt-0.5 truncate text-xs text-slate-500">
                            {account.ability}
                          </p>
                        </div>
                        <span className="shrink-0 font-mono text-[11px] text-slate-400">
                          {account.password}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </section>
      </div>
    </div>
  )
}
