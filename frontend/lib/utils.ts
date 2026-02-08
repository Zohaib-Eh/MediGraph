import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Format a value, handling null/undefined gracefully
 */
export function formatValue(value: unknown, fallback: string = "N/A"): string {
  if (value === null || value === undefined || value === "") {
    return fallback
  }
  return String(value)
}

/**
 * Check if a value is empty/null/undefined
 */
export function isEmpty(value: unknown): boolean {
  return value === null || value === undefined || value === "" || value === "null"
}
