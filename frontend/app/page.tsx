"use client"

import { useState } from "react"
import { SWRConfig } from "swr"
import { Header } from "@/components/header"
import { DataManagementTab } from "@/components/data-management-tab"
import { QueryExploreTab } from "@/components/query-explore-tab"
import { PlanningAssistant } from "@/components/planning-assistant"

export default function Page() {
  const [activeTab, setActiveTab] = useState("data")

  return (
    <SWRConfig
      value={{
        revalidateOnFocus: true,
        shouldRetryOnError: true,
        errorRetryCount: 3,
        errorRetryInterval: 5000,
        onError: (err: Error, key: string) => {
          console.error("[v0] SWR error for key:", key, err.message)
        },
      }}
    >
      <div className="flex min-h-screen flex-col bg-background">
        <Header activeTab={activeTab} onTabChange={setActiveTab} />
        <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 lg:px-6">
          {activeTab === "data" && <DataManagementTab />}
          {activeTab === "query" && <QueryExploreTab />}
          {activeTab === "planning" && <PlanningAssistant />}
        </main>
        <footer className="border-t bg-card py-4">
          <div className="mx-auto max-w-7xl px-4 lg:px-6">
            <p className="text-center text-xs text-muted-foreground">
              Healthcare Knowledge Graph &middot; Intelligent Document Parser & Medical Knowledge Graph System
            </p>
          </div>
        </footer>
      </div>
    </SWRConfig>
  )
}
