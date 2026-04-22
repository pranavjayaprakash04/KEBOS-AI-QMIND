import { useState, useEffect } from 'react';
import { 
  jobManagementService, 
  Job, 
  JobStatus, 
  JobType, 
  JobPriority, 
  JobQuery
} from '@/services/jobManagementService';
import { toast } from 'react-hot-toast';

interface JobStats {
  totalJobs: number;
  runningJobs: number;
  completedJobs: number;
  failedJobs: number;
  avgExecutionTime: string;
  systemLoad: number;
}

export function JobManagerPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [stats, setStats] = useState<JobStats>({
    totalJobs: 0,
    runningJobs: 0,
    completedJobs: 0,
    failedJobs: 0,
    avgExecutionTime: '0s',
    systemLoad: 0
  });
  const [isLoading, setIsLoading] = useState(true);
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<string>('all');

  // Fetch jobs from API
  const fetchJobs = async () => {
    try {
      setIsLoading(true);
      
      const query: JobQuery = {
        page: 1,
        limit: 50,
        sort_by: 'updated_at',
        sort_desc: true
      };

      // Add filters if selected
      if (selectedStatus !== 'all') {
        query.status = [selectedStatus as JobStatus];
      }
      if (selectedType !== 'all') {
        query.job_type = [selectedType as JobType];
      }

      const result = await jobManagementService.getJobs(query);
      setJobs(result.items);
    } catch (err) {
      console.error('Failed to fetch jobs:', err);
      toast.error('Failed to fetch jobs');
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch statistics from API
  const fetchStatistics = async () => {
    try {
      const statistics = await jobManagementService.getJobStatistics();
      setStats({
        totalJobs: statistics.total_jobs,
        runningJobs: statistics.jobs_by_status[JobStatus.RUNNING] || 0,
        completedJobs: statistics.jobs_by_status[JobStatus.COMPLETED] || 0,
        failedJobs: statistics.jobs_by_status[JobStatus.FAILED] || 0,
        avgExecutionTime: formatDuration(statistics.average_execution_time),
        systemLoad: Math.round(statistics.resource_utilization.avg_cpu_percent)
      });
    } catch (err) {
      console.error('Failed to fetch statistics:', err);
    }
  };

  // Helper function to format duration
  const formatDuration = (seconds: number): string => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m ${Math.round(seconds % 60)}s`;
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  useEffect(() => {
    fetchJobs();
    fetchStatistics();
  }, [selectedStatus, selectedType]);

  // Refresh data every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchJobs();
      fetchStatistics();
    }, 30000);

    return () => clearInterval(interval);
  }, [selectedStatus, selectedType]);

  const getStatusColor = (status: JobStatus) => {
    switch (status) {
      case JobStatus.RUNNING:
        return 'bg-blue-600 text-white';
      case JobStatus.COMPLETED:
        return 'bg-green-600 text-white';
      case JobStatus.FAILED:
        return 'bg-red-600 text-white';
      case JobStatus.PENDING:
      case JobStatus.QUEUED:
        return 'bg-yellow-600 text-gray-900';
      case JobStatus.CANCELLED:
        return 'bg-gray-500 text-white';
      default:
        return 'bg-gray-500 text-white';
    }
  };

  const getPriorityColor = (priority: JobPriority) => {
    switch (priority) {
      case JobPriority.CRITICAL:
        return 'text-red-600';
      case JobPriority.HIGH:
        return 'text-yellow-600';
      case JobPriority.NORMAL:
        return 'text-blue-600';
      case JobPriority.LOW:
        return 'text-gray-600';
      default:
        return 'text-gray-600';
    }
  };

  const getTypeIcon = (type: JobType) => {
    switch (type) {
      case JobType.NETWORK_SCAN:
      case JobType.THREAT_ANALYSIS:
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        );
      case JobType.DATA_PROCESSING:
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        );
      case JobType.ML_TRAINING:
      case JobType.ML_INFERENCE:
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
        );
      default:
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        );
    }
  };

  const filteredJobs = jobs.filter(job => {
    const matchesStatus = selectedStatus === 'all' || job.status === selectedStatus;
    const matchesType = selectedType === 'all' || job.job_type === selectedType;
    return matchesStatus && matchesType;
  });

  const handleCancelJob = async (jobId: string) => {
    try {
      await jobManagementService.stopJob(jobId);
      await fetchJobs(); // Refresh the list
      toast.success('Job cancelled successfully');
    } catch (err) {
      toast.error('Failed to cancel job');
    }
  };

  const handleRetryJob = async (jobId: string) => {
    try {
      await jobManagementService.retryJob(jobId);
      await fetchJobs(); // Refresh the list
      toast.success('Job retry initiated');
    } catch (err) {
      toast.error('Failed to retry job');
    }
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-black mb-2">Job Manager</h1>
          <p className="text-black">Monitor and manage background jobs and tasks</p>
        </div>
        <div className="flex space-x-2">
          <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors duration-200">
            Create Job
          </button>
          <button className="bg-gray-100 hover:bg-gray-200 text-black px-4 py-2 rounded-lg font-medium border border-gray-300 hover:shadow-md transition-all duration-200">
            Queue Settings
          </button>
        </div>
      </div>

      {/* Job Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-6 mb-8">
        <div className="bg-white rounded-lg p-6 border border-gray-200 shadow-sm">
          <div className="text-center">
            <p className="text-2xl font-bold text-blue-600">{stats.totalJobs}</p>
            <p className="text-black text-sm">Total Jobs</p>
          </div>
        </div>
        <div className="bg-white rounded-lg p-6 border border-gray-200 shadow-sm">
          <div className="text-center">
            <p className="text-2xl font-bold text-yellow-600">{stats.runningJobs}</p>
            <p className="text-black text-sm">Running</p>
          </div>
        </div>
        <div className="bg-white rounded-lg p-6 border border-gray-200 shadow-sm">
          <div className="text-center">
            <p className="text-2xl font-bold text-green-600">{stats.completedJobs}</p>
            <p className="text-black text-sm">Completed</p>
          </div>
        </div>
        <div className="bg-white rounded-lg p-6 border border-gray-200 shadow-sm">
          <div className="text-center">
            <p className="text-2xl font-bold text-red-600">{stats.failedJobs}</p>
            <p className="text-black text-sm">Failed</p>
          </div>
        </div>
        <div className="bg-white rounded-lg p-6 border border-gray-200 shadow-sm">
          <div className="text-center">
            <p className="text-2xl font-bold text-blue-600">{stats.avgExecutionTime}</p>
            <p className="text-black text-sm">Avg Time</p>
          </div>
        </div>
        <div className="bg-white rounded-lg p-6 border border-gray-200 shadow-sm">
          <div className="text-center">
            <p className="text-2xl font-bold text-blue-600">{stats.systemLoad}%</p>
            <p className="text-gray-600 text-sm">System Load</p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg p-6 border border-gray-200 shadow-sm mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0 md:space-x-4">
          <div className="flex space-x-4">
            <div>
              <label className="block text-sm font-medium text-gray-900 mb-1">Status</label>
              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">All Status</option>
                <option value={JobStatus.PENDING}>Pending</option>
                <option value={JobStatus.QUEUED}>Queued</option>
                <option value={JobStatus.RUNNING}>Running</option>
                <option value={JobStatus.COMPLETED}>Completed</option>
                <option value={JobStatus.FAILED}>Failed</option>
                <option value={JobStatus.CANCELLED}>Cancelled</option>
                <option value={JobStatus.TIMEOUT}>Timeout</option>
                <option value={JobStatus.RETRYING}>Retrying</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-900 mb-1">Type</label>
              <select
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">All Types</option>
                <option value={JobType.DATA_PROCESSING}>Data Processing</option>
                <option value={JobType.ML_TRAINING}>ML Training</option>
                <option value={JobType.ML_INFERENCE}>ML Inference</option>
                <option value={JobType.THREAT_ANALYSIS}>Threat Analysis</option>
                <option value={JobType.NETWORK_SCAN}>Network Scan</option>
                <option value={JobType.CUSTOM}>Custom</option>
              </select>
            </div>
          </div>
          <div className="text-sm text-gray-600">
            Showing {filteredJobs.length} of {jobs.length} jobs
          </div>
        </div>
      </div>

      {/* Jobs List */}
      <div className="space-y-4">
        {filteredJobs.map((job) => (
          <div key={job.id} className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-start space-x-4">
                <div className="p-2 bg-blue-50 rounded-lg">
                  {getTypeIcon(job.job_type)}
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{job.name}</h3>
                  <p className="text-gray-600 text-sm">
                    {job.job_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} Job
                  </p>
                  <div className="flex items-center space-x-4 mt-2">
                    <span className="text-sm text-gray-600">Created by: {job.created_by}</span>
                    <span className={`text-sm font-medium ${getPriorityColor(job.priority)}`}>
                      {job.priority.charAt(0).toUpperCase() + job.priority.slice(1)} Priority
                    </span>
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(job.status)}`}>
                  {job.status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </span>
                <div className="relative">
                  <button className="p-1 text-gray-600 hover:text-gray-900">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>

            {/* Progress Bar */}
            {(job.status === JobStatus.RUNNING || job.status === JobStatus.QUEUED) && (
              <div className="mb-4">
                <div className="flex justify-between text-sm text-gray-600 mb-1">
                  <span>Progress</span>
                  <span>{job.progress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                    style={{ width: `${job.progress}%` }}
                  ></div>
                </div>
              </div>
            )}

            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4 text-sm text-gray-600">
                <span>Created: {new Date(job.created_at).toLocaleString()}</span>
                <span>Updated: {new Date(job.updated_at).toLocaleString()}</span>
                {job.started_at && (
                  <span>Started: {new Date(job.started_at).toLocaleString()}</span>
                )}
                {job.completed_at && (
                  <span>Completed: {new Date(job.completed_at).toLocaleString()}</span>
                )}
              </div>
              <div className="flex items-center space-x-2">
                {job.tags && Object.entries(job.tags).map(([key, value]) => (
                  <span key={key} className="px-2 py-1 bg-blue-50 text-blue-600 text-xs rounded-full">
                    {key}: {value}
                  </span>
                ))}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center space-x-2 mt-4 pt-4 border-t border-gray-200">
              <button className="text-blue-600 hover:text-blue-700 text-sm font-medium">
                View Details
              </button>
              <button className="text-blue-600 hover:text-blue-700 text-sm font-medium">
                View Logs
              </button>
              {(job.status === JobStatus.RUNNING || job.status === JobStatus.QUEUED) && (
                <button 
                  onClick={() => handleCancelJob(job.id)}
                  className="text-red-600 hover:text-red-700 text-sm font-medium"
                >
                  Cancel
                </button>
              )}
              {(job.status === JobStatus.FAILED || job.status === JobStatus.TIMEOUT) && (
                <button 
                  onClick={() => handleRetryJob(job.id)}
                  className="text-yellow-600 hover:text-yellow-700 text-sm font-medium"
                >
                  Retry
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
