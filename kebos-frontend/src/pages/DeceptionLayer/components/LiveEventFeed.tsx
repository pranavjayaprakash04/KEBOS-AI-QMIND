import React from 'react'
import { HoneypotEvent, TrapType, EventType } from '../../../types/deception'

interface LiveEventFeedProps {
  events: HoneypotEvent[]
}

const TRAP_COLORS: Record<TrapType, string> = {
  ssh: 'bg-blue-100 text-blue-800 border-blue-300',
  http: 'bg-amber-100 text-amber-800 border-amber-300',
  rdp: 'bg-purple-100 text-purple-800 border-purple-300',
}

const EVENT_TYPE_LABELS: Record<EventType, string> = {
  credential_attempt: 'Credential Attempt',
  page_visit: 'Page Visit',
  connection_attempt: 'Connection',
  command_attempt: 'Command',
  negotiation_data: 'Negotiation',
}

function formatRelativeTime(timeStr: string): string {
  const date = new Date(timeStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffSecs = Math.floor(diffMs / 1000)
  const diffMins = Math.floor(diffSecs / 60)
  const diffHours = Math.floor(diffMins / 60)

  if (diffSecs < 10) return 'just now'
  if (diffSecs < 60) return `${diffSecs}s ago`
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  return date.toLocaleDateString()
}

export const LiveEventFeed: React.FC<LiveEventFeedProps> = ({ events }) => {
  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200 h-full overflow-hidden flex flex-col">
      <div className="p-4 border-b border-gray-200 bg-gray-50">
        <h2 className="font-semibold text-gray-800">Live Event Feed</h2>
        <p className="text-sm text-gray-500">Last 50 honeypot interactions</p>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {events.length === 0 ? (
          <div className="text-center text-gray-400 py-8">No events yet</div>
        ) : (
          events.map((event, index) => (
            <div
              key={`${event.time}-${event.attacker_ip}-${index}`}
              className={`p-3 rounded-lg border animate-in fade-in slide-in-from-top-2 duration-300 ${
                index === 0 ? 'bg-yellow-50 border-yellow-300' : 'bg-gray-50 border-gray-200'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-400">
                    {formatRelativeTime(event.time)}
                  </span>

                  <span className={`px-2 py-0.5 text-xs font-medium rounded-full border ${TRAP_COLORS[event.trap_type]}`}>
                    {event.trap_type.toUpperCase()}
                  </span>

                  <span className="text-xs text-gray-500">
                    {EVENT_TYPE_LABELS[event.event_type]}
                  </span>
                </div>

                {event.enrichment && (
                  <div className="flex items-center gap-1">
                    <span className={`text-xs font-semibold px-2 py-0.5 rounded ${
                      event.enrichment.stability_score >= 0.72
                        ? 'bg-red-100 text-red-800'
                        : 'bg-blue-100 text-blue-800'
                    }`}>
                      {(event.enrichment.stability_score * 100).toFixed(0)}%
                    </span>
                  </div>
                )}
              </div>

              <div className="mt-1 flex items-center gap-2">
                <code className="text-sm font-mono text-gray-700">{event.attacker_ip}</code>

                {event.enrichment && (
                  <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                    {event.enrichment.category}
                  </span>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default LiveEventFeed
