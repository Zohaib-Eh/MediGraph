"use client"

import { useState, useCallback } from "react"
import { useStats } from "@/lib/hooks"
import { StatsCards } from "./stats-cards"
import { FileUpload } from "./file-upload"
import { GraphControls } from "./graph-controls"
import { DataAnalytics } from "./data-analytics"
import { GraphVisualization } from "./graph-vis-simple"
import type { UploadResult } from "@/lib/api"

export function DataManagementTab() {
  const { data: stats, isLoading, error, mutate } = useStats()
  const [hasUploadResult, setHasUploadResult] = useState(false)
  const [refreshKey, setRefreshKey] = useState(0)

  const handleUploadComplete = useCallback((_result: UploadResult) => {
    setHasUploadResult(true)
    mutate()
    setRefreshKey((prev) => prev + 1) // Trigger graph refresh
  }, [mutate])

  const handleRefresh = useCallback(async () => {
    await mutate()
    setRefreshKey((prev) => prev + 1) // Trigger graph refresh
  }, [mutate])

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-lg font-semibold text-foreground">Dashboard</h2>
        <p className="text-sm text-muted-foreground">
          Monitor graph statistics and manage healthcare data
        </p>
      </div>

      <StatsCards stats={stats} isLoading={isLoading} error={error} />

      <div className="grid gap-6 lg:grid-cols-2">
        <FileUpload onUploadComplete={handleUploadComplete} />
        <GraphControls onRefresh={handleRefresh} hasUploadResult={hasUploadResult} />
      </div>

      <GraphVisualization
        key={refreshKey}
        title="Knowledge Graph Overview"
        onRefresh={handleRefresh}
      />

      <DataAnalytics stats={stats} error={error} />
    </div>
  )
}
