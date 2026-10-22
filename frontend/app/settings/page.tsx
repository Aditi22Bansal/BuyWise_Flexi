"use client"

import { useEffect, useState } from "react"
import DashboardLayout from "@/app/dashboard-layout"
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/card"
import { Button } from "@/components/button"
import { api } from "@/lib/api"
import { SlidersHorizontal, AlertTriangle, Save } from "lucide-react"
import { toast } from "sonner"

export default function SettingsPage() {
  const [weights, setWeights] = useState<Record<string, number>>({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    api.get<{ weights: Record<string, number> }>("/settings/evaluation-weights").then((data) => {
      setWeights(data.weights)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  const total = Object.values(weights).reduce((sum, w) => sum + w, 0)

  async function handleSave() {
    setSaving(true)
    try {
      await api.put("/settings/evaluation-weights", { weights })
      toast.success("Evaluation weights saved")
    } catch (err: any) {
      toast.error("Failed to save weights: " + (err?.message || "Unknown error"))
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <DashboardLayout title="Evaluation Settings">
        <div className="flex h-full items-center justify-center">
          <div className="animate-pulse rounded-full h-10 w-10 border-b-2 border-primary"></div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout title="Evaluation Settings" breadcrumbs={["Settings"]}>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Evaluation Criteria Weights</h1>
          <p className="text-muted-foreground">
            Configure how procurement criteria are weighted in vendor scoring.
            Weights must sum to 100%.
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Criteria Configuration</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(weights).map(([criterion, weight]) => (
                <div key={criterion} className="flex items-center justify-between py-3 border-b border-border/50 last:border-0">
                  <div>
                    <div className="text-sm font-medium text-foreground">{criterion.charAt(0).toUpperCase() + criterion.slice(1)}</div>
                    <div className="text-xs text-muted-foreground">Weight: {(weight * 100).toFixed(1)}%</div>
                  </div>
                  <div className="w-64">
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.01"
                      value={weight}
                      onChange={(e) => {
                        const val = parseFloat(e.target.value)
                        setWeights({ ...weights, [criterion]: val })
                      }}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary"
                    />
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 pt-4 border-t border-border">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Total Weight:</span>
                <span className={total === 1 ? "text-green-600" : "text-destructive"}>
                  {(total * 100).toFixed(1)}% {total === 1 ? "✓" : "✗ must equal 100%"}
                </span>
              </div>
            </div>
          </CardContent>
          <CardFooter>
            <Button
              onClick={handleSave}
              disabled={saving || Math.abs(total - 1) > 0.001}
              className="w-full bg-primary hover:bg-primary/90"
            >
              {saving ? (
                <div className="flex items-center justify-center gap-2">
                  <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
                  Saving...
                </div>
              ) : (
                <div className="flex items-center justify-center gap-2">
                  <Save className="w-4 h-4" />
                  Save Configuration
                </div>
              )}
            </Button>
          </CardFooter>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">About Scoring</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              The evaluation score for each vendor is a weighted sum of individual
              criterion scores (price, quality, review, warranty, delivery, reliability,
              budget). Changing these weights will affect scoring for all subsequent
              procurement evaluations. Historical results are preserved.
            </p>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}