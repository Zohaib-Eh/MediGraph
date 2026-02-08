"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts"
import type { GraphStats } from "@/lib/api"

interface DataAnalyticsProps {
  stats: GraphStats | undefined
  error?: Error | null
}

const COLORS = [
  "hsl(217, 91%, 60%)",
  "hsl(160, 84%, 39%)",
  "hsl(38, 92%, 50%)",
  "hsl(0, 84%, 60%)",
  "hsl(262, 83%, 58%)",
  "hsl(215, 14%, 46%)",
]

export function DataAnalytics({ stats, error }: DataAnalyticsProps) {
  if (error) {
    return null
  }

  const allEntries = stats
    ? [
        { name: "Facilities", value: stats.total_facilities ?? 0 },
        { name: "Equipment", value: stats.total_equipment ?? 0 },
        { name: "Procedures", value: stats.total_procedures ?? 0 },
        { name: "Specialties", value: stats.total_specialties ?? 0 },
        { name: "Locations", value: stats.total_locations ?? 0 },
      ]
    : []

  const hasAnyData = allEntries.some((d) => d.value > 0)

  const barData = allEntries.map((d) => ({ name: d.name, count: d.value }))
  const pieData = allEntries.filter((d) => d.value > 0)

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card className="border-border/50">
        <CardHeader className="pb-4">
          <CardTitle className="text-base font-semibold">Entity Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          {hasAnyData ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={barData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(214, 20%, 90%)" />
                <XAxis
                  dataKey="name"
                  tick={{ fontSize: 12, fill: "hsl(215, 14%, 46%)" }}
                  axisLine={{ stroke: "hsl(214, 20%, 90%)" }}
                />
                <YAxis
                  tick={{ fontSize: 12, fill: "hsl(215, 14%, 46%)" }}
                  axisLine={{ stroke: "hsl(214, 20%, 90%)" }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(0, 0%, 100%)",
                    border: "1px solid hsl(214, 20%, 90%)",
                    borderRadius: "8px",
                    fontSize: "13px",
                  }}
                />
                <Bar dataKey="count" fill="hsl(217, 91%, 60%)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
              No data available. Upload a CSV to see analytics.
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="border-border/50">
        <CardHeader className="pb-4">
          <CardTitle className="text-base font-semibold">Entity Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={95}
                  paddingAngle={3}
                  dataKey="value"
                  label={({ name, percent }) =>
                    `${name} ${(percent * 100).toFixed(0)}%`
                  }
                  labelLine={false}
                >
                  {pieData.map((_entry, index) => (
                    <Cell key={index} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(0, 0%, 100%)",
                    border: "1px solid hsl(214, 20%, 90%)",
                    borderRadius: "8px",
                    fontSize: "13px",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
              No data available. Upload a CSV to see analytics.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
