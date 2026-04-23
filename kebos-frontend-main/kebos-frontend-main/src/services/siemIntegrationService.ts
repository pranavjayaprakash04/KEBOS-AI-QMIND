import { apiClient } from './apiClient';
import { ApiResponse, PaginatedResponse } from '@/types';

// SIEM Integration Service Types
export interface SIEMConfig {
  id?: string;
  name: string;
  display_name?: string;
  description?: string;
  siem_type: SIEMType;
  endpoint_url: string;
  auth_type: SIEMAuthType;
  auth_config: Record<string, any>;
  connection_settings: Record<string, any>;
  is_active: boolean;
  is_primary: boolean;
  tags?: Record<string, string>;
  created_at?: string;
  updated_at?: string;
  last_health_check?: string;
  connection_status?: SIEMConnectionStatus;
}

export interface SIEMEvent {
  id?: string;
  siem_config_id: string;
  event_id: string;
  timestamp: string;
  source_ip?: string;
  destination_ip?: string;
  event_type: string;
  severity: SIEMEventSeverity;
  category: SIEMEventCategory;
  description: string;
  raw_data: Record<string, any>;
  processed_data?: Record<string, any>;
  tags?: Record<string, string>;
  user_agent?: string;
  user_name?: string;
  host_name?: string;
  process_name?: string;
  file_name?: string;
  created_at?: string;
}

export interface SIEMQuery {
  id?: string;
  siem_config_id: string;
  query_name?: string;
  query_string: string;
  query_language: string;
  parameters?: Record<string, any>;
  time_range_start?: string;
  time_range_end?: string;
  result_count?: number;
  execution_time_ms?: number;
  status: string;
  error_message?: string;
  created_at?: string;
  completed_at?: string;
}

export interface SIEMHealthStatus {
  siem_config_id: string;
  status: SIEMConnectionStatus;
  last_check: string;
  response_time_ms?: number;
  error_message?: string;
  details: Record<string, any>;
}

export interface SIEMStatistics {
  total_configs: number;
  active_configs: number;
  total_events: number;
  events_last_24h: number;
  events_by_severity: Record<SIEMEventSeverity, number>;
  events_by_category: Record<SIEMEventCategory, number>;
  events_by_siem: Record<string, number>;
  total_queries: number;
  queries_last_24h: number;
  avg_query_time_ms: number;
  connection_health: {
    healthy: number;
    degraded: number;
    failed: number;
  };
}

export interface SIEMWebhookPayload {
  event_type: string;
  timestamp: string;
  source: string;
  data: Record<string, any>;
  severity?: SIEMEventSeverity;
  category?: SIEMEventCategory;
}

export enum SIEMType {
  SPLUNK = 'splunk',
  QRADAR = 'qradar',
  ELASTIC_SIEM = 'elastic_siem',
  ELASTICSEARCH = 'elasticsearch',
  AZURE_SENTINEL = 'azure_sentinel',
  MICROSOFT_SENTINEL = 'microsoft_sentinel',
  CHRONICLE = 'chronicle',
  ARCSIGHT = 'arcsight',
  SUMO_LOGIC = 'sumo_logic',
  LOGRHYTHM = 'logrhythm',
  SECURONIX = 'securonix',
  DEVO = 'devo',
  GENERIC = 'generic'
}

export enum SIEMAuthType {
  API_KEY = 'api_key',
  OAUTH2 = 'oauth2',
  BASIC_AUTH = 'basic_auth',
  BEARER_TOKEN = 'bearer_token',
  JWT = 'jwt',
  CERTIFICATE = 'certificate',
  SAML = 'saml',
  NONE = 'none'
}

export enum SIEMEventSeverity {
  CRITICAL = 'critical',
  HIGH = 'high',
  MEDIUM = 'medium',
  LOW = 'low',
  INFO = 'info',
  UNKNOWN = 'unknown'
}

export enum SIEMEventCategory {
  AUTHENTICATION = 'authentication',
  AUTHORIZATION = 'authorization',
  NETWORK = 'network',
  MALWARE = 'malware',
  DATA_LOSS = 'data_loss',
  INTRUSION = 'intrusion',
  VULNERABILITY = 'vulnerability',
  COMPLIANCE = 'compliance',
  SYSTEM = 'system',
  APPLICATION = 'application',
  OTHER = 'other'
}

export enum SIEMConnectionStatus {
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  ERROR = 'error',
  TESTING = 'testing',
  MAINTENANCE = 'maintenance',
  UNKNOWN = 'unknown'
}

export interface SIEMConfigCreateRequest {
  name: string;
  display_name?: string;
  description?: string;
  siem_type: SIEMType;
  endpoint_url: string;
  auth_type: SIEMAuthType;
  auth_config: Record<string, any>;
  connection_settings?: Record<string, any>;
  is_active?: boolean;
  is_primary?: boolean;
  tags?: Record<string, string>;
}

