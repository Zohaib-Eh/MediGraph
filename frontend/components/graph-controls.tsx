"use client"

import { cn } from "@/lib/utils"

import { useState } from "react"
import { RefreshCw, Trash2, Network } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { api } from "@/lib/api"

interface GraphControlsProps {
  onRefresh: () => Promise<void> | void
  hasUploadResult: boolean
}

export function GraphControls({ onRefresh, hasUploadResult }: GraphControlsProps) {
  const [clearExisting, setClearExisting] = useState(true)
  const [building, setBuilding] = useState(false)
  const [clearing, setClearing] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [clearDialogOpen, setClearDialogOpen] = useState(false)
  const [message, setMessage] = useState<{ text: string; type: "success" | "error" } | null>(null)

  const handleBuildGraph = async () => {
    setBuilding(true)
    setMessage(null)
    try {
      const result = await api.buildGraph(clearExisting)
      setMessage({ text: result.message || "Graph built successfully", type: "success" })
      onRefresh()
    } catch (err) {
      setMessage({ text: err instanceof Error ? err.message : "Build failed", type: "error" })
    } finally {
      setBuilding(false)
    }
  }

  const handleClearGraph = async () => {
    setClearing(true)
    setMessage(null)
    try {
      const result = await api.clearGraph()
      setMessage({ text: result.message || "Graph cleared", type: "success" })
      setClearDialogOpen(false)
      onRefresh()
    } catch (err) {
      setMessage({ text: err instanceof Error ? err.message : "Clear failed", type: "error" })
    } finally {
      setClearing(false)
    }
  }

  return (
    <Card className="border-border/50 shadow-sm">
      <CardHeader className="pb-4">
        <CardTitle className="text-base font-semibold">Graph Controls</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <Switch
            id="clear-existing"
            checked={clearExisting}
            onCheckedChange={setClearExisting}
          />
          <Label htmlFor="clear-existing" className="text-sm text-foreground">
            Clear existing data first
          </Label>
        </div>

        <Button
          onClick={handleBuildGraph}
          disabled={building || !hasUploadResult}
          className="w-full"
        >
          {building ? (
            <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Network className="mr-2 h-4 w-4" />
          )}
          {building ? "Building Graph..." : "Build Knowledge Graph"}
        </Button>

        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={refreshing}
            onClick={async () => {
              setRefreshing(true)
              try {
                await onRefresh()
              } finally {
                setRefreshing(false)
              }
            }}
            className="flex-1"
          >
            <RefreshCw className={cn("mr-2 h-3.5 w-3.5", refreshing && "animate-spin")} />
            {refreshing ? "Refreshing..." : "Refresh Stats"}
          </Button>

          <Dialog open={clearDialogOpen} onOpenChange={setClearDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm" className="flex-1 text-destructive hover:text-destructive bg-transparent">
                <Trash2 className="mr-2 h-3.5 w-3.5" />
                Clear All Data
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Clear All Graph Data</DialogTitle>
                <DialogDescription>
                  This action will permanently remove all nodes and relationships from the Neo4j graph. This cannot be undone.
                </DialogDescription>
              </DialogHeader>
              <DialogFooter>
                <Button variant="outline" onClick={() => setClearDialogOpen(false)}>
                  Cancel
                </Button>
                <Button variant="destructive" onClick={handleClearGraph} disabled={clearing}>
                  {clearing ? "Clearing..." : "Yes, Clear All Data"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>

        {message && (
          <div
            className={`rounded-lg border p-3 text-sm ${
              message.type === "success"
                ? "border-[hsl(var(--success))]/30 bg-[hsl(var(--success))]/5 text-[hsl(var(--success))]"
                : "border-destructive/30 bg-destructive/5 text-destructive"
            }`}
          >
            {message.text}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
