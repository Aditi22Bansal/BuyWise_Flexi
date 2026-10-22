"use client"

import * as React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  LayoutDashboard,
  FilePlus,
  List,
  Activity,
  PieChart,
  MessageCircle,
  CheckCircle2,
  Settings,
  FileText,
  X,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useAuth } from "@/lib/auth"

const NAV_ITEMS = [
  {
    section: "WORKSPACE",
    items: [
      { name: "Overview", href: "/", icon: LayoutDashboard, roles: null },
      { name: "New Procurement", href: "/new-procurement", icon: FilePlus, roles: ["admin", "requester"] },
      { name: "Procurement Requests", href: "/requests", icon: List, roles: null },
    ],
  },
  {
    section: "INTELLIGENCE",
    items: [
      { name: "Agent Activity", href: "/agent-activity", icon: Activity, roles: null },
      { name: "Vendor Comparison", href: "/vendor-comparison", icon: PieChart, roles: null },
      { name: "Negotiations", href: "/negotiations", icon: MessageCircle, roles: null },
    ],
  },
  {
    section: "MANAGEMENT",
    items: [
      { name: "Approvals", href: "/approvals", icon: CheckCircle2, roles: ["admin", "approver", "auditor"] },
      { name: "Evaluation Settings", href: "/settings", icon: Settings, roles: ["admin"] },
      { name: "Audit Logs", href: "/audit-logs", icon: FileText, roles: null },
    ],
  },
]

interface SidebarProps {
  collapsed?: boolean
  mobileOpen?: boolean
  onMobileClose?: () => void
}

export default function AppSidebar({
  collapsed = false,
  mobileOpen = false,
  onMobileClose,
}: SidebarProps) {
  const pathname = usePathname()
  const { user } = useAuth()

  function canSee(item: { roles: string[] | null }) {
    if (!item.roles) return true
    return !!user && item.roles.includes(user.role)
  }

  return (
    <aside
      className={cn(
        "sidebar",
        collapsed && "sidebar--collapsed",
        mobileOpen && "sidebar--mobile-open"
      )}
    >
      <div className="sidebar__inner">
        {/* Logo + mobile close */}
        <div className="sidebar__logo">
          <Link href="/" className="sidebar__logo-link">
            <div className="sidebar__logo-icon">
              <span className="text-primary-foreground font-bold text-sm">BW</span>
            </div>
            {!collapsed && (
              <span className="font-semibold tracking-tight text-sidebar-foreground">
                BuyWise
              </span>
            )}
          </Link>
          {/* Mobile close button */}
          {mobileOpen && onMobileClose && (
            <button
              onClick={onMobileClose}
              className="sidebar__close-btn"
              aria-label="Close sidebar"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Navigation */}
        <nav className="sidebar__nav">
          {NAV_ITEMS.map((section) => (
            <div key={section.section} className="sidebar__section">
              {section.section && !collapsed && (
                <h3 className="sidebar__section-title">
                  {section.section}
                </h3>
              )}
              {section.items.filter(canSee).map((item) => {
                const Icon = item.icon
                const isActive =
                  pathname === item.href ||
                  (pathname !== "/" && pathname.startsWith(item.href + "/"))
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    onClick={onMobileClose}
                    className={cn(
                      "sidebar__link",
                      isActive && "sidebar__link--active"
                    )}
                  >
                    <Icon className="sidebar__link-icon" />
                    {!collapsed && <span className="sidebar__link-label">{item.name}</span>}
                  </Link>
                )
              })}
            </div>
          ))}
        </nav>

        {/* Bottom user + settings */}
        <div className="sidebar__bottom">
          {!collapsed && user && (
            <div className="mb-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2">
              <p className="truncate text-xs font-medium text-sidebar-foreground">{user.name}</p>
              <p className="text-[11px] text-slate-400">{user.title}</p>
            </div>
          )}
          <Link
            href="/settings"
            onClick={onMobileClose}
            className={cn(
              "sidebar__link",
              pathname === "/settings" && "sidebar__link--active"
            )}
          >
            <Settings className="sidebar__link-icon" />
            {!collapsed && <span className="sidebar__link-label">Settings</span>}
          </Link>
        </div>
      </div>
    </aside>
  )
}