import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs))
}

export function formatCurrency(value: number, currency: string = "USD"): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
  }).format(value)
}

export function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  })
}

export function formatDateTime(dateString: string): string {
  return new Date(dateString).toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

export function getStatusColor(status: string): string {
  switch (status?.toLowerCase()) {
    case "completed":
    case "approved":
      return "bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400"
    case "pending":
    case "running":
      return "bg-blue-100 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400"
    case "rejected":
    case "failed":
      return "bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400"
    case "skipped":
      return "bg-gray-100 text-gray-700 dark:bg-gray-800/50 dark:text-gray-400"
    default:
      return "bg-gray-100 text-gray-700"
  }
}