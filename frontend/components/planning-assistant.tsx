"use client"

import { useState, useCallback } from "react"
import { SearchInterface } from "./search-interface"
import { QueryResultCard } from "./query-result"
import { AnalysisInsights } from "./analysis-insights"
import { GraphVisualization } from "./graph-vis-simple"
import { LocationMap } from "./location-map"
import { Loader2, Lightbulb } from "lucide-react"
import { api } from "@/lib/api"
import type { QueryResult } from "@/lib/api"

const PLANNING_EXAMPLE_QUERIES = [
  "Which facilities lack ultrasound equipment and where should we prioritize distribution?",
  "Which regions need more cardiology services and which facilities could offer them?",
  "How should we distribute 10 new ultrasound machines across facilities for maximum impact?",
  "Which facilities are at capacity and need expansion based on their current utilization?",
]

interface PlanningHistory {
  query: string
  result: QueryResult
}

export function PlanningAssistant() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [history, setHistory] = useState<PlanningHistory[]>([])
  const [currentQuery, setCurrentQuery] = useState<string>("")

  const handleSearch = useCallback(async (query: string) => {
    if (!query.trim()) return
    setIsLoading(true)
    setError(null)
    setCurrentQuery(query)
    try {
      const response = await api.query(query, true)
      setHistory((prev) => [{ query, result: response }, ...prev])
    } catch (err) {
      setError(err instanceof Error ? err.message : "Planning query failed")
    } finally {
      setIsLoading(false)
    }
  }, [])

  return (
    <div className="flex flex-col gap-6">
      <SearchInterface
        onSearch={handleSearch}
        isLoading={isLoading}
        title="Healthcare Planning Assistant"
        subtitle="Get AI-powered recommendations for resource allocation, service expansion, and capacity planning"
        placeholder="e.g., Which facilities should receive MRI machines based on patient load?"
        exampleQueries={PLANNING_EXAMPLE_QUERIES}
        icon={Lightbulb}
      />

      {isLoading && (
        <div className="flex items-center justify-center gap-3 py-8">
          <Loader2 className="h-5 w-5 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Generating planning recommendation...</p>
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
          {/* Planning Results - 65% */}
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
                title="Relevant Knowledge Graph"
                limit={50}
              />
            </div>
          )}
        </div>
      )}

      {/* Map: below the knowledge graph */}
      {currentQuery && (
        <LocationMap
          query={currentQuery}
          title="Planning Locations Map"
        />
      )}

      <AnalysisInsights />
    </div>
  )
}
