import { apiClient } from './apiClient';
import { ApiResponse, PaginatedResponse } from '@/types';

// Job Management Service Types
export interface Job {
  id: string;
  name: string;
  job_type: JobType;
  status: JobStatus;
  priority: JobPriority;
  progress: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  updated_at: string;
  created_by: string;
  assigned_to?: string;
  parameters: Record<string, any>;
  results?: Record<string, any>;
  error_details?: string;
  tags?: Record<string, string>;
  timeout_seconds?: number;
  retry_attempts: number;
  max_retries: number;
  dependencies?: string[];
  queue_name?: string;
  estimated_duration?: number;
  actual_duration?: number;
  resource_usage?: ResourceUsage;
}

export interface ResourceUsage {
  memory_mb?: number;
  cpu_percent?: number;
  disk_mb?: number;
  network_mb?: number;
}

export enum JobType {
  DATA_PROCESSING = 'data_processing',
  ML_TRAINING = 'ml_training',
  ML_INFERENCE = 'ml_inference',
  THREAT_ANALYSIS = 'threat_analysis',
  NETWORK_SCAN = 'network_scan',
  CUSTOM = 'custom'
}

export enum JobStatus {
  PENDING = 'pending',
  QUEUED = 'queued',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
  TIMEOUT = 'timeout',
  RETRYING = 'retrying'
}

export enum JobPriority {
  LOW = 'low',
  NORMAL = 'normal',
  HIGH = 'high',
  CRITICAL = 'critical'
}

export interface JobCreateRequest {
  name: string;
  job_type: JobType;
  priority?: JobPriority;
  parameters?: Record<string, any>;
  timeout_seconds?: number;
  max_retries?: number;
  tags?: Record<string, string>;
  dependencies?: string[];
  scheduled_for?: string;
}

export interface JobUpdateRequest {
  name?: string;
  priority?: JobPriority;
  parameters?: Record<string, any>;
  tags?: Record<string, string>;
}

export interface JobQuery {
  status?: JobStatus[];
  job_type?: JobType[];
  priority?: JobPriority[];
  created_by?: string;
  assigned_to?: string;
  created_after?: string;
  created_before?: string;
  search?: string;
  page?: number;
  limit?: number;
  sort_by?: string;
  sort_desc?: boolean;
}

export interface JobStatistics {
  total_jobs: number;
  jobs_by_status: Record<JobStatus, number>;
  jobs_by_type: Record<JobType, number>;
  jobs_by_priority: Record<JobPriority, number>;
  average_execution_time: number;
  success_rate: number;
  queue_sizes: Record<string, number>;
  resource_utilization: {
    avg_memory_mb: number;
    avg_cpu_percent: number;
    peak_memory_mb: number;
    peak_cpu_percent: number;
  };
  execution_metrics: {
    completed_last_hour: number;
    completed_last_day: number;
    failed_last_hour: number;
    failed_last_day: number;
  };
}

export interface JobHealthStatus {
  status: 'healthy' | 'warning' | 'critical';
  message: string;
  details: {
    active_workers: number;
    queue_backlog: number;
    failed_jobs_last_hour: number;
    avg_response_time: number;
    disk_usage_percent: number;
    memory_usage_percent: number;
  };
  checks: Array<{
    name: string;
    status: 'pass' | 'fail' | 'warning';
    message: string;
    timestamp: string;
  }>;
}

export interface BatchJobRequest {
  jobs: JobCreateRequest[];
  run_in_parallel?: boolean;
  stop_on_first_failure?: boolean;
  max_concurrent_jobs?: number;
}

export interface BatchJobResponse {
  batch_id: string;
  total_jobs: number;
  created_jobs: number;
  failed_jobs: number;
  job_ids: string[];
  errors: Array<{
    index: number;
    error: string;
  }>;
}

class JobManagementService {
  private readonly baseUrl = '/api/job-manager';

