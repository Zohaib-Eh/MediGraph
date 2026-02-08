"use client"

import { useState, useCallback } from "react"
import { motion } from "framer-motion"
import { useStats } from "@/lib/hooks"
import { StatsCards } from "./stats-cards"
import { FileUpload } from "./file-upload"
import { GraphControls } from "./graph-controls"
import { DataAnalytics } from "./data-analytics"
import { GraphVisualization } from "./graph-vis-simple"
import type { UploadResult } from "@/lib/api"

const container = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.06 },
  },
}

const item = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0 },
}

export function DataManagementTab() {
  const { data: stats, isLoading, error, mutate } = useStats()
  const [hasUploadResult, setHasUploadResult] = useState(false)
  const [refreshKey, setRefreshKey] = useState(0)

  const handleUploadComplete = useCallback((_result: UploadResult) => {
    setHasUploadResult(true)
    mutate()
    setRefreshKey((prev) => prev + 1)
  }, [mutate])

  const handleRefresh = useCallback(async () => {
    await mutate()
    setRefreshKey((prev) => prev + 1)
  }, [mutate])

  return (
    <motion.div
      className="flex flex-col gap-6"
      variants={container}
      initial="hidden"
      animate="visible"
    >
      <motion.div variants={item}>
        <h2 className="text-lg font-semibold tracking-tight text-foreground">
          Dashboard
        </h2>
        <p className="text-sm text-muted-foreground">
          Monitor graph statistics and manage healthcare data
        </p>
      </motion.div>

      <motion.div variants={item}>
        <StatsCards stats={stats} isLoading={isLoading} error={error} />
      </motion.div>

      <motion.div variants={item} className="grid gap-6 lg:grid-cols-2">
        <FileUpload onUploadComplete={handleUploadComplete} />
        <GraphControls onRefresh={handleRefresh} hasUploadResult={hasUploadResult} />
      </motion.div>

      <motion.div variants={item}>
        <GraphVisualization
          key={refreshKey}
          title="Knowledge Graph Overview"
          onRefresh={handleRefresh}
        />
      </motion.div>

      <motion.div variants={item}>
        <DataAnalytics stats={stats} error={error} />
      </motion.div>
    </motion.div>
  )
}
