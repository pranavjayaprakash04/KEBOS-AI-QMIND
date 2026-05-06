import React from 'react'
import { AttackerProfile } from '../../../types/deception'

interface ThreatStateVisualizerProps {
  profiles: AttackerProfile[]
}

const THREAT_CATEGORIES = [
  'C2_Infrastructure',
  'Botnet_IP',
  'Phishing',
  'Malware',
  'Credential_Leak',
  'DDoS',
  'Insider_Threat',
  'Supply_Chain',
  'CVE_Exploitation',
  'Benign',
]

export const ThreatStateVisualizer: React.FC<ThreatStateVisualizerProps> = ({
  profiles,
}) => {
  // Get the profile with highest stability score
  const topProfile = profiles.length > 0
    ? [...profiles].sort((a, b) => (b.enrichment?.stability_score || 0) - (a.enrichment?.stability_score || 0))[0]
    : null

  const threatState = topProfile?.enrichment?.threat_state || {}
  const stabilityScore = topProfile?.enrichment?.stability_score || 0

  // Find the category with highest score
  let maxCategory = ''
  let maxScore = 0

  THREAT_CATEGORIES.forEach((category) => {
    const score = threatState[category] || 0
    if (score > maxScore) {
      maxScore = score
      maxCategory = category
    }
  })

  if (!topProfile) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Threat State</h2>
        <div className="text-center text-gray-400 py-8">
          Awaiting first attacker...
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
      <h2 className="text-lg font-semibold text-gray-800 mb-2">Threat State</h2>
      <p className="text-sm text-gray-500 mb-4">Profile: {topProfile.ip}</p>

      {stabilityScore >= 0.72 && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 rounded animate-pulse">
          <p className="text-red-800 font-semibold text-sm">
            HIGH CONFIDENCE THREAT — Automated response active
          </p>
        </div>
      )}

      <div className="space-y-3">
        {THREAT_CATEGORIES.map((category) => {
          const score = threatState[category] || 0
          const isMax = category === maxCategory && score > 0

          return (
            <div key={category}>
              <div className="flex justify-between text-xs mb-1">
                <span className={isMax ? 'font-semibold text-amber-700' : 'text-gray-600'}>
                  {category.replace(/_/g, ' ')}
                </span>
                <span className="text-gray-500">{(score * 100).toFixed(0)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className={`h-3 rounded-full transition-all ${
                    isMax ? 'bg-amber-500' : 'bg-gray-400'
                  }`}
                  style={{ width: `${score * 100}%` }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default ThreatStateVisualizer
