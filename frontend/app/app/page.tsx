"use client"

import { useState, useEffect, Suspense } from "react"
import { useSearchParams } from "next/navigation"
import { SWRConfig } from "swr"
import { motion, AnimatePresence } from "framer-motion"
import { Header } from "@/components/header"
import { DataManagementTab } from "@/components/data-management-tab"
import { QueryExploreTab } from "@/components/query-explore-tab"
import { PlanningAssistant } from "@/components/planning-assistant"

const tabVariants = {
  hidden: { opacity: 0, y: 8 },
  visible: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -4 },
}

function AppContent() {
  const searchParams = useSearchParams()
  const tabParam = searchParams.get("tab")
  const [activeTab, setActiveTab] = useState("data")

  useEffect(() => {
    if (tabParam === "query" || tabParam === "planning") {
      setActiveTab(tabParam)
    }
  }, [tabParam])

  return (
    <SWRConfig
      value={{
        revalidateOnFocus: true,
        shouldRetryOnError: true,
        errorRetryCount: 3,
        errorRetryInterval: 5000,
        onError: (err: Error, key: string) => {
          console.error("[SWR] error for key:", key, err.message)
        },
      }}
    >
      <div className="flex min-h-screen flex-col bg-background">
        <Header activeTab={activeTab} onTabChange={setActiveTab} />
        <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 lg:px-6">
          <AnimatePresence mode="wait">
            {activeTab === "data" && (
              <motion.div
                key="data"
                variants={tabVariants}
                initial="hidden"
                animate="visible"
                exit="exit"
                transition={{ duration: 0.2 }}
                className="flex flex-col gap-6"
              >
                <DataManagementTab />
              </motion.div>
            )}
            {activeTab === "query" && (
              <motion.div
                key="query"
                variants={tabVariants}
                initial="hidden"
                animate="visible"
                exit="exit"
                transition={{ duration: 0.2 }}
                className="flex flex-col gap-6"
              >
                <QueryExploreTab />
              </motion.div>
            )}
            {activeTab === "planning" && (
              <motion.div
                key="planning"
                variants={tabVariants}
                initial="hidden"
                animate="visible"
                exit="exit"
                transition={{ duration: 0.2 }}
                className="flex flex-col gap-6"
              >
                <PlanningAssistant />
              </motion.div>
            )}
          </AnimatePresence>
        </main>
        <motion.footer
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="border-t border-border/50 bg-card/50 py-4"
        >
          <div className="mx-auto max-w-7xl px-4 lg:px-6">
            <p className="text-center text-xs text-muted-foreground">
              MediGraph · Intelligent Document Parser & Medical Knowledge Graph
            </p>
          </div>
        </motion.footer>
      </div>
    </SWRConfig>
  )
}

export default function AppPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center bg-background"><div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" /></div>}>
      <AppContent />
    </Suspense>
  )
}
