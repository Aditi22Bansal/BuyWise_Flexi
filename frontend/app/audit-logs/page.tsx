"use client"

import { useEffect, useState } from "react"
import DashboardLayout from "@/app/dashboard-layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/card"
import { api } from "@/lib/api"
import { formatDateTime } from "@/lib/utils"
import { FileText } from "lucide-react"

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<any[]>("/audit-logs?limit=100")
      .then(setLogs)
      .catch(() => setLogs([]))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <DashboardLayout title="Audit Logs">
        <div className="flex h-full items-center justify-center">
          <div className="animate-pulse rounded-full h-10 w-10 border-b-2 border-primary"></div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout title="Audit Logs" breadcrumbs={["Audit Logs"]}>
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">System Audit Trail</CardTitle>
        </CardHeader>
        <CardContent>
          {logs.length === 0 ? (
            <div className="py-8 text-center text-muted-foreground">
              <FileText className="w-8 h-8 mx-auto mb-2 text-muted-foreground" />
              <p>No audit events recorded yet.</p>
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
                    <th className="pb-3">Request ID</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log) => (
                    <tr key={log.id} className="border-b border-border/50 hover:bg-accent/50 transition-colors">
                      <td className="py-3 text-muted-foreground text-xs font-mono">{formatDateTime(log.created_at)}</td>
                      <td className="py-3 text-xs font-medium text-foreground">{log.event_type}</td>
                      <td className="py-3 text-sm text-foreground">{log.event_description}</td>
                      <td className="py-3 text-xs text-muted-foreground">{log.actor || "system"}</td>
                      <td className="py-3 text-xs font-mono text-muted-foreground">{log.request_id || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </DashboardLayout>
  )
}