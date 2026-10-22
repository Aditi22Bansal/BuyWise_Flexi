"use client"

import { useCallback, useEffect, useState } from "react"
import DashboardLayout from "@/app/dashboard-layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/card"
import { Badge } from "@/components/badge"
import { Button } from "@/components/button"
import { api, createEventSource } from "@/lib/api"
import { useAuth } from "@/lib/auth"
import { formatCurrency } from "@/lib/utils"
import {
  Activity,
  Bot,
  CheckCircle2,
  Clock,
  Play,
  RefreshCw,
  Sparkles,
  XCircle,
} from "lucide-react"
import { cn } from "@/lib/utils"

const AGENT_NAMES = [
  "Product Research Agent",
  "Vendor Research Agent",
  "Review & Quality Agent",
  "Comparison Agent",
  "Decision Agent",
  "Negotiation Agent",
  "Re-evaluation Agent",
  "Approval Agent",
]

type LogEntry = { time: string; text: string; kind: "info" | "success" | "error" }

export default function AgentActivityPage() {
  const { user } = useAuth()
  const [requests, setRequests] = useState<any[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [detail, setDetail] = useState<any>(null)
  const [audit, setAudit] = useState<any[]>([])
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const canRun = user?.role === "admin" || user?.role === "officer"
  const canCreate = user?.role === "admin" || user?.role === "requester"

  const addLog = useCallback((text: string, kind: LogEntry["kind"] = "info") => {
    setLogs((prev) => [
      { time: new Date().toLocaleTimeString(), text, kind },
      ...prev,
    ].slice(0, 200))
  }, [])

  const loadRequests = useCallback(async () => {
    try {
      const rows = await api.get<any[]>("/procurement-requests?limit=50")
      setRequests(rows)
      setSelectedId((current) => {
        if (current && rows.some((r) => r.id === current)) return current
        return rows[0]?.id ?? null
      })
    } catch (err: any) {
      setError(err?.message || "Unable to load procurement requests")
    }
  }, [])

  const loadDetail = useCallback(async (requestId: string) => {
    try {
      const [fresh, auditRows] = await Promise.all([
        api.get<any>(`/procurement-requests/${requestId}`),
        api.get<any[]>(`/audit-logs?request_id=${encodeURIComponent(requestId)}&limit=50`).catch(() => []),
      ])
      setDetail(fresh)
      setAudit(auditRows)
      setError(null)
    } catch (err: any) {
      setError(err?.message || "Unable to load this request")
    }
  }, [])

  useEffect(() => {
    loadRequests()
    const interval = setInterval(loadRequests, 8000)
    return () => clearInterval(interval)
  }, [loadRequests])

  useEffect(() => {
    if (!selectedId) {
      setDetail(null)
      setAudit([])
      return
    }
    loadDetail(selectedId)
    const interval = setInterval(() => loadDetail(selectedId), 3000)
    return () => clearInterval(interval)
  }, [selectedId, loadDetail])

  useEffect(() => {
    if (!selectedId) return
    const es = createEventSource(`/procurement-requests/${selectedId}/events`)
    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === "ping") return
        const agent = data.agent_name ? `${data.agent_name} ` : ""
        const message = data.output_summary || data.message || data.error || ""
        addLog(`${agent}${formatEventType(data.type)}${message ? ` — ${message}` : ""}`,
          data.type.includes("failed") ? "error" : data.type.includes("completed") ? "success" : "info")
        loadDetail(selectedId)
      } catch {
        // ignore malformed events
      }
    }
    es.onerror = () => es.close()
    return () => es.close()
  }, [selectedId, addLog, loadDetail])

  async function runDemo() {
    setBusy(true)
    setError(null)
    try {
      const created = await api.post<any>("/demo", {})
      addLog(`Demo request ${created.id} created — agents are starting`, "success")
      setSelectedId(created.id)
      await loadRequests()
      await loadDetail(created.id)
    } catch (err: any) {
      setError(err?.message || "Could not start the demo")
    } finally {
      setBusy(false)
    }
  }

  async function resumeWorkflow() {
    if (!selectedId) return
    setBusy(true)
    setError(null)
    try {
      await api.post(`/procurement-requests/${selectedId}/start`, {})
      addLog(`Workflow re-started for ${selectedId}`, "info")
      await loadDetail(selectedId)
    } catch (err: any) {
      setError(err?.message || "Could not start the workflow")
    } finally {
      setBusy(false)
    }
  }

  const executions: Record<string, any> = {}
  detail?.agent_executions?.forEach((exec: any) => {
    executions[exec.agent_name] = exec
  })

  const completed = AGENT_NAMES.filter((name) => executions[name]?.status === "completed").length
  const failed = AGENT_NAMES.filter((name) => executions[name]?.status === "failed").length
  const status = detail?.status || "no request"
  const running = status === "in_progress"
  const progress = Math.round((completed / AGENT_NAMES.length) * 100)

  const decision = detail?.decision
  const selectedRequest = requests.find((r) => r.id === selectedId)

  return (
    <DashboardLayout title="Agent Activity" breadcrumbs={["Agent Activity"]}>
      <div className="space-y-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Agent Activity</h1>
            <p className="text-muted-foreground">
              Watch each agent work in real time — what it is doing, what it produced and when.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary" className="flex items-center gap-1">
              <span className="h-2 w-2 animate-pulse rounded-full bg-green-500" />
              Live pipeline
            </Badge>
            {canRun && (
              <Button onClick={runDemo} disabled={busy} className="bg-primary hover:bg-primary/90">
                <Sparkles className="mr-2 h-4 w-4" />
                Run Demo
              </Button>
            )}
          </div>
        </div>

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        )}

        <Card>
          <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <CardTitle className="text-sm">Selected Request</CardTitle>
              <p className="mt-1 text-xs text-muted-foreground">
                Choose any request to replay its full agent activity.
              </p>
            </div>
            <select
              value={selectedId || ""}
              onChange={(event) => setSelectedId(event.target.value || null)}
              className="h-9 w-full rounded-md border border-border bg-background px-3 text-sm text-foreground sm:w-96"
            >
              {requests.length === 0 && <option value="">No requests yet</option>}
              {requests.map((request) => (
                <option key={request.id} value={request.id}>
                  {request.product_name} — {request.id} ({String(request.status).replace(/_/g, " ")})
                </option>
              ))}
            </select>
          </CardHeader>
          <CardContent>
            {selectedRequest ? (
              <div className="space-y-4">
                <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm">
                  <div>
                    <span className="text-muted-foreground">Request </span>
                    <span className="font-mono text-xs font-medium text-foreground">{selectedRequest.id}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Product </span>
                    <span className="font-medium text-foreground">{selectedRequest.product_name}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Budget </span>
                    <span className="font-medium text-foreground">{formatCurrency(selectedRequest.max_budget)}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Quantity </span>
                    <span className="font-medium text-foreground">{selectedRequest.quantity}</span>
                  </div>
                  <Badge variant={statusVariant(status)}>{String(status).replace(/_/g, " ")}</Badge>
                </div>

                <div>
                  <div className="mb-1 flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">
                      {completed} of {AGENT_NAMES.length} agents completed
                      {failed > 0 ? ` · ${failed} failed` : ""}
                    </span>
                    <span className="font-medium text-foreground">{progress}%</span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                    <div
                      className={cn(
                        "h-full rounded-full transition-all duration-500",
                        failed > 0 ? "bg-red-500" : running ? "bg-blue-500" : "bg-green-500"
                      )}
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                </div>

                {decision && (
                  <div className="rounded-lg border border-border bg-muted/40 p-3 text-sm">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge variant={decision.decision === "approve" ? "success" : "destructive"}>
                        Decision: {decision.decision}
                      </Badge>
                      <span className="font-medium text-foreground">{decision.recommended_vendor_name}</span>
                      <span className="text-muted-foreground">at {formatCurrency(decision.final_total_amount)}</span>
                      <span className="text-muted-foreground">· score {Number(decision.total_score).toFixed(1)}</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-muted-foreground">{decision.reasoning}</p>
                  </div>
                )}
              </div>
            ) : (
              <p className="py-4 text-sm text-muted-foreground">
                No procurement requests yet. Use Run Demo or create a request to see the agents work.
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Agent Pipeline Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="divide-y divide-border/60">
              {AGENT_NAMES.map((name, index) => {
                const exec = executions[name]
                const agentStatus = (exec?.status || "pending").toLowerCase()
                const agentRunning = running && exec?.status === "running"
                return (
                  <div key={name} className="flex items-start gap-3 py-3">
                    <div
                      className={cn(
                        "mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full border text-xs font-semibold",
                        agentStatus === "completed"
                          ? "border-green-200 bg-green-50 text-green-700"
                          : agentStatus === "failed"
                          ? "border-red-200 bg-red-50 text-red-700"
                          : agentRunning
                          ? "border-blue-200 bg-blue-50 text-blue-700"
                          : "border-border bg-muted text-muted-foreground"
                      )}
                    >
                      {agentStatus === "completed" ? (
                        <CheckCircle2 className="h-4 w-4" />
                      ) : agentStatus === "failed" ? (
                        <XCircle className="h-4 w-4" />
                      ) : agentRunning ? (
                        <RefreshCw className="h-4 w-4 animate-spin" />
                      ) : (
                        index + 1
                      )}
                    </div>

                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-foreground">{name}</span>
                          <Badge variant={getBadgeVariant(agentStatus)} className="text-[10px]">
                            {agentRunning ? "Working" : capitalize(agentStatus)}
                          </Badge>
                        </div>
                        <AgentTiming exec={exec} />
                      </div>
                      <p className="mt-1 text-xs leading-5 text-muted-foreground">
                        {exec?.output_summary
                          || (agentRunning
                            ? "Agent is working on this step..."
                            : agentStatus === "failed"
                            ? exec?.error_message || "Agent failed"
                            : "Waiting for its turn in the pipeline.")}
                      </p>
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm">
                <Activity className="h-4 w-4" />
                Live Event Stream
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-80 space-y-1 overflow-y-auto rounded-lg border border-border bg-slate-950 p-3 font-mono text-xs">
                {logs.length === 0 ? (
                  <div className="text-slate-400">
                    Waiting for agent events. Run the demo or start a request.
                  </div>
                ) : (
                  logs.map((log, index) => (
                    <div
                      key={`${log.time}-${index}`}
                      className={cn(
                        "rounded px-1 py-0.5",
                        log.kind === "success" && "text-emerald-400",
                        log.kind === "error" && "text-red-400",
                        log.kind === "info" && "text-slate-300"
                      )}
                    >
                      <span className="text-slate-500">[{log.time}]</span> {log.text}
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm">
                <Bot className="h-4 w-4" />
                Audit Trail
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-80 space-y-3 overflow-y-auto pr-1">
                {audit.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No audit events for this request yet.</p>
                ) : (
                  audit.map((event) => (
                    <div key={event.id} className="flex gap-3">
                      <div className="mt-1 h-2 w-2 shrink-0 rounded-full bg-blue-500" />
                      <div className="min-w-0">
                        <p className="text-sm text-foreground">{event.event_description}</p>
                        <p className="mt-0.5 text-[11px] text-muted-foreground">
                          {event.actor ? `${event.actor} · ` : ""}
                          {formatDateTime(event.created_at)}
                        </p>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Controls</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
            <Button
              onClick={resumeWorkflow}
              disabled={!canRun || running || !selectedId || busy}
              className="bg-primary hover:bg-primary/90"
            >
              <Play className="mr-2 h-4 w-4" />
              {running ? "Workflow Running..." : "Run / Resume Workflow"}
            </Button>
            <Button variant="outline" onClick={() => selectedId && loadDetail(selectedId)} disabled={!selectedId}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh Status
            </Button>
            {canCreate && !canRun && (
              <p className="self-center text-xs text-muted-foreground">
                Ask an officer or admin to run the pipeline. You can create requests from New Procurement.
              </p>
            )}
            {!canRun && user?.role === "auditor" && (
              <p className="self-center text-xs text-muted-foreground">
                Auditor mode: activity is read-only.
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}

function AgentTiming({ exec }: { exec: any }) {
  if (!exec) {
    return (
      <span className="flex items-center gap-1 text-[11px] text-muted-foreground">
        <Clock className="h-3 w-3" /> Not started
      </span>
    )
  }
  if (exec.status === "running" && exec.started_at) {
    return (
      <span className="flex items-center gap-1 text-[11px] text-blue-600">
        <RefreshCw className="h-3 w-3 animate-spin" /> Started {formatDateTime(exec.started_at)}
      </span>
    )
  }
  if (exec.completed_at) {
    const duration = durationSeconds(exec.started_at, exec.completed_at)
    return (
      <span className="flex items-center gap-1 text-[11px] text-muted-foreground">
        <Clock className="h-3 w-3" /> {duration}s · {formatDateTime(exec.completed_at)}
      </span>
    )
  }
  return (
    <span className="flex items-center gap-1 text-[11px] text-muted-foreground">
      <Clock className="h-3 w-3" /> {exec.started_at ? formatDateTime(exec.started_at) : "Not started"}
    </span>
  )
}

function formatEventType(type: string): string {
  return String(type || "event").replace(/_/g, " ")
}

function formatDateTime(value?: string): string {
  if (!value) return ""
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return value
  return parsed.toLocaleString()
}

function durationSeconds(start?: string, end?: string): string {
  if (!start || !end) return "0"
  const ms = new Date(end).getTime() - new Date(start).getTime()
  if (Number.isNaN(ms) || ms < 0) return "0"
  return (ms / 1000).toFixed(ms < 10000 ? 1 : 0)
}

function capitalize(value: string): string {
  return value ? value.charAt(0).toUpperCase() + value.slice(1) : value
}

function statusVariant(status: string): "default" | "secondary" | "destructive" | "outline" | "success" | "warning" | "pending" {
  switch (status) {
    case "completed": return "success"
    case "awaiting_approval": return "warning"
    case "in_progress": return "pending"
    case "failed":
    case "rejected": return "destructive"
    default: return "secondary"
  }
}

function getBadgeVariant(status: string): "default" | "secondary" | "destructive" | "outline" | "success" | "warning" | "pending" {
  switch (status.toLowerCase()) {
    case "completed": return "success"
    case "running": return "pending"
    case "failed": return "destructive"
    default: return "secondary"
  }
}
