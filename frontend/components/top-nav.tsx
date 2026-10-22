"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import { Bell, Menu, User as UserIcon, LogOut } from "lucide-react"
import { Button } from "@/components/button"
import { useAuth } from "@/lib/auth"

export default function AppHeader({
  title,
  breadcrumbs,
  onMenuToggle,
}: {
  title: string
  breadcrumbs?: string[]
  onMenuToggle?: () => void
}) {
  const [menuOpen, setMenuOpen] = React.useState(false)
  const { user, logout } = useAuth()
  const router = useRouter()

  function handleSignOut() {
    setMenuOpen(false)
    logout()
    router.replace("/login")
  }

  return (
    <header className="app-header">
      <div className="app-header__inner">
        <div className="app-header__left">
          {/* Hamburger for mobile */}
          {onMenuToggle && (
            <button
              onClick={onMenuToggle}
              className="app-header__menu-btn"
              aria-label="Toggle sidebar"
            >
              <Menu className="w-5 h-5" />
            </button>
          )}
          <h1 className="app-header__title">{title}</h1>
          {breadcrumbs && breadcrumbs.length > 0 && (
            <div className="app-header__breadcrumbs">
              {breadcrumbs.map((b, i) => (
                <span
                  key={i}
                  className={
                    i === breadcrumbs.length - 1
                      ? "app-header__breadcrumb--current"
                      : "app-header__breadcrumb"
                  }
                >
                  {i > 0 && <span className="app-header__breadcrumb-sep">/</span>}
                  {b}
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="app-header__right">
          <div className="app-header__status">
            <div className="app-header__status-dot" />
            <span className="text-xs text-muted-foreground">Backend connected</span>
          </div>
          <Button variant="ghost" size="icon">
            <Bell className="w-5 h-5" />
          </Button>
          <div className="relative">
            <Button variant="outline" size="icon" onClick={() => setMenuOpen(!menuOpen)}>
              <UserIcon className="w-5 h-5" />
            </Button>
            {menuOpen && (
              <div className="app-header__dropdown">
                <div className="border-b border-border px-3 py-2">
                  <p className="text-sm font-medium text-foreground">{user?.name || "Guest"}</p>
                  <p className="text-xs text-muted-foreground">
                    {user?.title || "Not signed in"}
                    {user?.username ? ` · ${user.username}` : ""}
                  </p>
                </div>
                <div className="space-y-1 px-3 py-2">
                  <button
                    onClick={() => setMenuOpen(false)}
                    className="w-full rounded-md p-2 text-left text-sm text-muted-foreground transition-colors hover:bg-accent"
                  >
                    Account Settings
                  </button>
                  <button
                    onClick={handleSignOut}
                    className="mt-1 flex w-full items-center gap-2 rounded-md p-2 text-left text-sm text-destructive transition-colors hover:bg-red-50/50"
                  >
                    <LogOut className="h-4 w-4" />
                    Sign Out
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}