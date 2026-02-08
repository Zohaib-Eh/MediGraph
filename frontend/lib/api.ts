const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export interface GraphStats {
  total_facilities: number
  total_equipment: number
  total_procedures: number
  total_specialties: number
  total_locations: number
  total_capabilities: number
  total_relationships: number
}

export interface UploadResult {
  message: string
  total_entities: number
  breakdown: Record<string, number>
  sample_facilities: Array<{
    name: string
    type: string
    location: string
  }>
  details?: Record<string, unknown>
}

export interface QueryResult {
  answer: string
  trace?: Record<string, unknown>
  citations?: Array<{
    source: string
    text: string
  }>
}

export interface HealthStatus {
  status: string
  neo4j: string
  api: string
}

export interface AnalysisResult {
  results: Array<Record<string, unknown>>
  summary?: string
}

export interface GraphNode {
  id: number
  label: string
  name: string
  properties: Record<string, unknown>
}

export interface GraphEdge {
  id: number
  source: number
  target: number
  type: string
  properties: Record<string, unknown>
}

export interface GraphVisualizationData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export interface QueryLocation {
  name: string
  city?: string
  state_or_region?: string
  country?: string
  country_code?: string
  facilities?: string[]
}

const DEBUG = process.env.NODE_ENV === "development"

async function apiFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`
  if (DEBUG) console.debug("[API]", url)
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        ...(options?.headers || {}),
      },
    })

    if (!res.ok) {
      const errorText = await res.text().catch(() => "Unknown error")
      if (DEBUG) console.error("[API] Error", res.status, errorText)
      throw new Error(`API Error (${res.status}): ${errorText}`)
    }

    const json = await res.json()
    return json
  } catch (err) {
    if (DEBUG) console.error("[API] Fetch error", endpoint, err)
    throw err
  }
}

export const api = {
  health: () => apiFetch<HealthStatus>("/health"),

  stats: () => apiFetch<GraphStats>("/stats"),

  upload: async (file: File) => {
    const formData = new FormData()
    formData.append("file", file)
    return apiFetch<UploadResult>("/upload", {
      method: "POST",
      body: formData,
    })
  },

  buildGraph: (clearExisting = false) =>
    apiFetch<{ message: string }>(`/build-graph?clear_existing=${clearExisting}`, {
      method: "POST",
    }),

  query: (query: string, showTrace = false) =>
    apiFetch<QueryResult>("/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, show_trace: showTrace }),
    }),

  clearGraph: () =>
    apiFetch<{ message: string }>("/clear-graph", { method: "DELETE" }),

  medicalDeserts: () => apiFetch<AnalysisResult>("/analysis/medical-deserts"),

  equipmentGaps: () => apiFetch<AnalysisResult>("/analysis/equipment-gaps"),

  inconsistencies: () => apiFetch<AnalysisResult>("/analysis/inconsistencies"),

  graphVisualization: (limit = 100) =>
    apiFetch<GraphVisualizationData>(`/graph/visualization?limit=${limit}`),

  queryGraphVisualization: (query: string, limit = 50) =>
    apiFetch<GraphVisualizationData>(
      `/graph/query-visualization?query=${encodeURIComponent(query)}&limit=${limit}`
    ),

  queryLocations: (query: string = "", limit = 50) =>
    apiFetch<{ locations: QueryLocation[] }>(
      `/graph/query-locations?query=${encodeURIComponent(query)}&limit=${limit}`
    ),

  sourceLocations: (query: string = "", limit = 100) =>
    apiFetch<{ locations: QueryLocation[] }>(
      `/sources/locations?query=${encodeURIComponent(query)}&limit=${limit}`
    ),
}
