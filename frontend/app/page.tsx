"use client"

import { useEffect, useState } from "react"
import DashboardLayout from "@/app/dashboard-layout"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/card"
import { Badge } from "@/components/badge"
import { BarChart, Bar, PieChart, Pie, Cell, ResponsiveContainer } from "recharts"
import {
  DollarSign,
  Clock,
  AlertCircle,
  CheckCircle,
  Activity,
  Plus,
} from "lucide-react"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { api } from "@/lib/api"
import { Button } from "@/components/button"

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"]

interface StatCard {
  label: string
  value: string
  delta: string
  icon: any
  color: string
}

interface SpendingPoint {
  name: string
  original: number
  revised: number
}

interface StatusPoint {
  name: string
  value: number
}

interface RecentRequest {
  id: string
  product_name: string
  category: string
  status: string
  max_budget: number
  created_at: string
}

export default function OverviewPage() {
  const [stats, setStats] = useState<StatCard[]>([
    { label: "Total Requests", value: "0", delta: "this month", icon: DollarSign, color: "text-blue-600" },
    { label: "In Progress", value: "0", delta: "active workflows", icon: Clock, color: "text-amber-600" },
    { label: "Pending Approvals", value: "0", delta: "awaiting review", icon: AlertCircle, color: "text-purple-600" },
    { label: "Negotiated Savings", value: "$0", delta: "realized savings", icon: CheckCircle, color: "text-green-600" },
  ])
  const [spendingData, setSpendingData] = useState<SpendingPoint[]>([])
  const [statusData, setStatusData] = useState<StatusPoint[]>([])
  const [recentRequests, setRecentRequests] = useState<RecentRequest[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDashboard()
  }, [])

  async function loadDashboard() {
    try {
      const [requests, approvals] = await Promise.all([
        api.get<any[]>("/procurement-requests?limit=100"),
        api.get<any[]>("/approvals"),
      ])

      const total = requests.length
      const inProgress = requests.filter((r) => r.status === "in_progress").length
      const pendingApprovals = approvals.filter((a) => a.status === "pending").length
      const completed = requests.filter((r) => r.status === "completed").length

      const negotiatedSavings = approvals.reduce(
        (sum, a) => sum + ((a.final_total_amount || 0) - (a.original_amount || 0)),
        0
      )

      setStats([
        { label: "Total Requests", value: String(total), delta: "this month", icon: DollarSign, color: "text-blue-600" },
        { label: "In Progress", value: String(inProgress), delta: "active workflows", icon: Clock, color: "text-amber-600" },
        { label: "Pending Approvals", value: String(pendingApprovals), delta: "awaiting review", icon: AlertCircle, color: "text-purple-600" },
        { label: "Negotiated Savings", value: `$${Math.abs(negotiatedSavings).toLocaleString()}`, delta: "realized savings", icon: CheckCircle, color: "text-green-600" },
      ])

      const categoryMap: Record<string, { original: number; revised: number }> = {}
      requests.forEach((r) => {
        if (!categoryMap[r.category]) {
          categoryMap[r.category] = { original: 0, revised: 0 }
        }
        categoryMap[r.category].original += r.max_budget
      })
      approvals.forEach((a) => {
        if (a.request_id && categoryMap[a.request_id]) {
          categoryMap[a.request_id].revised += a.final_total_amount || 0
        }
      })

      setSpendingData(
        Object.entries(categoryMap).map(([name, data]) => ({
          name,
          original: data.original,
          revised: data.revised,
        }))
      )

      setStatusData([
        { name: "Completed", value: completed },
        { name: "In Progress", value: inProgress },
        { name: "Pending Approval", value: pendingApprovals },
      ])

      const activities: RecentRequest[] = requests
        .sort((a: any, b: any) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
        .slice(0, 5)
      setRecentRequests(activities)
    } catch (err) {
      console.error("Failed to load dashboard:", err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <DashboardLayout title="Overview" breadcrumbs={["Overview"]}>
        <div className="flex h-full items-center justify-center">
          <div className="flex flex-col items-center gap-3">
            <div className="animate-pulse rounded-full h-12 w-12 border-b-2 border-primary"></div>
            <p className="text-sm text-muted-foreground">Loading dashboard...</p>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout title="Overview" breadcrumbs={["Overview"]}>
      <div className="space-y-8">
        {/* Page Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Overview</h1>
            <p className="text-muted-foreground">
              Monitor procurement activity, supplier performance, and cost savings.
            </p>
          </div>
          <Link href="/new-procurement">
            <Button className="px-5 py-2">
              <Plus className="w-4 h-4 mr-2" />
              New Procurement
            </Button>
          </Link>
        </div>

        {/* Metric Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          {stats.map((stat) => {
            const Icon = stat.icon
            return (
              <Card key={stat.label} className="overflow-hidden">
                <CardHeader className="pb-3 flex flex-row items-center justify-between">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    {stat.label}
                  </CardTitle>
                  <div className={cn("w-9 h-9 rounded-lg flex items-center justify-center", stat.color + "/10", stat.color)}>
                    <Icon className="w-5 h-5" />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-foreground">{stat.value}</div>
                  <p className="text-xs text-muted-foreground">{stat.delta}</p>
                </CardContent>
              </Card>
            )
          })}
        </div>

        {/* Charts Grid — 2 columns on desktop */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Spending Chart - Left Column */}
          <Card className="lg:col-span-2 overflow-hidden" style={{ minWidth: 0 }}>
            <CardHeader>
              <CardTitle className="text-sm font-semibold">Spending vs Savings</CardTitle>
              <CardDescription className="text-xs text-muted-foreground">
                Original vs negotiated vendor quotes by category
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div style={{ width: '100%', height: 288 }}>
                {spendingData.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-muted-foreground space-y-2">
                    <Activity className="w-10 h-10 opacity-20" />
                    <p className="text-sm">No spending data available</p>
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={spendingData}>
                      <Bar dataKey="original" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="revised" fill="#10b981" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Status Distribution */}
          <Card style={{ minWidth: 0 }}>
            <CardHeader>
              <CardTitle className="text-sm font-semibold">Request Status</CardTitle>
              <CardDescription className="text-xs text-muted-foreground">
                Distribution of procurement request statuses
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div style={{ width: '100%', height: 288 }}>
                {statusData.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-muted-foreground space-y-2">
                    <Activity className="w-10 h-10 opacity-20" />
                    <p className="text-sm">No status data available</p>
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={statusData}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        outerRadius={90}
                        fill="#8884d8"
                        label
                      >
                        {statusData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                    </PieChart>
                  </ResponsiveContainer>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Recent Requests — full-width below charts */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle className="text-sm font-semibold">Recent Requests</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-[11px] font-semibold text-muted-foreground uppercase">
                    <th className="pb-2 pr-4 font-medium">Request ID</th>
                    <th className="pb-2 pr-4 font-medium">Product</th>
                    <th className="pb-2 pr-4 font-medium">Category</th>
                    <th className="pb-2 pr-4 font-medium text-right">Budget</th>
                    <th className="pb-2 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {recentRequests.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="h-24 text-center text-muted-foreground">
                        No recent requests
                      </td>
                    </tr>
                  ) : (
                    recentRequests.map((req) => (
                      <tr key={req.id} className="border-b border-border/50 hover:bg-accent transition-colors">
                        <td className="py-3 pr-4 font-mono text-xs text-foreground">{req.id}</td>
                        <td className="py-3 pr-4 text-sm text-foreground">{req.product_name}</td>
                        <td className="py-3 pr-4 text-sm text-muted-foreground">{req.category}</td>
                        <td className="py-3 pr-4 text-sm text-right text-foreground">{formatCurrency(req.max_budget)}</td>
                        <td className="py-3">
                          <Badge variant={getBadgeVariant(req.status)} className="text-[10px]">
                            {req.status.charAt(0).toUpperCase() + req.status.slice(1)}
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
      </div>
    </DashboardLayout>
  )
}

function getBadgeVariant(status: string): "default" | "secondary" | "destructive" | "outline" | "success" | "warning" | "pending" {
  switch (status.toLowerCase()) {
    case "completed": return "success"
    case "in_progress": return "pending"
    case "pending": return "pending"
    case "rejected": return "destructive"
    case "failed": return "destructive"
    default: return "secondary"
  }
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value)
}