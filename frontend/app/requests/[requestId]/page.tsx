"use client"

import { useParams, useRouter } from "next/navigation"
import { useEffect, useState, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/card"
import { Badge } from "@/components/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/button"
import DashboardLayout from "@/app/dashboard-layout"
import { api, createEventSource } from "@/lib/api"
import { useAuth } from "@/lib/auth"
import { formatCurrency, formatDate, formatDateTime, getStatusColor, cn } from "@/lib/utils"
import { toast } from "sonner"
import {
  ChevronRight,
  Clock,
  CheckCircle,
  AlertCircle,
  DollarSign,
  Truck,
  Shield,
  Users,
  MessageCircle,
  RefreshCw,
  Play,
} from "lucide-react"

export default function RequestDetailsPage() {
  const params = useParams()
  const router = useRouter()
  const { user } = useAuth()
  const requestId = params.requestId as string
  const [request, setRequest] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [workflowStatus, setWorkflowStatus] = useState<any>(null)
  const [eventSource, setEventSource] = useState<EventSource | null>(null)
  const [startingPipeline, setStartingPipeline] = useState(false)

  const canStartPipeline = user && ["admin", "officer"].includes(user.role)

  async function handleStartPipeline() {
    setStartingPipeline(true)
    try {
      await api.post(`/procurement-requests/${requestId}/start`, {})
      toast.success("Pipeline started", { description: "All 8 agents will now execute sequentially." })
      fetchRequest()
      fetchWorkflowStatus()
    } catch (err: any) {
      toast.error("Failed to start pipeline", { description: err?.message })
    } finally {
      setStartingPipeline(false)
    }
  }

  useEffect(() => {
    if (!requestId) return
    fetchRequest()
  }, [requestId])

  useEffect(() => {
    if (!requestId) return
    const es = createEventSource(`/procurement-requests/${requestId}/events`)
    setEventSource(es)

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === "agent_started" || data.type === "agent_completed" || data.type === "agent_failed" || data.type === "workflow_completed" || data.type === "workflow_failed") {
          fetchRequest()
          fetchWorkflowStatus()
        }
      } catch {}
    }

    es.onerror = () => es.close()
    return () => es.close()
  }, [requestId])

  const fetchRequest = useCallback(async () => {
    if (!requestId) return
    try {
      const data = await api.get<any>(`/procurement-requests/${requestId}`)
      setRequest(data)
      setLoading(false)
    } catch (err) {
      console.error(err)
      setLoading(false)
    }
  }, [requestId])

  const fetchWorkflowStatus = useCallback(async () => {
    if (!requestId) return
    try {
      const data = await api.get<any>(`/procurement-requests/${requestId}/status`)
      setWorkflowStatus(data)
    } catch {
      // workflow may not have started yet
    }
  }, [requestId])

  useEffect(() => {
    fetchWorkflowStatus()
  }, [fetchWorkflowStatus])

  if (loading) {
    return (
      <DashboardLayout title="Request Details">
        <div className="flex h-full items-center justify-center">
          <div className="animate-pulse rounded-full h-10 w-10 border-b-2 border-primary"></div>
        </div>
      </DashboardLayout>
    )
  }

  if (!request) {
    return (
      <DashboardLayout title="Request Details">
        <div className="flex h-full items-center justify-center">
          <p className="text-muted-foreground">Request not found.</p>
        </div>
      </DashboardLayout>
    )
  }

  const isRunning = workflowStatus?.status === "running" || request.status === "in_progress"

  return (
    <DashboardLayout title={`Request ${request.id}`} breadcrumbs={["Requests", request.id]}>
      <div className="flex flex-col gap-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Request {request.id}</h1>
            <p className="text-muted-foreground">
              {request.product_name} • {request.category}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={getBadgeVariant(request.status)}>
              {request.status.charAt(0).toUpperCase() + request.status.slice(1)}
            </Badge>
            <Badge variant={isRunning ? "pending" : "outline"}>
              {isRunning ? "Running" : request.current_stage || "Not started"}
            </Badge>
            {canStartPipeline && request.status === "pending" && (
              <Button
                size="sm"
                onClick={handleStartPipeline}
                disabled={startingPipeline}
              >
                <Play className="w-4 h-4 mr-2" />
                {startingPipeline ? "Starting..." : "Start Pipeline"}
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                fetchRequest()
                fetchWorkflowStatus()
              }}
              disabled={isRunning}
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard title="Product" value={request.product_name} />
          <StatCard title="Category" value={request.category} />
          <StatCard title="Quantity" value={String(request.quantity)} />
          <StatCard title="Budget" value={formatCurrency(request.max_budget)} />
        </div>

        <Tabs defaultValue="overview">
          <TabsList className="w-full">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="requirements">Requirements</TabsTrigger>
            <TabsTrigger value="products">Products</TabsTrigger>
            <TabsTrigger value="vendors">Vendors</TabsTrigger>
            <TabsTrigger value="comparison">Quote Comparison</TabsTrigger>
            <TabsTrigger value="agents">Agent Execution</TabsTrigger>
            <TabsTrigger value="negotiations">Negotiation History</TabsTrigger>
            <TabsTrigger value="recommendation">Final Recommendation</TabsTrigger>
            <TabsTrigger value="approvals">Approval History</TabsTrigger>
            <TabsTrigger value="audit">Audit Trail</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Request Information</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <InfoRow label="Created" value={formatDateTime(request.created_at)} />
                  <InfoRow label="Last Updated" value={formatDateTime(request.updated_at || request.created_at)} />
                  <InfoRow label="Status" value={request.status} />
                  <InfoRow label="Current Stage" value={request.current_stage || "—"} />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Timeline</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <TimelineItem
                      title="Request Submitted"
                      time={formatDateTime(request.created_at)}
                      status="completed"
                    />
                    <TimelineItem
                      title="Agent Orchestration"
                      time={request.current_stage ? formatDateTime(request.updated_at || request.created_at) : "Pending"}
                      status={request.status === "completed" || request.status === "awaiting_approval" ? "completed" : request.status === "in_progress" ? "running" : "pending"}
                    />
                    {(request.status === "completed" || request.status === "awaiting_approval") && (
                      <TimelineItem
                        title={request.status === "awaiting_approval" ? "Awaiting Human Approval" : "Workflow Completed"}
                        time={formatDateTime(request.completed_at || request.updated_at || request.created_at)}
                        status={request.status === "awaiting_approval" ? "pending" : "completed"}
                      />
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="requirements">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Procurement Requirements</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <InfoRow label="Product Name" value={request.product_name} />
                <InfoRow label="Category" value={request.category} />
                <InfoRow label="Description" value={request.description || "—"} />
                <InfoRow label="Quantity" value={String(request.quantity)} />
                <InfoRow label="Max Budget" value={formatCurrency(request.max_budget)} />
                <InfoRow label="Currency" value={request.currency || "USD"} />
                <InfoRow label="Warranty (Months)" value={String(request.warranty_months)} />
                <InfoRow label="Required Features" value={Array.isArray(request.required_features) ? request.required_features.join(", ") : request.required_features || "—"} />
                <InfoRow label="Delivery Needed By" value={request.delivery_needed_by || "—"} />
                <InfoRow label="Preferred Vendors" value={Array.isArray(request.preferred_vendors) ? request.preferred_vendors.join(", ") : request.preferred_vendors || "—"} />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="products">
            <DataTable
              title="Product Candidates"
              columns={["Product", "Category", "Base Price", "Quality", "Reviews", "Warranty", "Manufacturer"]}
              rows={(request.products || []).map((p: any) => [
                p.name,
                p.category,
                formatCurrency(p.base_price),
                String(p.quality_score),
                String(p.review_score),
                p.warranty_months + " months",
                p.manufacturer,
              ])}
            />
          </TabsContent>

          <TabsContent value="vendors">
            <DataTable
              title="Identified Vendors"
              columns={["Vendor", "Reliability", "Delivery (Days)", "Payment Terms", "Contact"]}
              rows={(request.vendors || []).map((v: any) => [
                v.name,
                String(v.reliability_score),
                String(v.average_delivery_days),
                v.payment_terms,
                v.contact_email,
              ])}
            />
          </TabsContent>

          <TabsContent value="comparison">
            <ComparisonTab requestId={requestId} />
          </TabsContent>

          <TabsContent value="agents">
            <AgentExecutionTab requestId={requestId} workflowStatus={workflowStatus} />
          </TabsContent>

          <TabsContent value="negotiations">
            <NegotiationTab requestId={requestId} />
          </TabsContent>

          <TabsContent value="recommendation">
            <RecommendationTab requestId={requestId} decision={request.decision} />
          </TabsContent>

          <TabsContent value="approvals">
            <ApprovalsTab requestId={requestId} />
          </TabsContent>

          <TabsContent value="audit">
            <AuditTab requestId={requestId} />
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  )
}

function StatCard({ title, value }: { title: string; value: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm text-muted-foreground">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-lg font-bold text-foreground">{value}</div>
      </CardContent>
    </Card>
  )
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className="text-foreground">{value}</span>
    </div>
  )
}

