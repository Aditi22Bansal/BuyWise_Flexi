"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/card"
import { Badge } from "@/components/badge"
import { Button } from "@/components/button"
import { Input } from "@/components/ui/input"
import DashboardLayout from "@/app/dashboard-layout"
import { Search, Plus } from "lucide-react"
import { api } from "@/lib/api"
import { formatCurrency, formatDate } from "@/lib/utils"

interface RequestItem {
  id: string
  product_name: string
  category: string
  quantity: number
  max_budget: number
  status: string
  current_stage: string | null
  created_at: string
}

export default function RequestsPage() {
  const router = useRouter()
  const [requests, setRequests] = useState<RequestItem[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")

  useEffect(() => {
    fetchRequests()
  }, [])

  async function fetchRequests() {
    try {
      const data = await api.get<RequestItem[]>(`/procurement-requests?limit=100`)
      setRequests(data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const filtered = requests.filter(
    (r) =>
      r.product_name.toLowerCase().includes(search.toLowerCase()) ||
      r.id.toLowerCase().includes(search.toLowerCase()) ||
      r.category.toLowerCase().includes(search.toLowerCase())
  )

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

  return (
    <DashboardLayout title="Procurement Requests" breadcrumbs={["Requests"]}>
      <div className="flex flex-col gap-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Procurement Requests</h1>
            <p className="text-muted-foreground">
              View and manage all procurement requests across your organization.
            </p>
          </div>
          <Button onClick={() => router.push("/new-procurement")} className="bg-primary hover:bg-primary/90">
            <Plus className="w-4 h-4 mr-2" />
            New Request
          </Button>
        </div>

        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center gap-2">
              <Search className="w-4 h-4" />
              <Input
                placeholder="Search by request ID, product name, or category..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full md:w-80"
              />
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-[11px] font-semibold text-muted-foreground uppercase">
                    <th className="pb-3 font-medium">Request ID</th>
                    <th className="pb-3 font-medium">Product</th>
                    <th className="pb-3 font-medium">Category</th>
                    <th className="pb-3 font-medium">Quantity</th>
                    <th className="pb-3 font-medium">Budget</th>
                    <th className="pb-3 font-medium">Status</th>
                    <th className="pb-3 font-medium">Created</th>
                    <th className="pb-3 font-medium text-right">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan={8} className="py-8 text-center text-muted-foreground">
                        Loading requests...
                      </td>
                    </tr>
                  ) : filtered.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="py-8 text-center text-muted-foreground">
                        No requests found.
                      </td>
                    </tr>
                  ) : (
                    filtered.map((req) => (
                      <tr
                        key={req.id}
                        onClick={() => router.push(`/requests/${req.id}`)}
                        className="cursor-pointer hover:bg-accent/50 transition-colors border-b border-border/50"
                      >
                        <td className="py-3 font-mono text-xs text-foreground">{req.id}</td>
                        <td className="py-3 text-sm text-foreground">{req.product_name}</td>
                        <td className="py-3 text-sm text-muted-foreground">{req.category}</td>
                        <td className="py-3 text-sm text-foreground">{req.quantity}</td>
                        <td className="py-3 text-sm text-right text-foreground">{formatCurrency(req.max_budget)}</td>
                        <td className="py-3">
                          <Badge variant={getBadgeVariant(req.status)} className="text-[10px]">
                            {req.status.charAt(0).toUpperCase() + req.status.slice(1)}
                          </Badge>
                        </td>
                        <td className="py-3 text-sm text-muted-foreground">{formatDate(req.created_at)}</td>
                        <td className="py-3 text-right">
                          <Button variant="ghost" size="sm" onClick={(e) => {
                            e.stopPropagation()
                            router.push(`/requests/${req.id}`)
                          }}>
                            View
                          </Button>
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