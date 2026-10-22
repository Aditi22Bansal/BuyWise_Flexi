"use client"

import { useEffect, useState } from "react"
import DashboardLayout from "@/app/dashboard-layout"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/card"
import { Badge } from "@/components/badge"
import { api } from "@/lib/api"
import { formatCurrency } from "@/lib/utils"

export default function VendorComparisonPage() {
  const [comparisons, setComparisons] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<any[]>("/vendor-comparisons")
      .then((rows) => {
        setComparisons(rows)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <DashboardLayout title="Vendor Comparison">
        <div className="flex h-full items-center justify-center">
          <div className="animate-pulse rounded-full h-10 w-10 border-b-2 border-primary"></div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout title="Vendor Comparison" breadcrumbs={["Vendor Comparison"]}>
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Vendor Comparison & Evaluation Scores</CardTitle>
        </CardHeader>
        <CardContent>
          {comparisons.length === 0 ? (
            <div className="py-8 text-center text-muted-foreground">
              No vendor comparison data available. Submit a procurement request to generate comparisons.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-[11px] font-semibold text-muted-foreground uppercase">
                    <th className="pb-3">Request</th>
                    <th className="pb-3">Vendor</th>
                    <th className="pb-3 text-right">Total Cost</th>
                    <th className="pb-3 text-center">Score</th>
                    <th className="pb-3">Savings vs Budget</th>
                    <th className="pb-3">Discount</th>
                    <th className="pb-3">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {comparisons.map((c) => (
                    <tr key={c.evaluation_id} className="border-b border-border/50 hover:bg-accent/50 transition-colors">
                      <td className="py-3 text-xs text-foreground">
                        <div className="font-medium">{c.product_name}</div>
                        <div className="mt-0.5 font-mono text-[10px] text-muted-foreground">{c.request_id}</div>
                      </td>
                      <td className="py-3 text-sm text-foreground">{c.vendor_name}</td>
                      <td className="py-3 text-right text-sm text-foreground">{formatCurrency(c.total_amount)}</td>
                      <td className="py-3 text-center font-bold text-sm">{Number(c.total_score).toFixed(1)}</td>
                      <td className="py-3 text-sm text-foreground">{c.savings_vs_budget >= 0 ? "+" : ""}{formatCurrency(c.savings_vs_budget)}</td>
                      <td className="py-3 text-right text-sm text-foreground">{(Number(c.discount_percent) * 100).toFixed(1)}%</td>
                      <td className="py-3">
                        <Badge variant={c.is_revised ? "success" : "secondary"} className="text-[10px]">
                          {c.is_revised ? `Negotiated r${c.negotiation_round}` : "Initial"}
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
    </DashboardLayout>
  )
}