"use client"

import { Lightbulb } from "lucide-react"
import { QueryResultsTab } from "./query-results-tab"

const PLANNING_EXAMPLE_QUERIES = [
  "Which facilities lack ultrasound equipment and where should we prioritize distribution?",
  "Which regions need more cardiology services and which facilities could offer them?",
  "How should we distribute 10 new ultrasound machines across facilities for maximum impact?",
  "Which facilities are at capacity and need expansion based on their current utilization?",
]

export function PlanningAssistant() {
  return (
    <QueryResultsTab
      title="Healthcare Planning Assistant"
      subtitle="Get AI-powered recommendations for resource allocation, service expansion, and capacity planning"
      placeholder="e.g., Which facilities should receive MRI machines based on patient load?"
      exampleQueries={PLANNING_EXAMPLE_QUERIES}
      icon={Lightbulb}
      loadingMessage="Generating planning recommendation..."
      errorFallbackMessage="Planning query failed"
      graphTitle="Relevant Knowledge Graph"
      mapTitle="Planning Locations Map"
    />
  )
}
