"use client"

import { useEffect, useRef, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Loader2, Maximize2, Minimize2, RefreshCw } from "lucide-react"
import { api } from "@/lib/api"

interface GraphVisualizationProps {
  query?: string
  title?: string
  onRefresh?: () => void
  className?: string
  limit?: number
}

const NODE_COLORS: Record<string, string> = {
  Facility: "#3b82f6",
  Equipment: "#10b981",
  Procedure: "#f59e0b",
  Specialty: "#8b5cf6",
  Location: "#ef4444",
  Capability: "#06b6d4",
}

export function GraphVisualization({
  query,
  title = "Knowledge Graph",
  onRefresh,
  className = "",
  limit = 100,
}: GraphVisualizationProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const networkRef = useRef<any>(null)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [nodeCount, setNodeCount] = useState(0)
  const [edgeCount, setEdgeCount] = useState(0)

  useEffect(() => {
    if (!containerRef.current) return

    setIsLoading(true)
    setError(null)

    // Fetch graph data from backend
    const fetchData = query 
      ? api.queryGraphVisualization(query, limit)
      : api.graphVisualization(limit)

    fetchData
      .then((data) => {
        // Import vis-network
        import("vis-network/standalone/esm/vis-network").then(({ Network, DataSet }) => {
          try {
            // Create unique ID mapping to avoid duplicates
            const nodeIdMap = new Map<number, string>()
            const uniqueNodes = new Map<number, any>()
            const matchedNodeIds: string[] = []
            
            // Deduplicate nodes and create unique IDs
            data.nodes.forEach((node, index) => {
              if (!uniqueNodes.has(node.id)) {
                const uniqueId = `node_${index}_${node.id}`
                nodeIdMap.set(node.id, uniqueId)
                const isMatched = node.matched === true
                
                if (isMatched) {
                  matchedNodeIds.push(uniqueId)
                }
                
                // Build rich tooltip with properties
                const props = node.properties || {}
                let tooltip = `<div style="padding: 8px; font-family: system-ui;">
                  <div style="font-weight: bold; font-size: 14px; margin-bottom: 6px;">${node.label}</div>
                  <div style="font-size: 13px; color: #334155; margin-bottom: 4px;">${node.name || "Unknown"}</div>`
                
                // Add relevant properties
                if (props.capacity) tooltip += `<div style="font-size: 12px; color: #64748b;">Capacity: ${props.capacity}</div>`
                if (props.type) tooltip += `<div style="font-size: 12px; color: #64748b;">Type: ${props.type}</div>`
                if (props.operator_type) tooltip += `<div style="font-size: 12px; color: #64748b;">Operator: ${props.operator_type}</div>`
                if (props.equipment_type) tooltip += `<div style="font-size: 12px; color: #64748b;">Equipment Type: ${props.equipment_type}</div>`
                if (props.category) tooltip += `<div style="font-size: 12px; color: #64748b;">Category: ${props.category}</div>`
                if (props.data_source === 'llm') tooltip += `<div style="font-size: 11px; color: #f59e0b; margin-top: 4px;">✨ AI-extracted</div>`
                tooltip += `</div>`
                
                uniqueNodes.set(node.id, {
                  id: uniqueId,
                  label: node.name || "Unknown",
                  title: tooltip,
                  color: isMatched 
                    ? { background: NODE_COLORS[node.label] || "#64748b", border: "#fbbf24", highlight: { background: NODE_COLORS[node.label] || "#64748b", border: "#f59e0b" } }
                    : NODE_COLORS[node.label] || "#64748b",
                  shape: "dot",
                  size: isMatched ? 30 : 25,
                  borderWidth: isMatched ? 4 : 3,
                  font: {
                    size: isMatched ? 16 : 14,
                    color: "#1e293b",
                  },
                })
              }
            })

            const nodes = new DataSet(Array.from(uniqueNodes.values()))

            // Human-readable relationship labels
            const relationshipLabels: Record<string, string> = {
              HAS_EQUIPMENT: "has equipment",
              LACKS_EQUIPMENT: "lacks",
              OFFERS_PROCEDURE: "offers",
              REQUIRES_EQUIPMENT: "requires",
              LOCATED_IN: "located in",
              PROVIDES_SPECIALTY: "provides",
              LACKS_SPECIALTY: "lacks",
              HAS_CAPABILITY: "has capability",
            }
            
            const edges = new DataSet(
              data.edges.map((edge, index) => {
                const readableLabel = relationshipLabels[edge.type] || edge.type.toLowerCase().replace(/_/g, " ")
                return {
                  id: `edge_${index}`,
                  from: nodeIdMap.get(edge.source) || edge.source,
                  to: nodeIdMap.get(edge.target) || edge.target,
                  label: readableLabel,
                  title: `<div style="padding: 6px; font-family: system-ui;">
                    <div style="font-weight: bold; font-size: 12px;">${readableLabel}</div>
                    ${edge.properties?.confidence ? `<div style="font-size: 11px; color: #64748b;">Confidence: ${Math.round(edge.properties.confidence * 100)}%</div>` : ''}
                    ${edge.properties?.data_source === 'llm' ? '<div style="font-size: 11px; color: #f59e0b;">✨ AI-extracted</div>' : ''}
                  </div>`,
                  arrows: "to",
                  color: { color: "#334155" },
                  width: 3,
                  font: {
                    size: 12,
                    color: "#1e293b",
                  },
                }
              })
            )

            console.log(`📊 Loaded ${nodes.length} nodes and ${edges.length} edges`)
            setNodeCount(nodes.length)
            setEdgeCount(edges.length)

            const options = {
              nodes: {
                borderWidth: 3,
                borderWidthSelected: 4,
                shadow: true,
              },
              edges: {
                smooth: {
                  type: "dynamic",
                  roundness: 0.5,
                },
                shadow: true,
              },
              physics: {
                enabled: true,
                stabilization: {
                  iterations: 400,
                  fit: true,
                },
                barnesHut: {
                  gravitationalConstant: -20000,
                  centralGravity: 0.8, // Increased to pull disconnected components toward center
                  springLength: 150,
                  springConstant: 0.04,
                  damping: 0.2,
                  avoidOverlap: 0.5,
                },
              },
              interaction: {
                hover: true,
                navigationButtons: true,
                keyboard: true,
                tooltipDelay: 100,
              },
              layout: {
                improvedLayout: true,
                hierarchical: false,
              },
              height: isFullscreen ? "calc(100vh - 200px)" : "500px",
            }

            if (networkRef.current) {
              networkRef.current.destroy()
            }

            networkRef.current = new Network(containerRef.current!, { nodes, edges }, options)
            
            // Wait for stabilization, then zoom to matched nodes or fit all
            networkRef.current.once("stabilizationIterationsDone", () => {
              if (networkRef.current) {
                if (matchedNodeIds.length > 0) {
                  // Focus on matched nodes
                  networkRef.current.fit({
                    nodes: matchedNodeIds,
                    animation: {
                      duration: 1000,
                      easingFunction: "easeInOutQuad",
                    },
                  })
                } else {
                  // Fit all nodes
                  networkRef.current.fit({
                    animation: {
                      duration: 1000,
                      easingFunction: "easeInOutQuad",
                    },
                  })
                }
              }
            })
            
            setIsLoading(false)
          } catch (err) {
            console.error("Error creating network:", err)
            setError("Failed to create visualization")
            setIsLoading(false)
          }
        })
      })
      .catch((err) => {
        console.error("Error fetching graph data:", err)
        setError("Failed to load graph data")
        setIsLoading(false)
      })

    return () => {
      if (networkRef.current) {
        networkRef.current.destroy()
      }
    }
  }, [query, limit, isFullscreen])

  const toggleFullscreen = () => {
    setIsFullscreen((prev) => !prev)
  }

  const handleRefreshClick = () => {
    if (onRefresh) onRefresh()
  }

  return (
    <Card className={`border-border/50 shadow-sm ${isFullscreen ? "fixed inset-4 z-50 bg-background" : ""} ${className}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CardTitle className="text-base font-semibold tracking-tight">{title}</CardTitle>
            {!isLoading && !error && (
              <div className="flex gap-1.5">
                <Badge variant="secondary" className="text-xs">
                  {nodeCount} nodes
                </Badge>
                <Badge variant="secondary" className="text-xs">
                  {edgeCount} edges
                </Badge>
              </div>
            )}
          </div>
          <div className="flex gap-2">
            <Button variant="ghost" size="sm" onClick={handleRefreshClick}>
              <RefreshCw className="h-3.5 w-3.5" />
            </Button>
            <Button variant="ghost" size="sm" onClick={toggleFullscreen}>
              {isFullscreen ? <Minimize2 className="h-3.5 w-3.5" /> : <Maximize2 className="h-3.5 w-3.5" />}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {error && (
          <div className="mb-3 rounded-lg border border-destructive/30 bg-destructive/5 p-3">
            <p className="text-sm text-destructive">{error}</p>
          </div>
        )}
        <div className="relative">
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-background/80 z-10 rounded-lg">
              <div className="flex flex-col items-center gap-3">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                <p className="text-sm text-muted-foreground">Loading graph...</p>
              </div>
            </div>
          )}
          <div
            ref={containerRef}
            className="border rounded-lg bg-slate-50 dark:bg-slate-900"
            style={{ minHeight: isFullscreen ? "calc(100vh - 200px)" : "500px" }}
          />
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {Object.entries(NODE_COLORS).map(([label, color]) => (
            <div key={label} className="flex items-center gap-1.5 text-xs">
              <div className="h-3 w-3 rounded-full" style={{ backgroundColor: color }} />
              <span className="text-muted-foreground">{label}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