export interface SIEMConfigUpdateRequest {
  name?: string;
  display_name?: string;
  description?: string;
  endpoint_url?: string;
  auth_type?: SIEMAuthType;
  auth_config?: Record<string, any>;
  connection_settings?: Record<string, any>;
  is_active?: boolean;
  is_primary?: boolean;
  tags?: Record<string, string>;
}

export interface SIEMEventQuery {
  siem_config_id?: string;
  severity?: SIEMEventSeverity[];
  category?: SIEMEventCategory[];
  event_type?: string;
  source_ip?: string;
  destination_ip?: string;
  user_name?: string;
  host_name?: string;
  start_time?: string;
  end_time?: string;
  search?: string;
  page?: number;
  limit?: number;
  sort_by?: string;
  sort_desc?: boolean;
}

export interface SIEMQueryRequest {
  query_name?: string;
  query_string: string;
  query_language: string;
  parameters?: Record<string, any>;
  time_range_start?: string;
  time_range_end?: string;
}

class SIEMIntegrationService {
  private readonly baseUrl = '/api/siem-integration';

  /**
   * Get all SIEM configurations
   */
  async getConfigs(): Promise<SIEMConfig[]> {
    const response = await apiClient.get<ApiResponse<SIEMConfig[]>>(
      `${this.baseUrl}/configs`
    );
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    
    throw new Error(response.data.error || 'Failed to fetch SIEM configurations');
  }

  /**
   * Get a specific SIEM configuration
   */
  async getConfig(configId: string): Promise<SIEMConfig> {
    const response = await apiClient.get<ApiResponse<SIEMConfig>>(
      `${this.baseUrl}/config/${configId}`
    );
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    
    throw new Error(response.data.error || 'Failed to fetch SIEM configuration');
  }

  /**
   * Create a new SIEM configuration
   */
  async createConfig(configData: SIEMConfigCreateRequest): Promise<{ siem_id: string }> {
    const response = await apiClient.post<ApiResponse<{ siem_id: string }>>(
      `${this.baseUrl}/config`,
      configData
    );
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    
    throw new Error(response.data.error || 'Failed to create SIEM configuration');
  }

  /**
   * Update an existing SIEM configuration
   */
  async updateConfig(configId: string, updates: SIEMConfigUpdateRequest): Promise<{ success: boolean }> {
    const response = await apiClient.put<ApiResponse<{ success: boolean }>>(
      `${this.baseUrl}/config/${configId}`,
      updates
    );
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    
    throw new Error(response.data.error || 'Failed to update SIEM configuration');
  }

  /**
   * Delete a SIEM configuration
   */
  async deleteConfig(configId: string): Promise<{ success: boolean }> {
    const response = await apiClient.delete<ApiResponse<{ success: boolean }>>(
      `${this.baseUrl}/config/${configId}`
    );
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    
    throw new Error(response.data.error || 'Failed to delete SIEM configuration');
  }

  /**
   * Test SIEM connection
   */
  async testConnection(configId: string): Promise<SIEMHealthStatus> {
    const response = await apiClient.post<ApiResponse<SIEMHealthStatus>>(
      `${this.baseUrl}/test/connection/${configId}`
    );
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    
    throw new Error(response.data.error || 'Failed to test SIEM connection');
  }

  /**
   * Get SIEM health status
   */
  async getHealthStatus(configId: string): Promise<SIEMHealthStatus> {
    const response = await apiClient.get<ApiResponse<SIEMHealthStatus>>(
      `${this.baseUrl}/config/${configId}/health`
    );
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    
    throw new Error(response.data.error || 'Failed to fetch health status');
  }

  /**
   * Get events with filtering and pagination
   */
  async getEvents(query?: SIEMEventQuery): Promise<PaginatedResponse<SIEMEvent>> {
    const params = new URLSearchParams();
    
    if (query) {
      if (query.siem_config_id) params.append('siem_config_id', query.siem_config_id);
      if (query.severity) params.append('severity', query.severity.join(','));
      if (query.category) params.append('category', query.category.join(','));
      if (query.event_type) params.append('event_type', query.event_type);
      if (query.source_ip) params.append('source_ip', query.source_ip);
      if (query.destination_ip) params.append('destination_ip', query.destination_ip);
      if (query.user_name) params.append('user_name', query.user_name);
      if (query.host_name) params.append('host_name', query.host_name);
      if (query.start_time) params.append('start_time', query.start_time);
      if (query.end_time) params.append('end_time', query.end_time);
      if (query.search) params.append('search', query.search);
      if (query.page) params.append('page', query.page.toString());
      if (query.limit) params.append('limit', query.limit.toString());
      if (query.sort_by) params.append('sort_by', query.sort_by);
      if (query.sort_desc !== undefined) params.append('sort_desc', query.sort_desc.toString());
    }

    const response = await apiClient.get<ApiResponse<PaginatedResponse<SIEMEvent>>>(
      `${this.baseUrl}/events?${params.toString()}`
    );
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    
    throw new Error(response.data.error || 'Failed to fetch events');
  }

