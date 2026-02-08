"use client"

import { Activity, Database, Search, Lightbulb, Moon, Sun } from "lucide-react"
import { useEffect, useState } from "react"
import { useHealth } from "@/lib/hooks"
import { cn } from "@/lib/utils"

interface HeaderProps {
  activeTab: string
  onTabChange: (tab: string) => void
}

export function Header({ activeTab, onTabChange }: HeaderProps) {
  const { data: health } = useHealth()
  const [darkMode, setDarkMode] = useState(false)

  const isHealthy = health?.status === "ok" || health?.status === "healthy"

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add("dark")
    } else {
      document.documentElement.classList.remove("dark")
    }
  }, [darkMode])

  return (
    <header className="sticky top-0 z-50 border-b bg-card">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 lg:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary">
            <Activity className="h-5 w-5 text-primary-foreground" />
          </div>
          <div className="hidden sm:block">
            <h1 className="text-base font-semibold text-foreground">Healthcare Knowledge Graph</h1>
            <p className="text-xs text-muted-foreground">Intelligent Document Parser</p>
          </div>
        </div>

        <nav className="flex items-center gap-1 rounded-lg bg-muted p-1">
          <button
            type="button"
            onClick={() => onTabChange("data")}
            className={cn(
              "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
              activeTab === "data"
                ? "bg-card text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            <Database className="h-4 w-4" />
            <span className="hidden sm:inline">Data Management</span>
            <span className="sm:hidden">Data</span>
          </button>
          <button
            type="button"
            onClick={() => onTabChange("query")}
            className={cn(
              "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
              activeTab === "query"
                ? "bg-card text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            <Search className="h-4 w-4" />
            <span className="hidden sm:inline">Query & Explore</span>
            <span className="sm:hidden">Query</span>
          </button>
          <button
            type="button"
            onClick={() => onTabChange("planning")}
            className={cn(
              "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
              activeTab === "planning"
                ? "bg-card text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            <Lightbulb className="h-4 w-4" />
            <span className="hidden sm:inline">Planning</span>
            <span className="sm:hidden">Plan</span>
          </button>
        </nav>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div
              className={cn(
                "h-2.5 w-2.5 rounded-full",
                isHealthy ? "bg-[hsl(var(--success))]" : "bg-destructive"
              )}
            />
            <span className="hidden text-xs text-muted-foreground md:inline">
              {isHealthy ? "System Online" : "Offline"}
            </span>
          </div>
          <button
            type="button"
            onClick={() => setDarkMode(!darkMode)}
            className="rounded-md p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            aria-label="Toggle dark mode"
          >
            {darkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
        </div>
      </div>
    </header>
  )
}
