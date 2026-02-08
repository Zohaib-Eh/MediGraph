"use client"

import React, { useState } from "react"
import { motion } from "framer-motion"
import { Search, Loader2, Sparkles, type LucideIcon } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { useStats } from "@/lib/hooks"

const DEFAULT_EXAMPLE_QUERIES = [
  "How many facilities are in the database?",
  "Which facilities offer cardiology services?",
  "List facilities in Accra with their specialties",
  "What procedures do facilities offer?",
  "Which facilities provide 24/7 services?",
  "Show facilities by location",
]

interface SearchInterfaceProps {
  onSearch: (query: string) => void
  isLoading: boolean
  title?: string
  subtitle?: string
  placeholder?: string
  exampleQueries?: string[]
  icon?: LucideIcon
}

export function SearchInterface({
  onSearch,
  isLoading,
  title = "Explore Healthcare Facilities",
  subtitle = "Ask anything about healthcare facilities, equipment, specialties, and more",
  placeholder = "Ask anything about healthcare facilities...",
  exampleQueries = DEFAULT_EXAMPLE_QUERIES,
  icon: Icon = Sparkles,
}: SearchInterfaceProps) {
  const [query, setQuery] = useState("")
  const { data: stats } = useStats()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      onSearch(query.trim())
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
        className="flex flex-col items-center gap-4 rounded-2xl border border-border/50 bg-card/80 p-8 text-center shadow-sm"
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/15"
        >
          <Icon className="h-7 w-7 text-primary" />
        </motion.div>
        <div>
          <h2 className="text-xl font-semibold tracking-tight text-foreground">
            {title}
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {subtitle}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="flex w-full max-w-2xl gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={placeholder}
              className="pl-10 h-11"
              disabled={isLoading}
            />
          </div>
          <Button type="submit" disabled={!query.trim() || isLoading} className="h-11 px-6">
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              "Search"
            )}
          </Button>
        </form>

        {stats && (
          <p className="text-xs text-muted-foreground">
            Searching across {stats.total_facilities} facilities · {stats.total_equipment} equipment · {stats.total_specialties} specialties
          </p>
        )}
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="flex flex-col gap-2"
      >
        <p className="text-sm font-medium text-muted-foreground">Try these queries</p>
        <div className="flex flex-wrap gap-2">
          {exampleQueries.map((eq, i) => (
            <motion.button
              key={eq}
              type="button"
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.25 + i * 0.03 }}
              onClick={() => {
                setQuery(eq)
                onSearch(eq)
              }}
              disabled={isLoading}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="rounded-full border border-border/60 bg-card px-3.5 py-2 text-xs font-medium text-foreground transition-colors hover:bg-muted hover:border-primary/30 disabled:opacity-50"
            >
              {eq}
            </motion.button>
          ))}
        </div>
      </motion.div>
    </div>
  )
}
