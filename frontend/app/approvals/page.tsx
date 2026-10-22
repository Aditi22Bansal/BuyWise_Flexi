"use client"

import { useEffect, useState } from "react"
import DashboardLayout from "@/app/dashboard-layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/card"
import { Badge } from "@/components/badge"
import { Button } from "@/components/button"
import { CheckCircle2, AlertCircle, User, Clock, MessageCircle } from "lucide-react"
import { api } from "@/lib/api"
import { useAuth } from "@/lib/auth"
import { formatCurrency, formatDateTime } from "@/lib/utils"

export default function ApprovalsPage() {
  const { user } = useAuth()
  const [approvals, setApprovals] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<any[]>("/approvals")
      .then(setApprovals)
      .catch(() => setApprovals([]))
      .finally(() => setLoading(false))
  }, [])

  const canDecide = user?.role === "admin" || user?.role === "approver"

  function withinLimit(amount: number): boolean {
    if (user?.role !== "approver") return true
    return amount <= (user.approval_limit || 0)
  }

  async function handleAction(requestId: string, decision: "approve" | "reject") {
    const reviewerName = user?.name || user?.username || "Reviewer"

    try {
      if (decision === "approve") {
        await api.post(`/approvals/${requestId}/approve`, { decision, reviewer_name: reviewerName })
      } else {
        await api.post(`/approvals/${requestId}/reject`, { decision, reviewer_name: reviewerName })
      }
      setApprovals(approvals.map((a) =>
        a.request_id === requestId ? { ...a, status: decision === "approve" ? "approved" : "rejected" } : a
      ))
      setTimeout(() => window.location.reload(), 500)
    } catch (err: any) {
      alert(err?.message || "Action failed")
    }
  }

  if (loading) {
    return (
      <DashboardLayout title="Approvals">
        <div className="flex h-full items-center justify-center">
          <div className="animate-pulse rounded-full h-10 w-10 border-b-2 border-primary"></div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout title="Human Approval Center" breadcrumbs={["Approvals"]}>
      <div className="space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Human Approval Center</h1>
            <p className="text-muted-foreground">
              Review and approve procurement recommendations before commitment.
            </p>
          </div>
          <Badge variant="secondary">
            {approvals.filter((a) => a.status === "pending").length} Pending
          </Badge>
        </div>

        {approvals.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <CheckCircle2 className="w-12 h-12 text-muted-foreground mb-3" />
            <p className="text-muted-foreground">No pending approvals.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-[11px] font-semibold text-muted-foreground uppercase">
                  <th className="pb-3">Request</th>
                  <th className="pb-3">Product</th>
                  <th className="pb-3 text-right">Recommended Amount</th>
                  <th className="pb-3 text-center">Score</th>
                  <th className="pb-3">Status</th>
                  <th className="pb-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody>
                {approvals.map((a) => (
                  <tr key={a.id} className="border-b border-border/50 hover:bg-accent/50 transition-colors">
                    <td className="py-3 font-mono text-xs text-foreground">{a.request_id}</td>
                    <td className="py-3 text-sm text-foreground">{a.product_name || "—"}</td>
                    <td className="py-3 text-right text-sm text-foreground">{formatCurrency(a.final_total_amount || 0)}</td>
                    <td className="py-3 text-center">{a.total_score?.toFixed(2) || "—"}</td>
                    <td className="py-3">
                      <Badge variant={a.status === "pending" ? "pending" : a.status === "approved" ? "success" : "destructive"} className="text-[10px]">
                        {a.status.charAt(0).toUpperCase() + a.status.slice(1)}
                      </Badge>
                    </td>
                    <td className="py-3 text-right">
                      {a.status === "pending" && canDecide ? (
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="default"
                            size="sm"
                            disabled={!withinLimit(a.final_total_amount || 0)}
                            title={
                              withinLimit(a.final_total_amount || 0)
                                ? "Approve this request"
                                : `Exceeds your approval limit of ${formatCurrency(user?.approval_limit || 0)}`
                            }
                            onClick={() => handleAction(a.request_id, "approve")}
                          >
                            Approve
                          </Button>
                          <Button variant="destructive" size="sm" onClick={() => handleAction(a.request_id, "reject")}>
                            Reject
                          </Button>
                        </div>
                      ) : a.status === "pending" ? (
                        <span className="text-xs text-muted-foreground">
                          {user?.role === "auditor" ? "Read-only" : "Awaiting approver"}
                        </span>
                      ) : (
                        <span className="text-xs text-muted-foreground">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}