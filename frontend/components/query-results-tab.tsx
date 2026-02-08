"use client"

import { useState, useCallback } from "react"
import { SearchInterface } from "./search-interface"
import { QueryResultCard } from "./query-result"
import { AnalysisInsights } from "./analysis-insights"
import { GraphVisualization } from "./graph-vis-simple"
import { LocationMap } from "./location-map"
import { Loader2, type LucideIcon } from "lucide-react"
import { api } from "@/lib/api"
import type { QueryResult } from "@/lib/api"

export interface QueryHistoryItem {
  query: string
  result: QueryResult
}

export interface QueryResultsTabProps {
  /** Search interface title */
  title: string
  /** Search interface subtitle */
  subtitle: string
  /** Search input placeholder */
  placeholder: string
  /** Example queries for quick-select */
  exampleQueries: string[]
  /** Icon for the search section (e.g. Sparkles, Lightbulb) */
  icon?: LucideIcon
  /** Loading message shown during query */
  loadingMessage?: string
  /** Error message when query fails */
  errorFallbackMessage?: string
  /** Graph visualization title */
  graphTitle?: string
  /** Map title */
  mapTitle?: string
}

export function QueryResultsTab({
  title,
  subtitle,
  placeholder,
  exampleQueries,
  icon,
  loadingMessage = "Querying knowledge graph...",
  errorFallbackMessage = "Query failed",
  graphTitle = "Query Graph Visualization",
  mapTitle = "Query Locations Map",
}: QueryResultsTabProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [history, setHistory] = useState<QueryHistoryItem[]>([])
  const [currentQuery, setCurrentQuery] = useState<string>("")

  const handleSearch = useCallback(async (query: string) => {
    if (!query.trim()) return
    setIsLoading(true)
    setError(null)
    setCurrentQuery(query)
    try {
      const result = await api.query(query, true)
      setHistory((prev) => [{ query, result }, ...prev])
    } catch (err) {
      setError(err instanceof Error ? err.message : errorFallbackMessage)
    } finally {
      setIsLoading(false)
    }
  }, [errorFallbackMessage])

  return (
    <div className="flex flex-col gap-6">
      <SearchInterface
        onSearch={handleSearch}
        isLoading={isLoading}
        title={title}
        subtitle={subtitle}
        placeholder={placeholder}
        exampleQueries={exampleQueries}
        icon={icon}
      />

      {isLoading && (
        <div className="flex items-center justify-center gap-3 py-8">
          <Loader2 className="h-5 w-5 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">{loadingMessage}</p>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4">
          <p className="text-sm text-destructive">{error}</p>
          <button
            type="button"
            onClick={() => setError(null)}
            className="mt-2 text-xs font-medium text-destructive underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {(currentQuery || history.length > 0) && (
        <div className="flex gap-6">
          {history.length > 0 && (
            <div className={currentQuery ? "flex-[65] min-w-0" : "w-full"}>
              <div className="flex flex-col gap-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium text-muted-foreground">
                    Results ({history.length})
                  </h3>
                  {history.length > 1 && (
                    <button
                      type="button"
                      onClick={() => setHistory([])}
                      className="text-xs text-muted-foreground hover:text-foreground"
                    >
                      Clear all
                    </button>
                  )}
                </div>
                {history.map((item, i) => (
                  <QueryResultCard key={i} query={item.query} result={item.result} />
                ))}
              </div>
            </div>
          )}

          {currentQuery && (
            <div className="flex-[35] min-w-0 flex flex-col gap-6">
              <GraphVisualization
                query={currentQuery}
                title={graphTitle}
                limit={50}
              />
              <LocationMap query={currentQuery} title={mapTitle} />
            </div>
          )}
        </div>
      )}

      <AnalysisInsights />
    </div>
  )
}
