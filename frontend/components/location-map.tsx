"use client"

import { useEffect, useRef, useState } from "react"
import "mapbox-gl/dist/mapbox-gl.css"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader2, MapPin } from "lucide-react"
import { api, type QueryLocation } from "@/lib/api"
import type { Map as MapboxMap, Marker as MapboxMarker } from "mapbox-gl"

interface LocationMapProps {
  query?: string
  title?: string
  className?: string
}

interface GeocodedLocation extends QueryLocation {
  lng: number
  lat: number
}

const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN

function escapeHtml(s: string): string {
  const div = document.createElement("div")
  div.textContent = s
  return div.innerHTML
}

async function geocodeLocation(loc: QueryLocation): Promise<{ lng: number; lat: number } | null> {
  if (!MAPBOX_TOKEN) return null
  const parts = [loc.city, loc.state_or_region, loc.country].filter((p) => p && p !== "Unknown")
  const searchQuery = parts.length > 0 ? parts.join(", ") : loc.name
  const countryParam = loc.country_code ? `&country=${loc.country_code}` : "&country=GH"
  const url = `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(searchQuery)}.json?access_token=${MAPBOX_TOKEN}&limit=1${countryParam}`
  try {
    const res = await fetch(url)
    const data = await res.json()
    const center = data.features?.[0]?.center
    if (center) return { lng: center[0], lat: center[1] }
  } catch {
    // ignore geocoding errors
  }
  return null
}