function TimelineItem({ title, time, status }: { title: string; time: string; status: string }) {
  return (
    <div className="flex items-start gap-3">
      <div className={cn("w-2 h-2 rounded-full shrink-0 mt-2", getStatusColor(status))} />
      <div>
        <p className="text-sm font-medium text-foreground">{title}</p>
        <p className="text-xs text-muted-foreground">{time}</p>
      </div>
    </div>
  )
}

function DataTable({ title, columns, rows }: { title: string; columns: string[]; rows: any[][] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-[11px] font-semibold text-muted-foreground uppercase">
                {columns.map((col) => (
                  <th key={col} className="pb-3 font-medium">
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 ? (
                <tr>
                  <td colSpan={columns.length} className="py-8 text-center text-muted-foreground">
                    No data available
                  </td>
                </tr>
              ) : (
                rows.map((row, i) => (
                  <tr key={i} className="border-b border-border/50 hover:bg-accent/50 transition-colors">
                    {row.map((cell, j) => (
                      <td key={j} className="py-3 text-sm text-foreground">
                        {cell}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}

function ComparisonTab({ requestId }: { requestId: string }) {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<any>(`/procurement-requests/${requestId}/comparison`)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false))
  }, [requestId])

  if (loading) return <div className="h-64 flex items-center justify-center">Loading...</div>
  if (!data) return <div>No comparison data available.</div>

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Vendor Comparison & Evaluation</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-[11px] font-semibold text-muted-foreground uppercase">
                <th className="pb-3">Vendor</th>
                <th className="pb-3 text-right">Total Cost</th>
                <th className="pb-3 text-center">Score</th>
                <th className="pb-3">Savings vs Budget</th>
                <th className="pb-3">Negotiation</th>
                <th className="pb-3 text-right">Discount</th>
              </tr>
            </thead>
            <tbody>
              {data.comparison.map((c: any) => (
                <tr key={c.vendor_id} className="border-b border-border/50 hover:bg-accent/50 transition-colors">
                  <td className="py-3 font-medium text-foreground">{c.vendor_name}</td>
                  <td className="py-3 text-right text-foreground">{formatCurrency(c.total_amount)}</td>
                  <td className="py-3 text-center font-bold">{c.total_score}</td>
                  <td className="py-3 text-foreground">{c.savings_vs_budget >= 0 ? "+" : ""}{formatCurrency(c.savings_vs_budget)}</td>
                  <td className="py-3">
                    <Badge variant={c.success ? "success" : "secondary"}>
                      {c.success ? "Completed" : "N/A"}
                    </Badge>
                  </td>
                  <td className="py-3 text-right text-foreground">{c.discount_percent * 100}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-4">
          <p className="text-xs text-muted-foreground mb-2">Scoring Criteria Weights:</p>
          <div className="flex gap-4 text-xs text-muted-foreground">
            {Object.entries(data.criteria_weights || {}).map(([key, weight]) => (
              <span key={key} className="flex items-center gap-1">
                {key}: {(Number(weight) * 100).toFixed(0)}%
              </span>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function AgentExecutionTab({ requestId, workflowStatus }: { requestId: string; workflowStatus: any }) {
  const [executions, setExecutions] = useState<any[]>([])

  useEffect(() => {
    api.get<any>(`/procurement-requests/${requestId}`).then((req: any) => {
      setExecutions(req.agent_executions || [])
    }).catch(() => setExecutions([]))
  }, [requestId, workflowStatus?.status, workflowStatus?.progress])

  const agentOrder = [
    "Product Research Agent",
    "Vendor Research Agent",
    "Review & Quality Agent",
    "Comparison Agent",
    "Decision Agent",
    "Negotiation Agent",
    "Re-evaluation Agent",
    "Approval Agent",
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Agent Execution Pipeline</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {agentOrder.map((name, i) => {
            const exec = executions.find((e) => e.agent_name === name)
            const status = exec?.status || "pending"
            const running = workflowStatus?.current_agent === name && workflowStatus?.status === "running"
            return (
              <div key={name} className="flex items-center justify-between py-3 border-b border-border/50 last:border-0">
                <div className="flex items-center gap-3">
                  <div className={cn("w-2 h-2 rounded-full shrink-0", running ? "bg-blue-500 animate-pulse" : getStatusColor(status))} />
                  <span className="text-sm font-medium text-foreground">{name}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={getBadgeVariant(status)} className="text-[10px]">
                    {status.charAt(0).toUpperCase() + status.slice(1)}
                  </Badge>
                  {exec?.output_summary && (
                    <span className="text-xs text-muted-foreground">{exec.output_summary}</span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}

function NegotiationTab({ requestId }: { requestId: string }) {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<any[]>(`/procurement-requests/${requestId}/negotiations`)
      .then(setData)
      .catch(() => setData([]))
      .finally(() => setLoading(false))
  }, [requestId])

  if (loading) return <div className="h-64 flex items-center justify-center">Loading...</div>

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Negotiation History</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-[11px] font-semibold text-muted-foreground uppercase">
                <th className="pb-3">Vendor</th>
                <th className="pb-3 text-right">Original</th>
                <th className="pb-3 text-right">Revised</th>
                <th className="pb-3 text-center">Rounds</th>
                <th className="pb-3 text-right">Discount</th>
                <th className="pb-3 text-right">Savings</th>
                <th className="pb-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {data.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-muted-foreground">
                    No negotiations recorded.
                  </td>
                </tr>
              ) : (
                data.map((n) => (
                  <tr key={n.id} className="border-b border-border/50 hover:bg-accent/50 transition-colors">
                    <td className="py-3 font-medium text-foreground">{n.vendor_name}</td>
                    <td className="py-3 text-right text-foreground">{formatCurrency(n.final_total_amount + n.savings_achieved)}</td>
                    <td className="py-3 text-right text-foreground">{formatCurrency(n.final_total_amount)}</td>
                    <td className="py-3 text-center">{n.rounds}</td>
                    <td className="py-3 text-right text-foreground">{n.final_discount_percent * 100}%</td>
                    <td className="py-3 text-right text-foreground">-{formatCurrency(n.savings_achieved)}</td>
                    <td className="py-3">
                      <Badge variant={n.success ? "success" : "secondary"}>
                        {n.success ? "Success" : "No concession"}
                      </Badge>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}

function RecommendationTab({ requestId, decision }: { requestId: string; decision: any }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Final Recommendation</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex items-center justify-between py-4 border-b border-border">
            <div>
              <div className="text-sm font-medium text-muted-foreground">Recommended Vendor</div>
              <div className="text-lg font-bold text-foreground">{decision?.recommended_vendor_name || "—"}</div>
            </div>
            <Badge
              variant={
                decision?.decision === "approve"
                  ? "success"
                  : decision?.decision === "reject"
                  ? "destructive"
                  : decision?.decision
                  ? "pending"
                  : "secondary"
              }
            >
              {decision?.decision ? decision.decision.charAt(0).toUpperCase() + decision.decision.slice(1) : "Awaiting workflow"}
            </Badge>
          </div>
          <div className="flex items-center justify-between py-4 border-b border-border">
            <div>
              <div className="text-sm font-medium text-muted-foreground">Final Total Amount</div>
              <div className="text-lg font-bold text-foreground">{decision?.final_total_amount ? formatCurrency(decision.final_total_amount) : "—"}</div>
            </div>
            <div className="text-right">
              <div className="text-sm font-medium text-muted-foreground">Score</div>
              <div className="text-lg font-bold text-foreground">{decision?.total_score != null ? decision.total_score.toFixed(2) : "—"}</div>
            </div>
          </div>
          {decision?.reasoning && (
            <div className="py-4 text-sm text-muted-foreground">{decision.reasoning}</div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

function ApprovalStatusCard({ requestId }: { requestId: string }) {
  const [approval, setApproval] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<any>(`/approvals/${requestId}`)
      .then(setApproval)
      .catch(() => setApproval(null))
      .finally(() => setLoading(false))
  }, [requestId])

  if (loading) return <div className="h-64 flex items-center justify-center">Loading...</div>
  if (!approval) {
    return (
      <div className="py-8 text-center text-muted-foreground">
        No approval record yet. Workflow must complete first.
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <Badge
        variant={approval.status === "pending" ? "pending" : approval.status === "approved" ? "success" : "destructive"}
      >
        {approval.status.charAt(0).toUpperCase() + approval.status.slice(1)}
      </Badge>
      <InfoRow label="Reviewer" value={approval.reviewer_name || "—"} />
      <InfoRow label="Reason" value={approval.reason || "—"} />
      <InfoRow label="Decided At" value={approval.decided_at ? formatDateTime(approval.decided_at) : "—"} />
    </div>
  )
}

function ApprovalsTab({ requestId }: { requestId: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Approval History</CardTitle>
      </CardHeader>
      <CardContent>
        <ApprovalStatusCard requestId={requestId} />
      </CardContent>
    </Card>
  )
}

function AuditTab({ requestId }: { requestId: string }) {
  const [logs, setLogs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<any[]>(`/audit-logs?request_id=${requestId}&limit=50`)
      .then(setLogs)
      .catch(() => setLogs([]))
      .finally(() => setLoading(false))
  }, [requestId])

  if (loading) return <div className="h-64 flex items-center justify-center">Loading...</div>

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Audit Trail</CardTitle>
      </CardHeader>
      <CardContent>
        {logs.length === 0 ? (
          <div className="py-8 text-center text-muted-foreground">
            No audit events yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-[11px] font-semibold text-muted-foreground uppercase">
                  <th className="pb-3">Timestamp</th>
                  <th className="pb-3">Event Type</th>
                  <th className="pb-3">Description</th>
                  <th className="pb-3">Actor</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id} className="border-b border-border/50 hover:bg-accent/50 transition-colors">
                    <td className="py-3 text-muted-foreground text-xs font-mono">{formatDateTime(log.created_at)}</td>
                    <td className="py-3 text-xs font-medium text-foreground">{log.event_type}</td>
                    <td className="py-3 text-sm text-foreground">{log.event_description}</td>
                    <td className="py-3 text-xs text-muted-foreground">{log.actor || "system"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function getBadgeVariant(status: string): "default" | "secondary" | "destructive" | "outline" | "success" | "warning" | "pending" {
  switch (status.toLowerCase()) {
      case "completed": return "success"
      case "in_progress": return "pending"
      case "awaiting_approval": return "pending"
      case "pending": return "pending"
    case "rejected": return "destructive"
    case "failed": return "destructive"
    default: return "secondary"
  }
}