"use client"

import { useEffect, useState } from "react"
import DashboardLayout from "@/app/dashboard-layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/card"
import { Badge } from "@/components/badge"
import { MessageCircle, Clock, DollarSign, TrendingUp } from "lucide-react"
import { api } from "@/lib/api"
import { formatCurrency } from "@/lib/utils"

export default function NegotiationsPage() {
  const [negotiations, setNegotiations] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<any[]>("/negotiations")
      .then((rows) => {
        setNegotiations(rows)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <DashboardLayout title="Negotiations">
        <div className="flex h-full items-center justify-center">
          <div className="animate-pulse rounded-full h-10 w-10 border-b-2 border-primary"></div>
        </div>
      </DashboardLayout>
    )
  }

  const totalSavings = negotiations.reduce((sum, n) => sum + n.savings_achieved, 0)
  const successful = negotiations.filter((n) => n.success).length
  const avgRounds = negotiations.length ? negotiations.reduce((sum, n) => sum + n.rounds, 0) / negotiations.length : 0

  return (
    <DashboardLayout title="Negotiation Workspace" breadcrumbs={["Negotiations"]}>
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard title="Total Negotiations" value={negotiations.length} Icon={MessageCircle} />
          <StatCard title="Successful" value={successful} Icon={TrendingUp} />
          <StatCard title="Total Savings" value={formatCurrency(totalSavings)} Icon={DollarSign} />
          <StatCard title="Avg Rounds" value={avgRounds.toFixed(1)} Icon={Clock} />
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Negotiation History</CardTitle>
          </CardHeader>
          <CardContent>
            {negotiations.length === 0 ? (
              <div className="py-8 text-center text-muted-foreground">
                No negotiations recorded. Run a procurement workflow with negotiation enabled.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-left text-[11px] font-semibold text-muted-foreground uppercase">
                      <th className="pb-3">Request</th>
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
                    {negotiations.map((n) => (
                      <tr key={n.id} className="border-b border-border/50 hover:bg-accent/50 transition-colors">
                        <td className="py-3 text-xs text-foreground">
                          <div className="font-medium">{n.product_name}</div>
                          <div className="mt-0.5 font-mono text-[10px] text-muted-foreground">{n.request_id}</div>
                        </td>
                        <td className="py-3 text-sm text-foreground">{n.vendor_name}</td>
                        <td className="py-3 text-right text-sm text-foreground">{formatCurrency(n.final_total_amount + n.savings_achieved)}</td>
                        <td className="py-3 text-right text-sm text-foreground">{formatCurrency(n.final_total_amount)}</td>
                        <td className="py-3 text-center">{n.rounds}</td>
                        <td className="py-3 text-right text-sm text-foreground">{(Number(n.final_discount_percent) * 100).toFixed(1)}%</td>
                        <td className="py-3 text-right text-sm text-foreground">-{formatCurrency(n.savings_achieved)}</td>
                        <td className="py-3">
                          <Badge variant={n.success ? "success" : "secondary"} className="text-[10px]">
                            {n.success ? "Success" : "No concession"}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}

function StatCard({ title, value, Icon }: { title: string; value: string | number; Icon: any }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm text-muted-foreground">{title}</CardTitle>
        <Icon className="w-5 h-5 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold text-foreground">{value}</div>
      </CardContent>
    </Card>
  )
}