  /**
   * Get all jobs with optional filtering and pagination
   */
  async getJobs(query?: JobQuery): Promise<PaginatedResponse<Job>> {
    const params = new URLSearchParams();
    
    if (query) {
      if (query.status) params.append('status', query.status.join(','));
      if (query.job_type) params.append('job_type', query.job_type.join(','));
      if (query.priority) params.append('priority', query.priority.join(','));
      if (query.created_by) params.append('created_by', query.created_by);
      if (query.assigned_to) params.append('assigned_to', query.assigned_to);
      if (query.created_after) params.append('created_after', query.created_after);
      if (query.created_before) params.append('created_before', query.created_before);
      if (query.search) params.append('search', query.search);
      if (query.page) params.append('page', query.page.toString());
      if (query.limit) params.append('limit', query.limit.toString());
      if (query.sort_by) params.append('sort_by', query.sort_by);
      if (query.sort_desc !== undefined) params.append('sort_desc', query.sort_desc.toString());
    }

    const response = await apiClient.get<ApiResponse<PaginatedResponse<Job>>>(
      `${this.baseUrl}/jobs?${params.toString()}`
    );
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    
    throw new Error(response.data.error || 'Failed to fetch jobs');
  }

  /**
   * Get a specific job by ID
   */
  async getJob(jobId: string): Promise<Job> {
    const response = await apiClient.get<ApiResponse<Job>>(
      `${this.baseUrl}/jobs/${jobId}`
    );
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    
    throw new Error(response.data.error || 'Failed to fetch job');
  }

  /**
   * Create a new job
   */
  async createJob(jobData: JobCreateRequest): Promise<Job> {
    const response = await apiClient.post<ApiResponse<Job>>(
      `${this.baseUrl}/jobs`,
      jobData
    );
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    
    throw new Error(response.data.error || 'Failed to create job');
  }

  /**
   * Update an existing job
   */
  async updateJob(jobId: string, updates: JobUpdateRequest): Promise<Job> {
    const response = await apiClient.put<ApiResponse<Job>>(
      `${this.baseUrl}/jobs/${jobId}`,
      updates
    );
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    
    throw new Error(response.data.error || 'Failed to update job');
  }

  /**
   * Delete a job
   */
  async deleteJob(jobId: string): Promise<void> {
    const response = await apiClient.delete<ApiResponse<void>>(
      `${this.baseUrl}/jobs/${jobId}`
    );
    
    if (!response.data.success) {
      throw new Error(response.data.error || 'Failed to delete job');
    }
  }

  /**
   * Start job execution
   */
  async startJob(jobId: string): Promise<Job> {
    const response = await apiClient.post<ApiResponse<Job>>(
      `${this.baseUrl}/jobs/${jobId}/start`
    );
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    
    throw new Error(response.data.error || 'Failed to start job');
  }

  /**
   * Stop/cancel job execution
   */
  async stopJob(jobId: string): Promise<Job> {
    const response = await apiClient.post<ApiResponse<Job>>(
      `${this.baseUrl}/jobs/${jobId}/stop`
    );
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    
    throw new Error(response.data.error || 'Failed to stop job');
  }

  /**
   * Retry a failed job
   */
  async retryJob(jobId: string): Promise<Job> {
    const response = await apiClient.post<ApiResponse<Job>>(
      `${this.baseUrl}/jobs/${jobId}/retry`
    );
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    
    throw new Error(response.data.error || 'Failed to retry job');
  }

  /**
   * Get job execution logs
   */
  async getJobLogs(jobId: string, page = 1, limit = 100): Promise<PaginatedResponse<any>> {
    const response = await apiClient.get<ApiResponse<PaginatedResponse<any>>>(
      `${this.baseUrl}/jobs/${jobId}/logs?page=${page}&limit=${limit}`
    );
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    
    throw new Error(response.data.error || 'Failed to fetch job logs');
  }

  /**
   * Get job statistics
   */
  async getJobStatistics(): Promise<JobStatistics> {
    const response = await apiClient.get<ApiResponse<JobStatistics>>(
      `${this.baseUrl}/jobs/statistics`
    );
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    
    throw new Error(response.data.error || 'Failed to fetch job statistics');
  }