export function LocationMap({ query = "", title = "Locations Map", className = "" }: LocationMapProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<MapboxMap | null>(null)
  const markersRef = useRef<MapboxMarker[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [geocodedLocations, setGeocodedLocations] = useState<GeocodedLocation[]>([])

  useEffect(() => {
    let cancelled = false

    async function loadMap() {
      if (!MAPBOX_TOKEN) {
        setError("Mapbox token not configured. Set NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN in .env.local")
        setIsLoading(false)
        return
      }

      setError(null)
      setIsLoading(true)
      setGeocodedLocations([])

      try {
        // Fetch from BOTH: knowledge graph + source CSVs
        const [graphRes, sourceRes] = await Promise.all([
          api.queryLocations(query, 30),
          api.sourceLocations(query, 50),
        ])

        const graphLocs = graphRes.locations || []
        const sourceLocs = sourceRes.locations || []

        // Merge and dedupe by (name, city) - prefer source (richer addresses for geocoding)
        const seen = new Set<string>()
        const merged: QueryLocation[] = []
        for (const loc of sourceLocs) {
          const key = `${loc.name}|${loc.city || ""}|${loc.state_or_region || ""}`
          if (!seen.has(key)) {
            seen.add(key)
            merged.push(loc)
          }
        }
        for (const loc of graphLocs) {
          const key = `${loc.name}|${loc.city || ""}|${loc.state_or_region || ""}`
          if (!seen.has(key)) {
            seen.add(key)
            merged.push(loc)
          }
        }

        if (cancelled || merged.length === 0) {
          setIsLoading(false)
          if (merged.length === 0 && !cancelled) setGeocodedLocations([])
          return
        }

        const geocoded: GeocodedLocation[] = []
        for (const loc of merged) {
          const coords = await geocodeLocation(loc)
          if (coords && !cancelled) geocoded.push({ ...loc, ...coords })
        }

        if (cancelled) return
        setGeocodedLocations(geocoded)
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load locations")
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }

    loadMap()
    return () => { cancelled = true }
  }, [query])

  useEffect(() => {
    if (!containerRef.current || !MAPBOX_TOKEN) return

    let cancelled = false
    import("mapbox-gl").then((mb) => {
      const mapboxgl = mb.default
      if (cancelled || !containerRef.current) return
      mapboxgl.accessToken = MAPBOX_TOKEN

      if (mapRef.current) {
        markersRef.current.forEach((m) => m.remove())
        markersRef.current = []
        mapRef.current.remove()
        mapRef.current = null
      }

      // Default center: Ghana (most healthcare data is from Ghana)
      const center: [number, number] = geocodedLocations.length > 0
        ? [geocodedLocations[0].lng, geocodedLocations[0].lat]
        : [-1.6163, 6.6667] // Ghana center
      const zoom = geocodedLocations.length > 0 ? 6 : 5

      const map = new mapboxgl.Map({
        container: containerRef.current,
        style: "mapbox://styles/mapbox/light-v11",
        center,
        zoom,
      })
      mapRef.current = map

      const markers: MapboxMarker[] = []
      geocodedLocations.forEach((loc) => {
        const el = document.createElement("div")
        el.innerHTML = '<div style="width:24px;height:24px;background:#ef4444;border:2px solid white;border-radius:50%;box-shadow:0 2px 4px rgba(0,0,0,0.3);cursor:pointer;"></div>'
        const facilitiesStr = loc.facilities?.length
          ? escapeHtml(loc.facilities.slice(0, 3).join(", ") + (loc.facilities.length > 3 ? "..." : ""))
          : ""
        const popup = new mapboxgl.Popup({ offset: 25 }).setHTML(
          `<div style="padding:8px;font-family:system-ui;min-width:140px;">
            <div style="font-weight:600;font-size:14px;margin-bottom:4px;">${escapeHtml(loc.name)}</div>
            ${facilitiesStr ? `<div style="font-size:12px;color:#64748b;">Facilities: ${facilitiesStr}</div>` : ""}
          </div>`
        )
        const marker = new mapboxgl.Marker(el).setLngLat([loc.lng, loc.lat]).setPopup(popup).addTo(map)
        markers.push(marker)
      })
      markersRef.current = markers

      if (geocodedLocations.length > 1) {
        const bounds = new mapboxgl.LngLatBounds()
        geocodedLocations.forEach((loc) => bounds.extend([loc.lng, loc.lat]))
        map.fitBounds(bounds, { padding: 50, maxZoom: 12 })
      }
    })

    return () => {
      cancelled = true
      markersRef.current.forEach((m) => m.remove())
      markersRef.current = []
      if (mapRef.current) {
        mapRef.current.remove()
        mapRef.current = null
      }
    }
  }, [geocodedLocations])

  if (!MAPBOX_TOKEN) {
    return (
      <Card className={`border-border/50 ${className}`}>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <MapPin className="h-4 w-4 text-primary" />
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-lg border border-dashed bg-muted/30 p-6 text-center text-sm text-muted-foreground">
            Set <code className="rounded bg-muted px-1">NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN</code> in{" "}
            <code className="rounded bg-muted px-1">.env.local</code> to enable the map.
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={`border-border/50 ${className}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <MapPin className="h-4 w-4 text-primary" />
          <CardTitle className="text-base">{title}</CardTitle>
          {!isLoading && !error && geocodedLocations.length > 0 && (
            <span className="text-xs text-muted-foreground">({geocodedLocations.length} locations)</span>
          )}
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
            <div className="absolute inset-0 z-10 flex items-center justify-center rounded-lg bg-background/80">
              <div className="flex flex-col items-center gap-3">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                <p className="text-sm text-muted-foreground">Loading map...</p>
              </div>
            </div>
          )}
          {!isLoading && !error && geocodedLocations.length === 0 && (
            <div className="absolute bottom-4 left-4 right-4 z-10 rounded-md border bg-background/95 px-3 py-2 text-center text-sm text-muted-foreground shadow-sm">
              No locations found. Upload CSV files with address columns (address_city, address_country, etc.) and build the graph.
            </div>
          )}
          <div
            ref={containerRef}
            className="border rounded-lg bg-slate-50 dark:bg-slate-900 overflow-hidden"
            style={{ minHeight: "350px" }}
          />
        </div>
      </CardContent>
    </Card>
  )
}
