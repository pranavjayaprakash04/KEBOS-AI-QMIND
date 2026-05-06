import React, { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import { HoneypotEvent } from '../../../types/deception'

interface WorldMapPlotProps {
  events: HoneypotEvent[]
}

interface GeoIPCache {
  [ip: string]: { lat: number; lon: number; country: string; city: string }
}

interface MapData {
  type: string
  features: Array<{
    type: string
    properties: { name: string }
    geometry: {
      type: string
      coordinates: number[][][][]
    }
  }>
}

export const WorldMapPlot: React.FC<WorldMapPlotProps> = ({ events }) => {
  const svgRef = useRef<SVGSVGElement>(null)
  const [worldData, setWorldData] = useState<MapData | null>(null)
  const [geoIPCache, setGeoIPCache] = useState<GeoIPCache>({})
  const [tooltip, setTooltip] = useState<{
    x: number
    y: number
    content: string
  } | null>(null)

  // Load world atlas data
  useEffect(() => {
    const loadWorldData = async () => {
      try {
        const response = await fetch(
          'https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json'
        )
        const data = await response.json()
        setWorldData(data as MapData)
      } catch (err) {
        console.error('Failed to load world atlas:', err)
      }
    }

    loadWorldData()
  }, [])

  // Fetch GeoIP data for unique IPs
  useEffect(() => {
    const uniqueIPs = Array.from(new Set(events.map((e) => e.attacker_ip)))

    uniqueIPs.forEach(async (ip) => {
      if (geoIPCache[ip]) return

      try {
        const response = await fetch(
          `https://ip-api.com/json/${ip}?fields=lat,lon,country,city`
        )
        if (response.ok) {
          const data = await response.json()
          if (data.lat && data.lon) {
            setGeoIPCache((prev) => ({
              ...prev,
              [ip]: {
                lat: data.lat,
                lon: data.lon,
                country: data.country || 'Unknown',
                city: data.city || 'Unknown',
              },
            }))
          }
        }
      } catch {
        // Silently fail - skip if API fails
      }
    })
  }, [events, geoIPCache])

  // Calculate hit counts per IP
  const ipHitCounts = events.reduce((acc, event) => {
    acc[event.attacker_ip] = (acc[event.attacker_ip] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  // Get attacker profiles with enrichment
  const attackerProfiles = events.reduce((acc, event) => {
    if (!acc[event.attacker_ip]) {
      acc[event.attacker_ip] = {
        ip: event.attacker_ip,
        trap_types: new Set<string>(),
        category: event.enrichment?.category || 'Unknown',
      }
    }
    acc[event.attacker_ip].trap_types.add(event.trap_type)
    return acc
  }, {} as Record<string, { ip: string; trap_types: Set<string>; category: string }>)

  // Draw the map
  useEffect(() => {
    if (!svgRef.current || !worldData) return

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const width = 800
    const height = 400

    svg.attr('viewBox', `0 0 ${width} ${height}`)

    // Use Natural Earth projection
    const projection = d3
      .geoNaturalEarth1()
      .scale(140)
      .translate([width / 2, height / 2])

    const path = d3.geoPath().projection(projection)

    // Draw countries
    svg
      .append('g')
      .selectAll('path')
      .data(worldData.features)
      .enter()
      .append('path')
      .attr('d', path as any)
      .attr('fill', '#1a1a2e')
      .attr('stroke', '#2d2d4e')
      .attr('stroke-width', 0.5)

    // Plot attacker IPs
    const plottedIPs = Object.keys(geoIPCache)

    if (plottedIPs.length > 0) {
      const hitCounts = plottedIPs.map((ip) => ipHitCounts[ip] || 1)
      const maxHits = Math.max(...hitCounts)
      const minHits = Math.min(...hitCounts)

      const radiusScale = d3
        .scaleLinear()
        .domain([minHits, maxHits])
        .range([4, 16])

      svg
        .append('g')
        .selectAll('circle')
        .data(plottedIPs)
        .enter()
        .append('circle')
        .attr('cx', (ip: string) => {
          const coords = projection([geoIPCache[ip].lon, geoIPCache[ip].lat])
          return coords ? coords[0] : 0
        })
        .attr('cy', (ip: string) => {
          const coords = projection([geoIPCache[ip].lon, geoIPCache[ip].lat])
          return coords ? coords[1] : 0
        })
        .attr('r', (ip: string) => radiusScale(ipHitCounts[ip] || 1))
        .attr('fill', '#ef4444')
        .attr('opacity', 0.8)
        .attr('stroke', '#7f1d1d')
        .attr('stroke-width', 1)
        .style('cursor', 'pointer')
        .on('mouseenter', (event: MouseEvent, ip: string) => {
          const profile = attackerProfiles[ip]
          const geo = geoIPCache[ip]
          const hits = ipHitCounts[ip] || 0

          setTooltip({
            x: event.pageX + 10,
            y: event.pageY - 10,
            content: `${ip}
${geo.city}, ${geo.country}
Hits: ${hits}
Category: ${profile?.category || 'Unknown'}
Traps: ${Array.from(profile?.trap_types || []).join(', ')}`,
          })
        })
        .on('mouseleave', () => {
          setTooltip(null)
        })
    }
  }, [worldData, geoIPCache, events, ipHitCounts, attackerProfiles])

  const hasAttackers = Object.keys(geoIPCache).length > 0

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
      <h2 className="text-lg font-semibold text-gray-800 mb-4">Attacker Geography</h2>

      <div className="relative">
        <svg
          ref={svgRef}
          className="w-full h-auto"
          style={{ minHeight: '300px' }}
        />

        {!hasAttackers && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-50 bg-opacity-90">
            <p className="text-gray-500">No attacker activity yet</p>
          </div>
        )}
      </div>

      {tooltip && (
        <div
          className="fixed z-50 bg-gray-900 text-white text-xs p-2 rounded shadow-lg pointer-events-none whitespace-pre-line"
          style={{ left: tooltip.x, top: tooltip.y }}
        >
          {tooltip.content}
        </div>
      )}
    </div>
  )
}

export default WorldMapPlot
