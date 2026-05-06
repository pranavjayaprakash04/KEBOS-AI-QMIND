import React, { useEffect, useState, useCallback } from 'react'
import { useAuthStore } from '../../store/authStore'
import { TrapStatus, HoneypotEvent, AttackerProfile } from '../../types/deception'
import { HoneypotStatusGrid } from './components/HoneypotStatusGrid'
import { LiveEventFeed } from './components/LiveEventFeed'
import { AttackerProfileCard } from './components/AttackerProfileCard'
import { ThreatStateVisualizer } from './components/ThreatStateVisualizer'
import { WorldMapPlot } from './components/WorldMapPlot'
import { ComplianceWidget } from './components/ComplianceWidget'
import apiClient from '../../api/apiClient'

const DeceptionLayer: React.FC = () => {
  const { user, isAuthenticated } = useAuthStore()
  const [traps, setTraps] = useState<TrapStatus[]>([])
  const [events, setEvents] = useState<HoneypotEvent[]>([])
  const [profiles, setProfiles] = useState<AttackerProfile[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch trap status
  const fetchTraps = useCallback(async () => {
    try {
      const response = await apiClient.get<TrapStatus[]>('/api/v1/deception/traps')
      setTraps(response.data)
    } catch (err) {
      console.error('Failed to fetch traps:', err)
    }
  }, [])

  // Fetch live events
  const fetchEvents = useCallback(async () => {
    try {
      const response = await apiClient.get<HoneypotEvent[]>('/api/v1/deception/events/live?limit=50')
      setEvents(response.data)
    } catch (err) {
      console.error('Failed to fetch events:', err)
    }
  }, [])

  // Initial data load
  useEffect(() => {
    if (!isAuthenticated) return

    const loadData = async () => {
      setLoading(true)
      try {
        await Promise.all([fetchTraps(), fetchEvents()])
      } catch (err) {
        setError('Failed to load deception layer data')
      } finally {
        setLoading(false)
      }
    }

    loadData()

    // Poll traps every 10 seconds
    const trapInterval = setInterval(fetchTraps, 10000)

    return () => {
      clearInterval(trapInterval)
    }
  }, [isAuthenticated, fetchTraps, fetchEvents])

  // WebSocket for live events
  useEffect(() => {
    if (!isAuthenticated || !user) return

    const wsUrl = `${import.meta.env.VITE_WS_URL}/ws/threats/${user.tenant_id}`
    const ws = new WebSocket(wsUrl)

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'honeypot_event') {
          const newEvent: HoneypotEvent = {
            time: new Date().toISOString(),
            trap_type: data.trap_type,
            event_type: 'connection_attempt',
            attacker_ip: data.attacker_ip,
            enrichment: data.enrichment,
          }
          setEvents((prev) => [newEvent, ...prev.slice(0, 49)])
        }
      } catch (err) {
        console.error('WebSocket message error:', err)
      }
    }

    ws.onerror = (err) => {
      console.error('WebSocket error:', err)
    }

    return () => {
      ws.close()
    }
  }, [isAuthenticated, user])

  // Build attacker profiles from events
  useEffect(() => {
    const profileMap = new Map<string, AttackerProfile>()

    events.forEach((event) => {
      const existing = profileMap.get(event.attacker_ip)

      if (existing) {
        // Update existing profile
        if (!existing.trap_types_hit.includes(event.trap_type)) {
          existing.trap_types_hit.push(event.trap_type)
        }
        if (new Date(event.time) > new Date(existing.last_seen)) {
          existing.last_seen = event.time
          if (event.enrichment) {
            existing.enrichment = event.enrichment
          }
        }
      } else {
        // Create new profile
        profileMap.set(event.attacker_ip, {
          ip: event.attacker_ip,
          trap_types_hit: [event.trap_type],
          first_seen: event.time,
          last_seen: event.time,
          enrichment: event.enrichment || {
            threat_id: null,
            confidence: 0,
            category: 'Unknown',
            stability_score: 0,
            threat_state: {},
            mitigation: '',
            gemma_brief: '',
          },
        })
      }
    })

    // Sort by stability score (highest first)
    const sortedProfiles = Array.from(profileMap.values()).sort(
      (a, b) => (b.enrichment?.stability_score || 0) - (a.enrichment?.stability_score || 0)
    )

    setProfiles(sortedProfiles)
  }, [events])

  // Handle trap start
  const handleStartTrap = async (trapType: 'ssh' | 'http' | 'rdp') => {
    try {
      await apiClient.post(`/api/v1/deception/traps/${trapType}/start`)
      await fetchTraps()
    } catch (err) {
      setError(`Failed to start ${trapType} trap`)
    }
  }

  if (!isAuthenticated) {
    return <div className="flex items-center justify-center h-screen">Please log in...</div>
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-gray-300 rounded w-1/4"></div>
            <div className="grid grid-cols-4 gap-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-32 bg-gray-300 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        {error && (
          <div className="mb-4 p-4 bg-red-100 text-red-800 rounded">
            {error}
            <button onClick={() => setError(null)} className="ml-2 text-red-600 underline">
              Dismiss
            </button>
          </div>
        )}

        <header className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-800">Deception Layer</h1>
            <p className="text-gray-600">Cyber Deception & Honeypot Intelligence</p>
          </div>
          {import.meta.env.VITE_PQC_MODE !== 'real' && (
            <span className="px-3 py-1 bg-amber-100 text-amber-800 text-xs font-bold rounded border border-amber-300 uppercase tracking-wide">
              PQC Simulated
            </span>
          )}
        </header>

        {/* Three-column grid */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left: Trap Status */}
          <div className="lg:col-span-1">
            <HoneypotStatusGrid traps={traps} onStart={handleStartTrap} />
          </div>

          {/* Center: Live Event Feed */}
          <div className="lg:col-span-2">
            <LiveEventFeed events={events} />
          </div>

          {/* Right: Attacker Profiles */}
          <div className="lg:col-span-1 space-y-4 max-h-[800px] overflow-y-auto">
            {profiles.length === 0 ? (
              <div className="text-center text-gray-400 py-8">No attacker profiles yet</div>
            ) : (
              profiles.map((profile) => (
                <AttackerProfileCard key={profile.ip} profile={profile} />
              ))
            )}
          </div>
        </div>

        {/* World Map - Full Width */}
        <div className="mt-6">
          <WorldMapPlot events={events} />
        </div>

        {/* Threat State Visualizer + Compliance Widget */}
        <div className="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <ThreatStateVisualizer profiles={profiles} />
          </div>
          <div className="lg:col-span-1">
            <ComplianceWidget />
          </div>
        </div>
      </div>
    </div>
  )
}

export default DeceptionLayer
