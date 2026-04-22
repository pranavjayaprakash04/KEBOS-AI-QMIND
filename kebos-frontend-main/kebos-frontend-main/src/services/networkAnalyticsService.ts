import { apiClient } from './apiClient';

export interface AnalyticsQuery {
  metrics: string[];
  timeRange: string;
  filters?: Record<string, any>;
  visualization?: string;
}

export interface AnalyticsResult {
  id: string;
  query: AnalyticsQuery;
  data: any[];
  visualization: string;
  metadata: Record<string, any>;
  created_at: string;
}

export interface TrafficPattern {
  id: string;
  name: string;
  description: string;
  pattern_type: string;
  parameters: Record<string, any>;
  is_active: boolean;
  created_at: string;
}

export interface NetworkAnomaly {
  id: string;
  anomaly_type: string;
  severity: string;
  confidence: number;
  description: string;
  timestamp: string;
  metadata: Record<string, any>;
}

export interface NetworkFlow {
  id: string;
  source_ip: string;
  destination_ip: string;
  source_port: number;
  destination_port: number;
  protocol: string;
  bytes: number;
  packets: number;
  timestamp: string;
}

export interface NetworkTopology {
  id: string;
  node_type: string;
  node_id: string;
  name: string;
  connections: string[];
  metadata: Record<string, any>;
}

export interface NetworkStats {
  total_flows: number;
  total_bytes: number;
  total_packets: number;
  unique_ips: number;
  top_protocols: Record<string, number>;
  time_range: string;
}

class NetworkAnalyticsService {
  // Query execution
  async executeQuery(query: AnalyticsQuery): Promise<AnalyticsResult> {
    const response = await apiClient.post('/network/query', query);
    return response.data;
  }

  // Configuration endpoints
  async getAvailableVisualizations(): Promise<string[]> {
    const response = await apiClient.get('/network/visualizations');
    return response.data;
  }

  async getAvailableMetrics(): Promise<string[]> {
    const response = await apiClient.get('/network/metrics');
    return response.data;
  }

  async getAvailableTimeRanges(): Promise<string[]> {
    const response = await apiClient.get('/network/time-ranges');
    return response.data;
  }

  // Traffic patterns
  async getTrafficPatterns(): Promise<TrafficPattern[]> {
    const response = await apiClient.get('/network/patterns');
    return response.data;
  }

  async createTrafficPattern(pattern: Omit<TrafficPattern, 'id' | 'created_at'>): Promise<TrafficPattern> {
    const response = await apiClient.post('/network/patterns', pattern);
    return response.data;
  }

  // Anomaly detection
  async getAnomalies(filters?: Record<string, any>): Promise<NetworkAnomaly[]> {
    const response = await apiClient.get('/network/anomalies', { params: filters });
    return response.data;
  }

  async getAnomalyTypes(): Promise<string[]> {
    const response = await apiClient.get('/network/anomalies/types');
    return response.data;
  }

  // Network flows
  async getNetworkFlows(filters?: Record<string, any>): Promise<NetworkFlow[]> {
    const response = await apiClient.get('/network/flows', { params: filters });
    return response.data;
  }

  // Network topology
  async getNetworkTopology(): Promise<NetworkTopology[]> {
    const response = await apiClient.get('/network/topology');
    return response.data;
  }

  // Statistics
  async getNetworkStats(timeRange?: string): Promise<NetworkStats> {
    const response = await apiClient.get('/network/stats', { 
      params: timeRange ? { time_range: timeRange } : {}
    });
    return response.data;
  }

  // Real-time data
  async getRealtimeSummary(): Promise<any> {
    const response = await apiClient.get('/network/realtime/summary');
    return response.data;
  }

  async getLatestFlows(limit?: number): Promise<NetworkFlow[]> {
    const response = await apiClient.get('/network/realtime/flows/latest', {
      params: limit ? { limit } : {}
    });
    return response.data;
  }

  // Background jobs
  async startPatternDetectionJob(config: Record<string, any>): Promise<{ job_id: string }> {
    const response = await apiClient.post('/network/jobs/pattern-detection', config);
    return response.data;
  }

  async startAnomalyDetectionJob(config: Record<string, any>): Promise<{ job_id: string }> {
    const response = await apiClient.post('/network/jobs/anomaly-detection', config);
    return response.data;
  }

  // Export
  async exportFlows(filters: Record<string, any>, format: string = 'csv'): Promise<Blob> {
    const response = await apiClient.post('/network/export/flows', 
      { ...filters, format },
      { responseType: 'blob' }
    );
    return response.data;
  }

  // Health and diagnostics
  async getHealth(): Promise<any> {
    const response = await apiClient.get('/network/health');
    return response.data;
  }

  async getDiagnostics(): Promise<any> {
    const response = await apiClient.get('/network/diagnostics');
    return response.data;
  }
}

export const networkAnalyticsService = new NetworkAnalyticsService();
