"use client"

import React from "react"

import { useState } from "react"
import { MapPin, AlertTriangle, Wrench, Loader2 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { useMedicalDeserts, useEquipmentGaps, useInconsistencies } from "@/lib/hooks"
import { formatValue } from "@/lib/utils"

export function AnalysisInsights() {
  const [activeTab, setActiveTab] = useState("deserts")
  const { data: deserts, isLoading: desertsLoading } = useMedicalDeserts()
  const { data: gaps, isLoading: gapsLoading } = useEquipmentGaps()
  const { data: inconsistencies, isLoading: inconsistenciesLoading } = useInconsistencies()

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h3 className="text-lg font-semibold text-foreground">Analysis & Insights</h3>
        <p className="text-sm text-muted-foreground">
          Explore healthcare coverage gaps and data quality
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="w-full justify-start">
          <TabsTrigger value="deserts" className="gap-2">
            <MapPin className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Medical Deserts</span>
            <span className="sm:hidden">Deserts</span>
          </TabsTrigger>
          <TabsTrigger value="gaps" className="gap-2">
            <Wrench className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Equipment Gaps</span>
            <span className="sm:hidden">Gaps</span>
          </TabsTrigger>
          <TabsTrigger value="issues" className="gap-2">
            <AlertTriangle className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Inconsistencies</span>
            <span className="sm:hidden">Issues</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="deserts">
          <AnalysisPanel
            data={deserts}
            isLoading={desertsLoading}
            emptyMessage="No medical deserts detected"
            icon={<MapPin className="h-5 w-5 text-[hsl(var(--warning))]" />}
          />
        </TabsContent>

        <TabsContent value="gaps">
          <AnalysisPanel
            data={gaps}
            isLoading={gapsLoading}
            emptyMessage="No equipment gaps detected"
            icon={<Wrench className="h-5 w-5 text-primary" />}
          />
        </TabsContent>

        <TabsContent value="issues">
          <AnalysisPanel
            data={inconsistencies}
            isLoading={inconsistenciesLoading}
            emptyMessage="No inconsistencies found"
            icon={<AlertTriangle className="h-5 w-5 text-destructive" />}
          />
        </TabsContent>
      </Tabs>
    </div>
  )
}

interface AnalysisPanelProps {
  data:
    | {
        results: Array<Record<string, unknown>>
        summary?: string
      }
    | undefined
  isLoading: boolean
  emptyMessage: string
  icon: React.ReactNode
}

function AnalysisPanel({ data, isLoading, emptyMessage, icon }: AnalysisPanelProps) {
  const [expanded, setExpanded] = useState(false)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-5 w-5 animate-spin text-primary" />
        <span className="ml-2 text-sm text-muted-foreground">Loading analysis...</span>
      </div>
    )
  }

  if (!data || !data.results || data.results.length === 0) {
    return (
      <Card className="border-border/50">
        <CardContent className="flex flex-col items-center gap-3 py-12">
          {icon}
          <p className="text-sm text-muted-foreground">{emptyMessage}</p>
          <p className="text-xs text-muted-foreground">
            Upload data and build the graph to see analysis results
          </p>
        </CardContent>
      </Card>
    )
  }

  const displayItems = expanded ? data.results : data.results.slice(0, 5)

  return (
    <div className="flex flex-col gap-3">
      {data.summary && (
        <Card className="border-[hsl(var(--warning))]/20 bg-[hsl(var(--warning))]/5">
          <CardContent className="p-4">
            <p className="text-sm text-foreground">{data.summary}</p>
          </CardContent>
        </Card>
      )}
      <div className="flex flex-col gap-2">
        {displayItems.map((item, i) => (
          <Card key={i} className="border-border/50 hover:border-primary/20 transition-colors">
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <div className="shrink-0 pt-0.5">{icon}</div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 flex-1 min-w-0">
                  {Object.entries(item).map(([key, value]) => {
                    const isNull = value === null || value === undefined || value === ""
                    const displayValue = isNull 
                      ? "N/A" 
                      : typeof value === "object" && value !== null
                        ? JSON.stringify(value)
                        : String(value)
                    
                    return (
                      <div key={key} className="flex flex-col gap-0.5">
                        <span className="text-xs font-medium text-muted-foreground capitalize">
                          {key.replace(/_/g, " ")}
                        </span>
                        <span className={`text-sm ${
                          isNull 
                            ? "text-muted-foreground/60 italic" 
                            : "text-foreground font-medium"
                        } truncate`}>
                          {displayValue}
                        </span>
                      </div>
                    )
                  })}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      {data.results.length > 5 && (
        <Button variant="outline" size="sm" onClick={() => setExpanded(!expanded)}>
          {expanded ? "Show less" : `Show all ${data.results.length} results`}
        </Button>
      )}
    </div>
  )
}
