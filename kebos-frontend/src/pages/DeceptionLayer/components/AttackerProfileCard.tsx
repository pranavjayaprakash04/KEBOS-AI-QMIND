import React, { useState, useEffect } from 'react'
import { AttackerProfile, TrapType } from '../../../types/deception'

interface AttackerProfileCardProps {
  profile: AttackerProfile
}

const TRAP_BADGES: Record<TrapType, { label: string; color: string }> = {
  ssh: { label: 'SSH', color: 'bg-blue-100 text-blue-800' },
  http: { label: 'HTTP', color: 'bg-amber-100 text-amber-800' },
  rdp: { label: 'RDP', color: 'bg-purple-100 text-purple-800' },
}

interface GeoIPData {
  country?: string
  countryCode?: string
}

const COUNTRY_FLAGS: Record<string, string> = {
  'US': '🇺🇸', 'CN': '🇨🇳', 'RU': '🇷🇺', 'IN': '🇮🇳', 'BR': '🇧🇷',
  'GB': '🇬🇧', 'DE': '🇩🇪', 'FR': '🇫🇷', 'JP': '🇯🇵', 'KR': '🇰🇷',
  'KP': '🇰🇵', 'IR': '🇮🇷', 'PK': '🇵🇰', 'BD': '🇧🇩', 'LK': '🇱🇰',
  'NP': '🇳🇵', 'MY': '🇲🇾', 'SG': '🇸🇬', 'TH': '🇹🇭', 'VN': '🇻🇳',
  'ID': '🇮🇩', 'PH': '🇵🇭', 'TW': '🇹🇼', 'HK': '🇭🇰', 'UA': '🇺🇦',
}

export const AttackerProfileCard: React.FC<AttackerProfileCardProps> = ({ profile }) => {
  const [geoData, setGeoData] = useState<GeoIPData | null>(null)
  const [expanded, setExpanded] = useState(false)

  useEffect(() => {
    // Fetch GeoIP data once per IP
    const fetchGeoIP = async () => {
      try {
        const response = await fetch(`https://ip-api.com/json/${profile.ip}?fields=country,countryCode`)
        if (response.ok) {
          const data = await response.json()
          if (data.country) {
            setGeoData(data)
          }
        }
      } catch {
        // Silently fail - don't block rendering
      }
    }

    fetchGeoIP()
  }, [profile.ip])

  const enrichment = profile.enrichment
  const stability = enrichment?.stability_score || 0

  // Determine stability color
  const stabilityColor = stability >= 0.72
    ? 'bg-red-500'
    : stability >= 0.3
    ? 'bg-amber-500'
    : 'bg-green-500'

  const isAutoResponse = stability >= 0.72
  const isFallback = enrichment?.fallback

  // Get flag emoji
  const flag = geoData?.countryCode ? (COUNTRY_FLAGS[geoData.countryCode] || '🌍') : '🌍'

  return (
    <div className={`bg-white rounded-lg shadow-md p-4 border-2 transition-all ${
      isAutoResponse ? 'border-red-500 shadow-red-100' : 'border-gray-200'
    }`}>
      {/* Header with IP and country */}
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-mono text-lg font-bold text-gray-800">{profile.ip}</h3>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-xl">{flag}</span>
            <span className="text-sm text-gray-600">{geoData?.country || 'Unknown'}</span>
          </div>
        </div>

        {isAutoResponse && (
          <div className="bg-red-100 text-red-800 text-xs font-bold px-3 py-1 rounded">
            AUTO-RESPONSE TRIGGERED
          </div>
        )}
      </div>

      {/* Trap types hit */}
      <div className="mt-3 flex flex-wrap gap-1">
        {profile.trap_types_hit.map((trapType) => (
          <span
            key={trapType}
            className={`px-2 py-1 text-xs font-medium rounded ${TRAP_BADGES[trapType].color}`}
          >
            {TRAP_BADGES[trapType].label}
          </span>
        ))}
      </div>

      {/* Category and confidence */}
      {enrichment && (
        <div className="mt-3 flex items-center gap-2">
          <span className="text-sm text-gray-600">{enrichment.category}</span>
          <span className="text-sm font-semibold text-gray-800">
            {(enrichment.confidence * 100).toFixed(0)}%
          </span>
        </div>
      )}

      {/* Stability score bar */}
      {enrichment && (
        <div className="mt-3">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>Adversarial Stability</span>
            <span>{(stability * 100).toFixed(0)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all ${stabilityColor}`}
              style={{ width: `${stability * 100}%` }}
            />
          </div>
        </div>
      )}

      {/* Gemma brief or fallback */}
      {isFallback ? (
        <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded">
          <p className="text-sm text-amber-800">⚠️ Manual review required</p>
          <p className="text-xs text-amber-600 mt-1">QMind enrichment unavailable</p>
        </div>
      ) : enrichment?.gemma_brief && (
        <div className="mt-3">
          <p className={`text-sm text-gray-700 ${expanded ? '' : 'line-clamp-2'}`}>
            {enrichment.gemma_brief}
          </p>
          {enrichment.gemma_brief.length > 100 && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="mt-1 text-xs text-blue-600 hover:text-blue-800"
            >
              {expanded ? 'Show less' : 'Read more'}
            </button>
          )}
        </div>
      )}

      {/* Timestamps */}
      <div className="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-400">
        <div>First seen: {new Date(profile.first_seen).toLocaleString()}</div>
        <div>Last seen: {new Date(profile.last_seen).toLocaleString()}</div>
      </div>
    </div>
  )
}

export default AttackerProfileCard
