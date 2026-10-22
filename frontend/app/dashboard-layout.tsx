"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import AppSidebar from "@/components/sidebar"
import AppHeader from "@/components/top-nav"
import { useAuth } from "@/lib/auth"

export default function DashboardLayout({
  children,
  title,
  breadcrumbs,
}: {
  children: React.ReactNode
  title?: string
  breadcrumbs?: string[]
}) {
  const [sidebarOpen, setSidebarOpen] = React.useState(false)
  const { user, loading } = useAuth()
  const router = useRouter()

  React.useEffect(() => {
    if (!loading && !user) {
      router.replace("/login")
    }
  }, [loading, user, router])

  if (loading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-3">
          <div className="h-10 w-10 animate-pulse rounded-full border-b-2 border-blue-600" />
          <p className="text-sm text-slate-500">Loading workspace...</p>
        </div>
      </div>
    )
  }

  return (
    <>
      {/* Grid shell: sidebar column + main column */}
      <div className="app-shell">
        <AppSidebar
          mobileOpen={sidebarOpen}
          onMobileClose={() => setSidebarOpen(false)}
        />
        <div className="app-main">
          <AppHeader
            title={title || "BuyWise"}
            breadcrumbs={breadcrumbs}
            onMenuToggle={() => setSidebarOpen((prev) => !prev)}
          />
          <main className="app-content">{children}</main>
        </div>
      </div>

      {/* Mobile overlay backdrop */}
      {sidebarOpen && (
        <div
          className="sidebar-backdrop"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </>
  )
}