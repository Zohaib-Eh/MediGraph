"use client"

import { useEffect, useRef, useState } from "react"
import "mapbox-gl/dist/mapbox-gl.css"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
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

/** Group locations that geocode to same/similar coords into clusters */
function clusterLocations(locations: GeocodedLocation[]): { center: { lat: number; lng: number }; locations: GeocodedLocation[] }[] {
  const ROUND = 4 // ~11m - treat as same point
  const groups = new Map<string, GeocodedLocation[]>()
  for (const loc of locations) {
    const key = `${loc.lat.toFixed(ROUND)}|${loc.lng.toFixed(ROUND)}`
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key)!.push(loc)
  }
  return Array.from(groups.entries()).map(([, locs]) => ({
    center: { lat: locs[0].lat, lng: locs[0].lng },
    locations: locs,
  }))
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

        const coordsResults = await Promise.all(
          merged.map((loc) => geocodeLocation(loc))
        )
        const geocoded: GeocodedLocation[] = []
        for (let i = 0; i < merged.length && !cancelled; i++) {
          const coords = coordsResults[i]
          if (coords) geocoded.push({ ...merged[i], ...coords })
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

      const clusters = clusterLocations(geocodedLocations)
      const markers: MapboxMarker[] = []

      clusters.forEach((cluster) => {
        const count = cluster.locations.length
        const size = count > 1 ? 32 : 24
        const el = document.createElement("div")
        el.innerHTML = count > 1
          ? `<div style="width:${size}px;height:${size}px;background:hsl(var(--chart-4));border:2px solid white;border-radius:50%;box-shadow:0 2px 4px rgba(0,0,0,0.3);cursor:pointer;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:12px;color:white;font-family:system-ui;">${count}</div>`
          : '<div style="width:24px;height:24px;background:hsl(var(--chart-4));border:2px solid white;border-radius:50%;box-shadow:0 2px 4px rgba(0,0,0,0.3);cursor:pointer;"></div>'

        const itemsHtml = cluster.locations
          .map((loc) => {
            const facilities = loc.facilities?.length ? loc.facilities.join(", ") : ""
            const line = facilities ? `${escapeHtml(loc.name)} — ${escapeHtml(facilities)}` : escapeHtml(loc.name)
            return `<li style="margin-bottom:6px;font-size:13px;">${line}</li>`
          })
          .join("")
        const popup = new mapboxgl.Popup({ offset: 25, maxWidth: "320px" }).setHTML(
          `<div style="padding:10px;font-family:system-ui;max-height:280px;overflow-y:auto;">
            <div style="font-weight:600;font-size:14px;margin-bottom:8px;">${count} location${count > 1 ? "s" : ""}</div>
            <ul style="margin:0;padding-left:18px;list-style:disc;">${itemsHtml}</ul>
          </div>`
        )
        const marker = new mapboxgl.Marker(el)
          .setLngLat([cluster.center.lng, cluster.center.lat])
          .setPopup(popup)
          .addTo(map)
        markers.push(marker)
      })
      markersRef.current = markers

      if (geocodedLocations.length > 0) {
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
          <CardTitle className="text-base font-semibold">{title}</CardTitle>
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
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CardTitle className="text-base font-semibold">{title}</CardTitle>
            {!isLoading && !error && geocodedLocations.length > 0 && (
              <Badge variant="secondary" className="text-xs">
                {geocodedLocations.length} locations
              </Badge>
            )}
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
                <p className="text-sm text-muted-foreground">Loading map...</p>
              </div>
            </div>
          )}
          {!isLoading && !error && geocodedLocations.length === 0 && (
            <div className="absolute bottom-4 left-4 right-4 z-10 rounded-lg border border-border bg-background/95 px-4 py-3 text-center text-sm text-muted-foreground shadow-sm">
              No locations found. Upload CSV files with address columns (address_city, address_country, etc.) and build the graph.
            </div>
          )}
          <div
            ref={containerRef}
            className="border rounded-lg bg-slate-50 dark:bg-slate-900 overflow-hidden"
            style={{ minHeight: "500px" }}
          />
        </div>
      </CardContent>
    </Card>
  )
}
