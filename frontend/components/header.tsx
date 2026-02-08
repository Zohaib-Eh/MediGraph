"use client"

import Link from "next/link"
import { Activity, Database, Search, Lightbulb, Moon, Sun } from "lucide-react"
import { useTheme } from "next-themes"
import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { useHealth } from "@/lib/hooks"
import { cn } from "@/lib/utils"

interface HeaderProps {
  activeTab: string
  onTabChange: (tab: string) => void
}

const tabs = [
  { id: "data", label: "Data Management", short: "Data", icon: Database },
  { id: "query", label: "Query & Explore", short: "Query", icon: Search },
  { id: "planning", label: "Planning", short: "Plan", icon: Lightbulb },
] as const

export function Header({ activeTab, onTabChange }: HeaderProps) {
  const { data: health } = useHealth()
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)

  useEffect(() => setMounted(true), [])
  const isDark = mounted ? theme === "dark" : true

  const isHealthy = health?.status === "ok" || health?.status === "healthy"

  return (
    <motion.header
      initial={{ y: -16, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="sticky top-0 z-50 border-b border-border/50 bg-card/80 backdrop-blur-md"
    >
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 lg:px-6">
        <Link href="/" className="flex items-center gap-3">
          <motion.div
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.98 }}
            className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary shadow-lg shadow-primary/25"
          >
            <Activity className="h-5 w-5 text-primary-foreground" />
          </motion.div>
          <div className="hidden sm:block">
            <h1 className="text-base font-semibold tracking-tight text-foreground">
              MediGraph
            </h1>
            <p className="text-xs text-muted-foreground">
              Healthcare Knowledge Graph
            </p>
          </div>
        </Link>

        <nav className="flex items-center gap-0.5 rounded-xl bg-muted/80 p-1">
          {tabs.map(({ id, label, short, icon: Icon }) => (
            <motion.button
              key={id}
              type="button"
              onClick={() => onTabChange(id)}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className={cn(
                "relative flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                activeTab === id
                  ? "text-foreground"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              {activeTab === id && (
                <motion.span
                  layoutId="header-tab"
                  className="absolute inset-0 rounded-lg bg-card shadow-sm"
                  transition={{ type: "spring", bounce: 0.2, duration: 0.4 }}
                  style={{ zIndex: 0 }}
                />
              )}
              <Icon className="relative z-10 h-4 w-4" />
              <span className="relative z-10 hidden sm:inline">{label}</span>
              <span className="relative z-10 sm:hidden">{short}</span>
            </motion.button>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 rounded-lg bg-muted/60 px-2.5 py-1.5">
            <motion.div
              animate={{ scale: isHealthy ? 1 : [1, 1.2, 1] }}
              transition={{ repeat: isHealthy ? 0 : Infinity, duration: 1.5 }}
              className={cn(
                "h-2 w-2 rounded-full",
                isHealthy ? "bg-emerald-500" : "bg-destructive"
              )}
            />
            <span className="text-xs text-muted-foreground">
              {isHealthy ? "Online" : "Offline"}
            </span>
          </div>
          <motion.button
            type="button"
            onClick={() => setTheme(isDark ? "light" : "dark")}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="rounded-lg p-2.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            aria-label="Toggle theme"
          >
            {mounted && !isDark ? (
              <Moon className="h-4 w-4" />
            ) : (
              <Sun className="h-4 w-4" />
            )}
          </motion.button>
        </div>
      </div>
    </motion.header>
  )
}
