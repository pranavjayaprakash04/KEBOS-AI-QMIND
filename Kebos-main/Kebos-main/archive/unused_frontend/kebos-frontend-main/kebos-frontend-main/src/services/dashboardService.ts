/**
 * Dashboard Service
 * 
 * Handles all dashboard-related API calls for metrics, activities, and analytics
 */

import { apiClient } from './apiClient';
import { ThreatSeverity, ThreatType } from '@/types';

export interface DashboardMetrics {
  activeThreats: number;
  attackSimulations: number;
  activeJobs: number;
  threatsByType: Record<string, number>;
  threatsBySeverity: Record<string, number>;
  systemHealth: {
    uptime: number;
    cpuUsage: number;
    memoryUsage: number;
    diskUsage: number;
  };
}

export interface ThreatActivity {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    borderColor: string;
    backgroundColor: string;
  }>;
}

export interface RecentActivity {
  id: string;
  type: 'threat' | 'simulation' | 'job' | 'audit';
  message: string;
  timestamp: string;
  severity?: ThreatSeverity;
  userId?: string;
  details?: Record<string, any>;
}

export interface ThreatAlert {
  id: string;
  threatType: ThreatType;
  severity: ThreatSeverity;
  source: string;
  target: string;
  description: string;
  timestamp: string;
  confidence: number;
  resolved: boolean;
}

export interface JobStatus {
  id: string;
  type: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  createdAt: string;
  updatedAt: string;
  result?: any;
  error?: string;
}

export class DashboardService {
  private baseUrl = '/api';

  /**
   * Get comprehensive dashboard metrics
   */
  async getMetrics(): Promise<DashboardMetrics> {
    try {
      // Get threat detection statistics
      const threatStatsResponse = await apiClient.get(`${this.baseUrl}/threats/stats`);
      const threatStats = threatStatsResponse.data;

      // Get active job count
      const jobsResponse = await apiClient.get(`${this.baseUrl}/jobs/active`);
      const activeJobs = Array.isArray(jobsResponse.data) ? jobsResponse.data.length : 0;

      // Get recent alerts to calculate active threats
      const alertsResponse = await apiClient.get(`${this.baseUrl}/threats/alerts?limit=100`);
      const recentAlerts = Array.isArray(alertsResponse.data) ? alertsResponse.data : [];
      const activeThreats = recentAlerts.filter(alert => !alert.resolved).length;

      // Calculate threat distribution by type and severity
      const threatsByType: Record<string, number> = {};
      const threatsBySeverity: Record<string, number> = {};

      recentAlerts.forEach((alert: any) => {
        if (alert.threatType) {
          threatsByType[alert.threatType] = (threatsByType[alert.threatType] || 0) + 1;
        }
        if (alert.severity) {
          threatsBySeverity[alert.severity] = (threatsBySeverity[alert.severity] || 0) + 1;
        }
      });

      // System health metrics (would typically come from monitoring service)
      const systemHealth = {
        uptime: 99.8,
        cpuUsage: Math.random() * 30 + 20, // 20-50%
        memoryUsage: Math.random() * 20 + 40, // 40-60%
        diskUsage: Math.random() * 15 + 25, // 25-40%
      };

      return {
        activeThreats,
        attackSimulations: threatStats?.simulations_run || 0,
        activeJobs,
        threatsByType,
        threatsBySeverity,
        systemHealth,
      };
    } catch (error) {
      console.error('Failed to fetch dashboard metrics:', error);
      throw new Error('Failed to fetch dashboard metrics');
    }
  }

  /**
   * Get threat activity data for charts
   */
  async getThreatActivity(timeRange: string = '7d'): Promise<ThreatActivity> {
    try {
      const response = await apiClient.get(`${this.baseUrl}/threats/activity?range=${timeRange}`);
      
      if (response.data && response.data.labels && response.data.datasets) {
        return response.data;
      }

      // Fallback: Generate from recent alerts if dedicated endpoint doesn't exist
      const alertsResponse = await apiClient.get(`${this.baseUrl}/threats/alerts?limit=100`);
      const alerts = Array.isArray(alertsResponse.data) ? alertsResponse.data : [];

      // Group alerts by day for the last 7 days
      const now = new Date();
      const labels: string[] = [];
      const criticalData: number[] = [];
      const highData: number[] = [];
      const mediumData: number[] = [];
      const lowData: number[] = [];

      for (let i = 6; i >= 0; i--) {
        const date = new Date(now);
        date.setDate(date.getDate() - i);
        const dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        labels.push(dateStr);

        const dayStart = new Date(date);
        dayStart.setHours(0, 0, 0, 0);
        const dayEnd = new Date(date);
        dayEnd.setHours(23, 59, 59, 999);

        const dayAlerts = alerts.filter((alert: any) => {
          const alertDate = new Date(alert.timestamp);
          return alertDate >= dayStart && alertDate <= dayEnd;
        });

        criticalData.push(dayAlerts.filter((a: any) => a.severity === 'critical').length);
        highData.push(dayAlerts.filter((a: any) => a.severity === 'high').length);
        mediumData.push(dayAlerts.filter((a: any) => a.severity === 'medium').length);
        lowData.push(dayAlerts.filter((a: any) => a.severity === 'low').length);
      }

      return {
        labels,
        datasets: [
          {
            label: 'Critical Threats',
            data: criticalData,
            borderColor: '#ef4444',
            backgroundColor: 'rgba(239, 68, 68, 0.2)',
          },
          {
            label: 'High Threats',
            data: highData,
            borderColor: '#f97316',
            backgroundColor: 'rgba(249, 115, 22, 0.2)',
          },
          {
            label: 'Medium Threats',
            data: mediumData,
            borderColor: '#eab308',
            backgroundColor: 'rgba(234, 179, 8, 0.2)',
          },
          {
            label: 'Low Threats',
            data: lowData,
            borderColor: '#22c55e',
            backgroundColor: 'rgba(34, 197, 94, 0.2)',
          },
        ],
      };
    } catch (error) {
      console.error('Failed to fetch threat activity:', error);
      throw new Error('Failed to fetch threat activity data');
    }
  }