  /**
   * Get system health status
   */
  async getHealthStatus(): Promise<JobHealthStatus> {
    const response = await apiClient.get<ApiResponse<JobHealthStatus>>(
      `${this.baseUrl}/jobs/health`
    );
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    
    throw new Error(response.data.error || 'Failed to fetch health status');
  }

  /**
   * Create multiple jobs in batch
   */
  async createBatchJobs(batchData: BatchJobRequest): Promise<BatchJobResponse> {
    const response = await apiClient.post<ApiResponse<BatchJobResponse>>(
      `${this.baseUrl}/jobs/batch`,
      batchData
    );
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    
    throw new Error(response.data.error || 'Failed to create batch jobs');
  }

  /**
   * Get jobs by type
   */
  async getJobsByType(jobType: JobType, page = 1, limit = 20): Promise<PaginatedResponse<Job>> {
    const response = await apiClient.get<ApiResponse<PaginatedResponse<Job>>>(
      `${this.baseUrl}/jobs/types/${jobType}?page=${page}&limit=${limit}`
    );
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    
    throw new Error(response.data.error || 'Failed to fetch jobs by type');
  }

  /**
   * Get running jobs
   */
  async getRunningJobs(): Promise<Job[]> {
    const result = await this.getJobs({
      status: [JobStatus.RUNNING],
      limit: 100
    });
    
    return result.items;
  }

  /**
   * Get recent jobs (last 24 hours)
   */
  async getRecentJobs(limit = 50): Promise<Job[]> {
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    
    const result = await this.getJobs({
      created_after: yesterday.toISOString(),
      limit,
      sort_by: 'created_at',
      sort_desc: true
    });
    
    return result.items;
  }

  /**
   * Get failed jobs requiring attention
   */
  async getFailedJobs(): Promise<Job[]> {
    const result = await this.getJobs({
      status: [JobStatus.FAILED, JobStatus.TIMEOUT],
      limit: 100,
      sort_by: 'updated_at',
      sort_desc: true
    });
    
    return result.items;
  }

  /**
   * Search jobs by name or description
   */
  async searchJobs(searchTerm: string, page = 1, limit = 20): Promise<PaginatedResponse<Job>> {
    return this.getJobs({
      search: searchTerm,
      page,
      limit,
      sort_by: 'updated_at',
      sort_desc: true
    });
  }

  /**
   * Get job execution timeline for a specific job
   */
  async getJobTimeline(jobId: string): Promise<any[]> {
    const response = await apiClient.get<ApiResponse<any[]>>(
      `${this.baseUrl}/jobs/${jobId}/timeline`
    );
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    
    throw new Error(response.data.error || 'Failed to fetch job timeline');
  }

  /**
   * Export jobs data
   */
  async exportJobs(query?: JobQuery, format: 'csv' | 'json' = 'csv'): Promise<void> {
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
      `${this.baseUrl}/jobs/export?${params.toString()}`,
      `jobs_export_${new Date().toISOString().split('T')[0]}.${format}`
    );
  }

  /**
   * Cancel multiple jobs
   */
  async cancelJobs(jobIds: string[]): Promise<{ cancelled: string[]; failed: string[] }> {
    const response = await apiClient.post<ApiResponse<{ cancelled: string[]; failed: string[] }>>(
      `${this.baseUrl}/jobs/cancel-batch`,
      { job_ids: jobIds }
    );
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    
    throw new Error(response.data.error || 'Failed to cancel jobs');
  }

  /**
   * Get job queue information
   */
  async getQueueInfo(): Promise<Record<string, any>> {
    const response = await apiClient.get<ApiResponse<Record<string, any>>>(
      `${this.baseUrl}/jobs/queue-info`
    );
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    
    throw new Error(response.data.error || 'Failed to fetch queue information');
  }
}

export const jobManagementService = new JobManagementService();
