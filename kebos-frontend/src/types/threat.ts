export interface ThreatEvent {
  id: string;
  ioc_value: string;
  ioc_type: string;
  lead_category: ThreatCategory;
  confidence: number;
  qmind_confidence?: number;
  qmind_category?: string;
  source: string;
  is_proactive: boolean;
  status: ThreatStatus;
  reversibility: Reversibility;
  created_at: string;
  updated_at?: string;
  tenant_id: number;
  cert_in_deadline?: string;
  cert_in_status?: CERTInStatus;
}

export type ThreatCategory =
  | 'C2_Infrastructure'
  | 'Botnet_IP'
  | 'Phishing'
  | 'Malware'
  | 'Credential_Leak'
  | 'DDoS'
  | 'Insider_Threat'
  | 'Supply_Chain'
  | 'CVE_Exploitation'
  | 'Benign';

export type ThreatStatus =
  | 'PENDING'
  | 'ELEVATED'
  | 'CONFIRMED_THREAT'
  | 'FALSE_POSITIVE'
  | 'BENIGN';

export type Reversibility = 'REVERSIBLE' | 'IRREVERSIBLE';

export type CERTInStatus = 'PENDING' | 'SUBMITTED' | 'ACKNOWLEDGED' | 'CLOSED';

export interface Case {
  id: string;
  case_number: string;
  title: string;
  threat_event_id: string;
  tenant_id: number;
  status: 'OPEN' | 'IN_PROGRESS' | 'CLOSED';
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  cert_in_deadline: string;
  cert_in_status: CERTInStatus;
  created_at: string;
  updated_at: string;
}

export interface TimelineEvent {
  timestamp: string;
  event_type: string;
  actor: string;
  description: string;
  metadata: Record<string, unknown>;
  severity: string;
}

export interface CaseTimeline {
  case_id: string;
  total_events: number;
  events: TimelineEvent[];
  generated_at: string;
  dilithium_signature: string;
}

export interface SOCReport {
  case_id: string;
  sections: {
    executive_summary: string;
    technical_analysis: string;
    ioc_details: string;
    mitigation_recommendations: string;
  };
  dilithium_signature?: string;
  generated_at: string;
}
