"use client"

import { Building2, Wrench, Syringe, Stethoscope, MapPin, Zap, Link2, AlertCircle } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import type { GraphStats } from "@/lib/api"

interface StatsCardsProps {
  stats: GraphStats | undefined
  isLoading: boolean
  error?: Error | null
}

const statConfig = [
  { key: "total_facilities" as const, label: "Facilities", icon: Building2, color: "text-[hsl(var(--chart-1))]", bg: "bg-[hsl(var(--chart-1)/.1)]" },
  { key: "total_equipment" as const, label: "Equipment", icon: Wrench, color: "text-[hsl(var(--chart-2))]", bg: "bg-[hsl(var(--chart-2)/.1)]" },
  { key: "total_procedures" as const, label: "Procedures", icon: Syringe, color: "text-[hsl(var(--chart-3))]", bg: "bg-[hsl(var(--chart-3)/.1)]" },
  { key: "total_specialties" as const, label: "Specialties", icon: Stethoscope, color: "text-[hsl(var(--chart-5))]", bg: "bg-[hsl(var(--chart-5)/.1)]" },
  { key: "total_locations" as const, label: "Locations", icon: MapPin, color: "text-[hsl(var(--chart-4))]", bg: "bg-[hsl(var(--chart-4)/.1)]" },
  { key: "total_capabilities" as const, label: "Capabilities", icon: Zap, color: "text-orange-500", bg: "bg-orange-500/10" },
  { key: "total_relationships" as const, label: "Relationships", icon: Link2, color: "text-muted-foreground", bg: "bg-muted" },
]

export function StatsCards({ stats, isLoading, error }: StatsCardsProps) {
  if (error) {
    return (
      <Card className="border-destructive/50 bg-destructive/5">
        <CardContent className="flex items-center gap-3 p-4">
          <AlertCircle className="h-5 w-5 text-destructive" />
          <div>
            <p className="text-sm font-medium text-destructive">Failed to load stats</p>
            <p className="text-xs text-muted-foreground">
              {error.message || "Could not connect to the backend API. Make sure the FastAPI server is running at the configured URL."}
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
      {statConfig.map((stat) => (
        <Card key={stat.key} className="border-border/50 hover:border-primary/30 transition-colors">
          <CardContent className="flex flex-col gap-3 p-4">
            <div className="flex items-center justify-between">
              <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${stat.bg}`}>
                <stat.icon className={`h-4 w-4 ${stat.color}`} />
              </div>
            </div>
            {isLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <div>
                <p className="text-2xl font-bold text-foreground">
                  {stats ? (stats[stat.key] ?? 0).toLocaleString() : "\u2014"}
                </p>
                <p className="text-xs text-muted-foreground">{stat.label}</p>
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
