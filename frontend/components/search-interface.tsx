"use client"

import React from "react"

import { useState } from "react"
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
      <div className="flex flex-col items-center gap-4 rounded-xl bg-card border p-8 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
          <Icon className="h-6 w-6 text-primary" />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-foreground">
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
            Searching across {stats.total_facilities} facilities &middot;{" "}
            {stats.total_equipment} equipment types &middot;{" "}
            {stats.total_specialties} specialties
          </p>
        )}
      </div>

      <div className="flex flex-col gap-2">
        <p className="text-sm font-medium text-muted-foreground">Try these queries</p>
        <div className="flex flex-wrap gap-2">
          {exampleQueries.map((eq) => (
            <button
              key={eq}
              type="button"
              onClick={() => {
                setQuery(eq)
                onSearch(eq)
              }}
              disabled={isLoading}
              className="rounded-full border bg-card px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-muted disabled:opacity-50"
            >
              {eq}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