  /**
   * Create a new event
   */
  async createEvent(eventData: Omit<SIEMEvent, 'id' | 'created_at'>): Promise<SIEMEvent> {
    const response = await apiClient.post<ApiResponse<SIEMEvent>>(
      `${this.baseUrl}/events`,
      eventData
    );
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    
    throw new Error(response.data.error || 'Failed to create event');
  }

  /**
   * Create multiple events in batch
   */
  async createEventsBatch(events: Omit<SIEMEvent, 'id' | 'created_at'>[]): Promise<{ created: number; failed: number }> {
    const response = await apiClient.post<ApiResponse<{ created: number; failed: number }>>(
      `${this.baseUrl}/events/batch`,
      { events }
    );
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    
    throw new Error(response.data.error || 'Failed to create events batch');
  }

  /**
   * Execute a query against a SIEM system
   */
  async executeQuery(configId: string, queryData: SIEMQueryRequest): Promise<SIEMQuery> {
    const response = await apiClient.post<ApiResponse<SIEMQuery>>(
      `${this.baseUrl}/config/${configId}/query`,
      queryData
    );
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    
    throw new Error(response.data.error || 'Failed to execute query');
  }

  /**
   * Get integration statistics
   */
  async getStatistics(): Promise<SIEMStatistics> {
    const response = await apiClient.get<ApiResponse<SIEMStatistics>>(
      `${this.baseUrl}/stats`
    );
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    
    throw new Error(response.data.error || 'Failed to fetch statistics');
  }

  /**
   * Get available SIEM types
   */
  async getSIEMTypes(): Promise<{ types: Array<{ value: string; label: string; description?: string }> }> {
    const response = await apiClient.get<ApiResponse<{ types: Array<{ value: string; label: string; description?: string }> }>>(
      `${this.baseUrl}/types`
    );
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    
    throw new Error(response.data.error || 'Failed to fetch SIEM types');
  }

  /**
   * Get available authentication types
   */
  async getAuthTypes(): Promise<{ auth_types: Array<{ value: string; label: string; description?: string }> }> {
    const response = await apiClient.get<ApiResponse<{ auth_types: Array<{ value: string; label: string; description?: string }> }>>(
      `${this.baseUrl}/auth-types`
    );
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    
    throw new Error(response.data.error || 'Failed to fetch auth types');
  }

  /**
   * Get available event severities
   */
  async getEventSeverities(): Promise<{ severities: Array<{ value: string; label: string; color?: string }> }> {
    const response = await apiClient.get<ApiResponse<{ severities: Array<{ value: string; label: string; color?: string }> }>>(
      `${this.baseUrl}/severities`
    );
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    
    throw new Error(response.data.error || 'Failed to fetch severities');
  }

  /**
   * Process webhook data
   */
  async processWebhook(webhookData: SIEMWebhookPayload): Promise<{ processed: boolean; event_id?: string }> {
    const response = await apiClient.post<ApiResponse<{ processed: boolean; event_id?: string }>>(
      `${this.baseUrl}/webhook`,
      webhookData
    );
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    
    throw new Error(response.data.error || 'Failed to process webhook');
  }

  /**
   * Get recent events (last 24 hours)
   */
  async getRecentEvents(limit = 50): Promise<SIEMEvent[]> {
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    
    const result = await this.getEvents({
      start_time: yesterday.toISOString(),
      limit,
      sort_by: 'timestamp',
      sort_desc: true
    });
    
    return result.items;
  }

  /**
   * Get critical events requiring attention
   */
  async getCriticalEvents(): Promise<SIEMEvent[]> {
    const result = await this.getEvents({
      severity: [SIEMEventSeverity.CRITICAL, SIEMEventSeverity.HIGH],
      limit: 100,
      sort_by: 'timestamp',
      sort_desc: true
    });
    
    return result.items;
  }

  /**
   * Search events by text
   */
  async searchEvents(searchTerm: string, page = 1, limit = 20): Promise<PaginatedResponse<SIEMEvent>> {
    return this.getEvents({
      search: searchTerm,
      page,
      limit,
      sort_by: 'timestamp',
      sort_desc: true
    });
  }

  /**
   * Export events data
   */
  async exportEvents(query?: SIEMEventQuery, format: 'csv' | 'json' = 'csv'): Promise<void> {
    const params = new URLSearchParams();
    params.append('format', format);
    
    if (query) {
      Object.entries(query).forEach(([key, value]) => {
        if (value !== undefined) {
          params.append(key, Array.isArray(value) ? value.join(',') : value.toString());
        }
      });
    }

    await apiClient.download(
      `${this.baseUrl}/events/export?${params.toString()}`,
      `siem_events_export_${new Date().toISOString().split('T')[0]}.${format}`
    );
  }
}

export const siemIntegrationService = new SIEMIntegrationService();
