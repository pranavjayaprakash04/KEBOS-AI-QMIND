import { apiClient } from './apiClient';
import { ApiResponse } from '@/types';

export interface ThreatAlert {
  id: string;
  title: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  source: string;
  timestamp: string;
  status: 'active' | 'investigating' | 'resolved' | 'false_positive';
  description: string;
  type: string;
  affectedSystems: string[];
  indicators: string[];
  mitigations: string[];
}

export interface ThreatFilters {
  severity?: string[];
  status?: string[];
  source?: string[];
  search?: string;
  dateRange?: {
    start: string;
    end: string;
  };
}

export interface ThreatStats {
  total: number;
  active: number;
  resolved: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
}

export class ThreatDetectionService {
  private baseUrl = '/threats';

  async getThreats(filters: ThreatFilters = {}): Promise<ApiResponse<ThreatAlert[]>> {
    try {
      const response = await apiClient.get<ApiResponse<ThreatAlert[]>>(`${this.baseUrl}`, {
        params: filters
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to fetch threats');
    }
  }

  async getThreatById(id: string): Promise<ApiResponse<ThreatAlert>> {
    try {
      const response = await apiClient.get<ApiResponse<ThreatAlert>>(`${this.baseUrl}/${id}`);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to fetch threat details');
    }
  }

  async updateThreatStatus(id: string, status: string): Promise<ApiResponse<ThreatAlert>> {
    try {
      const response = await apiClient.patch<ApiResponse<ThreatAlert>>(`${this.baseUrl}/${id}/status`, {
        status
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to update threat status');
    }
  }

  async getThreatStats(): Promise<ApiResponse<ThreatStats>> {
    try {
      const response = await apiClient.get<ApiResponse<ThreatStats>>(`${this.baseUrl}/stats`);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to fetch threat statistics');
    }
  }

  async investigateThreat(id: string, notes: string): Promise<ApiResponse<any>> {
    try {
      const response = await apiClient.post<ApiResponse<any>>(`${this.baseUrl}/${id}/investigate`, {
        notes
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to investigate threat');
    }
  }

  async resolveThreat(id: string, resolution: string): Promise<ApiResponse<any>> {
    try {
      const response = await apiClient.post<ApiResponse<any>>(`${this.baseUrl}/${id}/resolve`, {
        resolution
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to resolve threat');
    }
  }
}

export const threatDetectionService = new ThreatDetectionService();
