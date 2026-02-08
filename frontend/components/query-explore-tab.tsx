"use client"

import { useState, useCallback } from "react"
import { SearchInterface } from "./search-interface"
import { QueryResultCard } from "./query-result"
import { AnalysisInsights } from "./analysis-insights"
import { GraphVisualization } from "./graph-vis-simple"
import { Loader2 } from "lucide-react"
import { api } from "@/lib/api"
import type { QueryResult } from "@/lib/api"

interface QueryHistory {
  query: string
  result: QueryResult
}

export function QueryExploreTab() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [history, setHistory] = useState<QueryHistory[]>([])
  const [currentQuery, setCurrentQuery] = useState<string>("")

  const handleSearch = useCallback(async (query: string) => {
    setIsLoading(true)
    setError(null)
    setCurrentQuery(query)
    
    try {
      const result = await api.query(query, true)
      setHistory((prev) => [{ query, result }, ...prev])
    } catch (err) {
      setError(err instanceof Error ? err.message : "Query failed")
    } finally {
      setIsLoading(false)
    }
  }, [])

  return (
    <div className="flex flex-col gap-6">
      <SearchInterface onSearch={handleSearch} isLoading={isLoading} />

      {isLoading && (
        <div className="flex items-center justify-center gap-3 py-8">
          <Loader2 className="h-5 w-5 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Querying knowledge graph...</p>
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

      {/* Side-by-side layout: Results (65%) and Graph (35%) */}
      {(currentQuery || history.length > 0) && (
        <div className="flex gap-6">
          {/* Query Results - 65% */}
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

          {/* Graph Visualization - 35% */}
          {currentQuery && (
            <div className="flex-[35] min-w-0">
              <GraphVisualization
                query={currentQuery}
                title="Query Graph Visualization"
                limit={50}
              />
            </div>
          )}
        </div>
      )}

      <AnalysisInsights />
    </div>
  )
}
