export type TrapType = 'ssh' | 'http' | 'rdp'
export type EventType = 'credential_attempt' | 'page_visit' |
                        'connection_attempt' | 'command_attempt' |
                        'negotiation_data'

export interface TrapStatus {
  trap_type: TrapType
  port: number
  running: boolean
  hit_count: number
}

export interface HoneypotEvent {
  time: string
  trap_type: TrapType
  event_type: EventType
  attacker_ip: string
  enrichment?: AttackerEnrichment
}

export interface AttackerEnrichment {
  threat_id: string | null
  confidence: number
  category: string
  stability_score: number
  threat_state: Record<string, number>
  mitigation: string
  gemma_brief: string
  fallback?: boolean
}

export interface AttackerProfile {
  ip: string
  trap_types_hit: TrapType[]
  first_seen: string
  last_seen: string
  enrichment: AttackerEnrichment
}
