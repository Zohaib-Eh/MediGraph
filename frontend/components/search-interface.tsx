"use client"

import React from "react"

import { useState } from "react"
import { Search, Loader2, Sparkles } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { useStats } from "@/lib/hooks"

const EXAMPLE_QUERIES = [
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
}

export function SearchInterface({ onSearch, isLoading }: SearchInterfaceProps) {
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
          <Sparkles className="h-6 w-6 text-primary" />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-foreground">
            Explore Healthcare Facilities
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Ask anything about healthcare facilities, equipment, specialties, and more
          </p>
        </div>

        <form onSubmit={handleSubmit} className="flex w-full max-w-2xl gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask anything about healthcare facilities..."
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
          {EXAMPLE_QUERIES.map((eq) => (
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
