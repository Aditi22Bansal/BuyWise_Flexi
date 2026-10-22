"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement> {
  variant?:
    | "default"
    | "secondary"
    | "destructive"
    | "outline"
    | "success"
    | "warning"
    | "pending"
  className?: string
}

const badgeVariants = {
  default: "bg-primary text-primary-foreground",
  secondary: "bg-secondary text-secondary-foreground",
  destructive:
    "bg-destructive text-destructive-foreground",
  outline: "border text-foreground",
  success: "bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400",
  warning: "bg-amber-100 text-amber-700 dark:bg-amber-900/20 dark:text-amber-400",
  pending: "bg-blue-100 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400",
}

const Badge = React.forwardRef<HTMLDivElement, BadgeProps>(
  ({ className, variant = "default", ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
        badgeVariants[variant],
        className
      )}
      {...props}
    />
  )
)
Badge.displayName = "Badge"

export { Badge }