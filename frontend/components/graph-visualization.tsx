"use client"

import { useEffect, useRef, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Loader2, Maximize2, Minimize2, RefreshCw } from "lucide-react"

interface GraphVisualizationProps {
  query?: string // Optional Cypher query to filter the graph
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
  const vizRef = useRef<HTMLDivElement>(null)
  const neovisRef = useRef<any>(null)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [nodeCount, setNodeCount] = useState(0)
  const [edgeCount, setEdgeCount] = useState(0)

  useEffect(() => {
    if (!vizRef.current) return

    // Clear any existing content
    vizRef.current.innerHTML = ""
    const containerId = `neovis-${Math.random().toString(36).substr(2, 9)}`
    vizRef.current.id = containerId

    setIsLoading(true)
    setError(null)

    // Small delay to ensure DOM is ready
    const timer = setTimeout(() => {
      // Dynamically import NeoVis
      import("neovis.js")
        .then(({ default: NeoVis }) => {
          try {
            // Verify container exists
            const container = document.getElementById(containerId)
            if (!container) {
              throw new Error("Container not found")
            }

            // Build the Cypher query - return path for proper ID extraction
            const cypherQuery = query
              ? `MATCH p=(n)-[r]->(m) 
                 WHERE toLower(n.name) CONTAINS toLower('${query.split(" ")[0]}')
                    OR toLower(m.name) CONTAINS toLower('${query.split(" ")[0]}')
                 RETURN p LIMIT 300`
              : `MATCH p=(n)-[r]->(m) RETURN p LIMIT 300`

          const config = {
            containerId: containerId,
            neo4j: {
              serverUrl: "bolt://localhost:7687",
              serverUser: "neo4j",
              serverPassword: "password",
              driverConfig: {
                encrypted: false,
              },
            },
            consoleLog: true, // Enable NeoVis debug logging
            visConfig: {
              nodes: {
                shape: "dot",
                size: 25,
                font: {
                  size: 14,
                  color: "#1e293b",
                  background: "rgba(255, 255, 255, 0.95)",
                  strokeWidth: 1,
                  strokeColor: "#e2e8f0",
                },
                borderWidth: 3,
                borderWidthSelected: 4,
                shadow: {
                  enabled: true,
                  color: "rgba(0,0,0,0.15)",
                  size: 8,
                  x: 2,
                  y: 2,
                },
              },
              edges: {
                arrows: {
                  to: { enabled: true, scaleFactor: 1.2, type: "arrow" },
                },
                color: {
                  color: "#334155",
                  highlight: "#0f172a",
                  hover: "#1e293b",
                },
                font: {
                  size: 12,
                  color: "#1e293b",
                  background: "rgba(255, 255, 255, 0.95)",
                  strokeWidth: 2,
                  strokeColor: "#ffffff",
                  align: "horizontal",
                },
                smooth: {
                  enabled: true,
                  type: "dynamic",
                  roundness: 0.5,
                },
                width: 3,
                selectionWidth: 5,
                hoverWidth: 4,
                shadow: {
                  enabled: true,
                  color: "rgba(0,0,0,0.1)",
                  size: 5,
                  x: 1,
                  y: 1,
                },
              },
              physics: {
                enabled: true,
                stabilization: {
                  enabled: true,
                  iterations: 300,
                  fit: true,
                },
                barnesHut: {
                  gravitationalConstant: -15000,
                  centralGravity: 0.2,
                  springLength: 200,
                  springConstant: 0.05,
                  damping: 0.15,
                  avoidOverlap: 0.5,
                },
              },
              interaction: {
                hover: true,
                navigationButtons: true,
                keyboard: {
                  enabled: true,
                  bindToWindow: false,
                },
                tooltipDelay: 100,
                hideEdgesOnDrag: false,
                hideEdgesOnZoom: false,
              },
              height: isFullscreen ? "calc(100vh - 200px)" : "500px",
            },
            labels: {
              Facility: {
                label: "name",
                [NeoVis.NEOVIS_ADVANCED_CONFIG]: {
                  static: {
                    color: NODE_COLORS.Facility,
                  },
                },
              },
              Equipment: {
                label: "name",
                [NeoVis.NEOVIS_ADVANCED_CONFIG]: {
                  static: {
                    color: NODE_COLORS.Equipment,
                  },
                },
              },
              Procedure: {
                label: "name",
                [NeoVis.NEOVIS_ADVANCED_CONFIG]: {
                  static: {
                    color: NODE_COLORS.Procedure,
                  },
                },
              },
              Specialty: {
                label: "name",
                [NeoVis.NEOVIS_ADVANCED_CONFIG]: {
                  static: {
                    color: NODE_COLORS.Specialty,
                  },
                },
              },
              Location: {
                label: "name",
                [NeoVis.NEOVIS_ADVANCED_CONFIG]: {
                  static: {
                    color: NODE_COLORS.Location,
                  },
                },
              },
              Capability: {
                label: "name",
                [NeoVis.NEOVIS_ADVANCED_CONFIG]: {
                  static: {
                    color: NODE_COLORS.Capability,
                  },
                },
              },
            },
            relationships: {
              HAS_EQUIPMENT: { value: "type" },
              LACKS_EQUIPMENT: { value: "type" },
              OFFERS_PROCEDURE: { value: "type" },
              REQUIRES_EQUIPMENT: { value: "type" },
              LOCATED_IN: { value: "type" },
              PROVIDES_SPECIALTY: { value: "type" },
              LACKS_SPECIALTY: { value: "type" },
              HAS_CAPABILITY: { value: "type" },
            },
          }

          const viz = new NeoVis(config as any)
          neovisRef.current = viz
          
          viz.registerOnEvent("completed", (e: any) => {
            console.log("NeoVis completed:", e)
            console.log("Record count:", e.recordCount)
            
            // Wait a bit for network to be fully initialized
            setTimeout(() => {
              try {
                console.log("Accessing viz.network getter")
                const network = (viz as any).network // This is a getter
                console.log("Network from getter:", network)
                
                if (network && network.body && network.body.data) {
                  const nodesData = network.body.data.nodes
                  const edgesData = network.body.data.edges
                  console.log("Nodes data:", nodesData)
                  console.log("Edges data:", edgesData)
                  
                  // DataSet objects have a .length property directly
                  const nodeCount = nodesData.length || 0
                  const edgeCount = edgesData.length || 0
                  
                  console.log(`✅ Network has ${nodeCount} nodes and ${edgeCount} edges`)
                  setNodeCount(nodeCount)
                  setEdgeCount(edgeCount)
                  
                  if (edgeCount === 0) {
                    console.warn("⚠️ WARNING: No edges in network! Edges are missing.")
                  } else if (edgeCount === 1) {
                    console.warn("⚠️ WARNING: Only 1 edge found! Expected ~128 edges.")
                    const allEdges = edgesData.get()
                    console.log("Edge data (full):", allEdges)
                    console.log("First edge details:", JSON.stringify(allEdges[0], null, 2))
                  } else {
                    console.log("🎉 Edges successfully loaded!")
                  }
                } else {
                  console.warn("Network structure not as expected")
                  console.log("network.body:", network?.body)
                  setNodeCount(e.recordCount || 0)
                  setEdgeCount(0)
                }
              } catch (err) {
                console.error("Error checking network data:", err)
                setNodeCount(e.recordCount || 0)
                setEdgeCount(0)
              }
              
              setIsLoading(false)
            }, 1000) // Increased to 1 second to ensure network is ready
          })

          viz.registerOnEvent("error", (e: any) => {
            console.error("NeoVis error:", e)
            setError("Failed to connect to Neo4j. Make sure the database is running.")
            setIsLoading(false)
          })

          // Use renderWithCypher instead of render()
          console.log("Rendering with Cypher:", cypherQuery)
          viz.renderWithCypher(cypherQuery)
        } catch (err) {
          console.error("Visualization error:", err)
          setError(`Failed to initialize visualization: ${err}`)
          setIsLoading(false)
        }
      })
      .catch((err) => {
        console.error("Failed to load neovis.js:", err)
        setError("Failed to load visualization library")
        setIsLoading(false)
      })
    }, 100) // 100ms delay to ensure DOM is ready

    return () => {
      clearTimeout(timer)
      if (neovisRef.current) {
        try {
          neovisRef.current.clearNetwork()
        } catch (e) {
          // Ignore cleanup errors
        }
      }
    }
  }, [query, limit, isFullscreen])

  const toggleFullscreen = () => {
    setIsFullscreen((prev) => !prev)
  }

  const handleRefreshClick = () => {
    if (onRefresh) {
      onRefresh()
    }
    // Reload visualization
    if (neovisRef.current) {
      setIsLoading(true)
      neovisRef.current.reload()
    }
  }

  return (
    <Card className={`border-border/50 ${isFullscreen ? "fixed inset-4 z-50 bg-background" : ""} ${className}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CardTitle className="text-base font-semibold">{title}</CardTitle>
            {!isLoading && !error && (
              <div className="flex gap-1.5">
                <Badge variant="secondary" className="text-xs">
                  ~{nodeCount} nodes
                </Badge>
                <Badge variant="secondary" className="text-xs">
                  ~{edgeCount} edges
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
            <p className="text-xs text-muted-foreground mt-1">
              Make sure Neo4j is running on localhost:7687 with credentials neo4j/password
            </p>
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
            ref={vizRef}
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