  /**
   * Get recent system activities
   */
  async getRecentActivities(limit: number = 10): Promise<RecentActivity[]> {
    try {
      const activities: RecentActivity[] = [];

      // Get recent threat alerts
      const alertsResponse = await apiClient.get(`${this.baseUrl}/threats/alerts?limit=${Math.ceil(limit / 2)}`);
      const alerts = Array.isArray(alertsResponse.data) ? alertsResponse.data : [];
      
      alerts.forEach((alert: any) => {
        activities.push({
          id: `threat-${alert.id}`,
          type: 'threat',
          message: `${alert.severity} threat detected: ${alert.description}`,
          timestamp: alert.timestamp,
          severity: alert.severity as ThreatSeverity,
          details: alert,
        });
      });

      // Get recent audit logs
      const auditResponse = await apiClient.get(`${this.baseUrl}/audit/recent?limit=${Math.ceil(limit / 2)}`);
      const auditLogs = Array.isArray(auditResponse.data) ? auditResponse.data : [];
      
      auditLogs.forEach((log: any) => {
        let type: RecentActivity['type'] = 'audit';
        let message = log.action;

        // Categorize audit logs
        if (log.action.includes('job') || log.action.includes('task')) {
          type = 'job';
          message = `Job ${log.action}: ${log.details?.job_type || 'system task'}`;
        } else if (log.action.includes('simulation') || log.action.includes('attack')) {
          type = 'simulation';
          message = `Attack simulation: ${log.action}`;
        } else {
          type = 'audit';
          message = `System audit: ${log.action}`;
        }

        activities.push({
          id: `audit-${log.id}`,
          type,
          message,
          timestamp: log.timestamp,
          userId: log.user_id,
          details: log.details,
        });
      });

      // Sort by timestamp (most recent first) and limit results
      return activities
        .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
        .slice(0, limit);
    } catch (error) {
      console.error('Failed to fetch recent activities:', error);
      throw new Error('Failed to fetch recent activities');
    }
  }

  /**
   * Get active job statuses
   */
  async getActiveJobs(): Promise<JobStatus[]> {
    try {
      const response = await apiClient.get(`${this.baseUrl}/jobs/active`);
      return Array.isArray(response.data) ? response.data : [];
    } catch (error) {
      console.error('Failed to fetch active jobs:', error);
      throw new Error('Failed to fetch active jobs');
    }
  }

  /**
   * Get threat alerts with filtering
   */
  async getThreatAlerts(
    limit: number = 50,
    severity?: ThreatSeverity,
    timeRange?: string
  ): Promise<ThreatAlert[]> {
    try {
      const params = new URLSearchParams();
      params.append('limit', limit.toString());
      if (severity) params.append('severity', severity);
      if (timeRange) params.append('range', timeRange);

      const response = await apiClient.get(`${this.baseUrl}/threats/alerts?${params.toString()}`);
      return Array.isArray(response.data) ? response.data : [];
    } catch (error) {
      console.error('Failed to fetch threat alerts:', error);
      throw new Error('Failed to fetch threat alerts');
    }
  }

  /**
   * Get system performance metrics
   */
  async getSystemMetrics(): Promise<any> {
    try {
      // This would typically come from a dedicated monitoring service
      // For now, we'll aggregate from available endpoints
      const threatStats = await apiClient.get(`${this.baseUrl}/threats/stats`);
      
      return {
        uptime: 99.8,
        throughput: threatStats.data?.total_packets_processed || 0,
        accuracy: threatStats.data?.detection_accuracy || 0,
        responseTime: threatStats.data?.average_processing_time_ms || 0,
        errorRate: threatStats.data?.false_positive_rate || 0,
      };
    } catch (error) {
      console.error('Failed to fetch system metrics:', error);
      throw new Error('Failed to fetch system metrics');
    }
  }
}

export const dashboardService = new DashboardService();
