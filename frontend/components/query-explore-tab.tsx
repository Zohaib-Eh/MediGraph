"use client"

import { QueryResultsTab } from "./query-results-tab"

const EXAMPLE_QUERIES = [
  "How many facilities are in the database?",
  "Which facilities offer cardiology services?",
  "List facilities in Accra with their specialties",
  "What procedures do facilities offer?",
  "Which facilities provide 24/7 services?",
  "Show facilities by location",
]

export function QueryExploreTab() {
  return (
    <QueryResultsTab
      title="Explore Healthcare Facilities"
      subtitle="Ask anything about healthcare facilities, equipment, specialties, and more"
      placeholder="Ask anything about healthcare facilities..."
      exampleQueries={EXAMPLE_QUERIES}
      loadingMessage="Querying knowledge graph..."
      errorFallbackMessage="Query failed"
      graphTitle="Query Graph Visualization"
      mapTitle="Query Locations Map"
    />
  )
}
