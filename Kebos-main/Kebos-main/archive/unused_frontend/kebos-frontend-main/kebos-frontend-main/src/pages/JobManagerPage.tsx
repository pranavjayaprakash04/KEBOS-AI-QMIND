import { useState, useEffect } from "react";
import CustomDropdown from "../components/CustomDropdown";

interface Job {
  id: string;
  name: string;
  type: "scan" | "analysis" | "training" | "monitoring";
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  priority: "low" | "medium" | "high" | "critical";
  progress: number;
  createdAt: string;
  updatedAt: string;
  estimatedCompletion: string;
  owner: string;
  description: string;
  tags: string[];
}

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
  const [stats, _setStats] = useState<JobStats>({
    totalJobs: 156,
    runningJobs: 8,
    completedJobs: 143,
    failedJobs: 5,
    avgExecutionTime: "12m 34s",
    systemLoad: 67,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [selectedStatus, setSelectedStatus] = useState<string>("all");
  const [selectedType, setSelectedType] = useState<string>("all");

  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setJobs([
        {
          id: "1",
          name: "Daily Threat Analysis",
          type: "analysis",
          status: "running",
          priority: "high",
          progress: 67,
          createdAt: "2024-01-15T09:00:00Z",
          updatedAt: "2024-01-15T10:30:00Z",
          estimatedCompletion: "2024-01-15T11:15:00Z",
          owner: "analyst@company.com",
          description:
            "Comprehensive analysis of daily threat intelligence data",
          tags: ["threat-intel", "daily", "scheduled"],
        },
        {
          id: "2",
          name: "ML Model Training",
          type: "training",
          status: "running",
          priority: "medium",
          progress: 23,
          createdAt: "2024-01-15T08:00:00Z",
          updatedAt: "2024-01-15T10:25:00Z",
          estimatedCompletion: "2024-01-15T14:30:00Z",
          owner: "mlops@company.com",
          description:
            "Training updated threat detection model with latest dataset",
          tags: ["ml", "training", "threat-detection"],
        },
        {
          id: "3",
          name: "Network Vulnerability Scan",
          type: "scan",
          status: "completed",
          priority: "medium",
          progress: 100,
          createdAt: "2024-01-15T07:00:00Z",
          updatedAt: "2024-01-15T09:45:00Z",
          estimatedCompletion: "2024-01-15T09:45:00Z",
          owner: "security@company.com",
          description: "Weekly network infrastructure vulnerability assessment",
          tags: ["vulnerability", "network", "weekly"],
        },
        {
          id: "4",
          name: "Real-time Monitoring Setup",
          type: "monitoring",
          status: "pending",
          priority: "critical",
          progress: 0,
          createdAt: "2024-01-15T10:00:00Z",
          updatedAt: "2024-01-15T10:00:00Z",
          estimatedCompletion: "2024-01-15T12:00:00Z",
          owner: "admin@company.com",
          description:
            "Initialize real-time threat monitoring for new endpoints",
          tags: ["monitoring", "real-time", "endpoints"],
        },
        {
          id: "5",
          name: "Attack Simulation Campaign",
          type: "scan",
          status: "failed",
          priority: "high",
          progress: 45,
          createdAt: "2024-01-15T06:00:00Z",
          updatedAt: "2024-01-15T08:30:00Z",
          estimatedCompletion: "2024-01-15T10:00:00Z",
          owner: "redteam@company.com",
          description: "Simulated attack campaign to test defense mechanisms",
          tags: ["attack-sim", "testing", "red-team"],
        },
      ]);
      setIsLoading(false);
    }, 1000);
  }, []);

  const getStatusColor = (status: Job["status"]) => {
    switch (status) {
      case "running":
        return "bg-primary text-white";
      case "completed":
        return "bg-success text-white";
      case "failed":
        return "bg-error text-white";
      case "pending":
        return "bg-warning text-text-primary";
      case "cancelled":
        return "bg-gray-500 text-white";
      default:
        return "bg-gray-500 text-white";
    }
  };

  const getPriorityColor = (priority: Job["priority"]) => {
    switch (priority) {
      case "critical":
        return "text-error";
      case "high":
        return "text-warning";
      case "medium":
        return "text-primary";
      case "low":
        return "text-text-secondary";
      default:
        return "text-text-secondary";
    }
  };

  const getTypeIcon = (type: Job["type"]) => {
    switch (type) {
      case "scan":
        return (
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        );
      case "analysis":
        return (
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
        );
      case "training":
        return (
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
            />
          </svg>
        );
      case "monitoring":
        return (
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
            />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
            />
          </svg>
        );
      default:
        return (
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
        );
    }
  };

  const filteredJobs = jobs.filter((job) => {
    const matchesStatus =
      selectedStatus === "all" || job.status === selectedStatus;
    const matchesType = selectedType === "all" || job.type === selectedType;
    return matchesStatus && matchesType;
  });

  const handleCancelJob = (jobId: string) => {
    setJobs(
      jobs.map((job) =>
        job.id === jobId ? { ...job, status: "cancelled" as const } : job
      )
    );
  };

  const handleRetryJob = (jobId: string) => {
    setJobs(
      jobs.map((job) =>
        job.id === jobId
          ? { ...job, status: "pending" as const, progress: 0 }
          : job
      )
    );
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  // Dropdown options
  const statusOptions = [
    { value: "all", label: "All Status" },
    { value: "pending", label: "Pending" },
    { value: "running", label: "Running" },
    { value: "completed", label: "Completed" },
    { value: "failed", label: "Failed" },
    { value: "cancelled", label: "Cancelled" },
  ];
  const typeOptions = [
    { value: "all", label: "All Types" },
    { value: "scan", label: "Scan" },
    { value: "analysis", label: "Analysis" },
    { value: "training", label: "Training" },
    { value: "monitoring", label: "Monitoring" },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm border-b border-slate-200/50 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg shadow-lg">
              <svg
                className="w-6 h-6 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z"
                />
              </svg>
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">
                Job Manager
              </h1>
              <p className="text-slate-600">
                Monitor and manage background jobs and tasks
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Actions */}
        <div className="flex justify-end space-x-4">
          <button className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-lg font-medium shadow-lg hover:shadow-xl transition-all duration-200">
            Create Job
          </button>
          <button className="px-6 py-3 bg-white/80 backdrop-blur-sm text-slate-700 rounded-lg font-medium border border-slate-200 hover:shadow-lg transition-all duration-200">
            Queue Settings
          </button>
        </div>

        {/* Statistics Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-6">
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-6 hover:shadow-2xl transition-all duration-200">
            <div className="text-center">
              <p className="text-3xl font-bold text-indigo-600">
                {stats.totalJobs}
              </p>
              <p className="text-slate-600 text-sm font-medium">Total Jobs</p>
            </div>
          </div>
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-6 hover:shadow-2xl transition-all duration-200">
            <div className="text-center">
              <p className="text-3xl font-bold text-warning">
                {stats.runningJobs}
              </p>
              <p className="text-slate-600 text-sm font-medium">Running</p>
            </div>
          </div>
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-6 hover:shadow-2xl transition-all duration-200">
            <div className="text-center">
              <p className="text-3xl font-bold text-success">
                {stats.completedJobs}
              </p>
              <p className="text-slate-600 text-sm font-medium">Completed</p>
            </div>
          </div>
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-6 hover:shadow-2xl transition-all duration-200">
            <div className="text-center">
              <p className="text-3xl font-bold text-error">
                {stats.failedJobs}
              </p>
              <p className="text-slate-600 text-sm font-medium">Failed</p>
            </div>
          </div>
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-6 hover:shadow-2xl transition-all duration-200">
            <div className="text-center">
              <p className="text-3xl font-bold text-primary">
                {stats.avgExecutionTime}
              </p>
              <p className="text-slate-600 text-sm font-medium">Avg Time</p>
            </div>
          </div>
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-6 hover:shadow-2xl transition-all duration-200">
            <div className="text-center">
              <p className="text-3xl font-bold text-primary">
                {stats.systemLoad}%
              </p>
              <p className="text-text-secondary text-sm font-medium">
                System Load
              </p>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-8 relative z-40">
          <div className="flex flex-col md:flex-row md:items-end md:justify-between space-y-4 md:space-y-0 md:space-x-6">
            <div className="flex flex-col sm:flex-row gap-6">
              <div className="min-w-[240px] relative z-50">
                <CustomDropdown
                  label="Status"
                  value={selectedStatus}
                  options={statusOptions}
                  onChange={setSelectedStatus}
                />
              </div>
              <div className="min-w-[240px] relative z-50">
                <CustomDropdown
                  label="Type"
                  value={selectedType}
                  options={typeOptions}
                  onChange={setSelectedType}
                />
              </div>
            </div>
            <div className="text-sm text-slate-600 font-medium">
              Showing {filteredJobs.length} of {jobs.length} jobs
            </div>
          </div>
        </div>

        {/* Jobs List */}
        <div className="space-y-4">
          {filteredJobs.map((job) => (
            <div
              key={job.id}
              className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-6 hover:shadow-2xl transition-all duration-200 relative z-10"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-start space-x-4">
                  <div className="p-3 bg-indigo-100 rounded-xl">
                    {getTypeIcon(job.type)}
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-text-primary">
                      {job.name}
                    </h3>
                    <p className="text-text-secondary text-sm">
                      {job.description}
                    </p>
                    <div className="flex items-center space-x-4 mt-2">
                      <span className="text-sm text-text-secondary">
                        Owner: {job.owner}
                      </span>
                      <span
                        className={`text-sm font-medium ${getPriorityColor(job.priority)}`}
                      >
                        {job.priority.charAt(0).toUpperCase() +
                          job.priority.slice(1)}{" "}
                        Priority
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(job.status)}`}
                  >
                    {job.status}
                  </span>
                </div>
              </div>

              {/* Progress Bar */}
              {job.status === "running" && (
                <div className="mb-4">
                  <div className="flex justify-between text-sm text-text-secondary mb-1">
                    <span>Progress</span>
                    <span>{job.progress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-primary h-2 rounded-full transition-all duration-300"
                      style={{ width: `${job.progress}%` }}
                    ></div>
                  </div>
                </div>
              )}

              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4 text-sm text-text-secondary">
                  <span>
                    Created: {new Date(job.createdAt).toLocaleString()}
                  </span>
                  <span>
                    Updated: {new Date(job.updatedAt).toLocaleString()}
                  </span>
                  {job.status === "running" && (
                    <span>
                      ETA: {new Date(job.estimatedCompletion).toLocaleString()}
                    </span>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  {job.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-1 bg-primary bg-opacity-10 text-primary text-xs rounded-full"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center space-x-2 mt-4 pt-4 border-t border-border">
                <button className="text-primary hover:text-primary-dark text-sm font-medium">
                  View Details
                </button>
                <button className="text-primary hover:text-primary-dark text-sm font-medium">
                  View Logs
                </button>
                {job.status === "running" && (
                  <button
                    onClick={() => handleCancelJob(job.id)}
                    className="text-error hover:text-error-dark text-sm font-medium"
                  >
                    Cancel
                  </button>
                )}
                {job.status === "failed" && (
                  <button
                    onClick={() => handleRetryJob(job.id)}
                    className="text-warning hover:text-warning-dark text-sm font-medium"
                  >
                    Retry
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Jobs List */}
        <div className="space-y-4">
          {filteredJobs.map((job) => (
            <div
              key={job.id}
              className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-6 hover:shadow-2xl transition-all duration-200 z-0 relative"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-start space-x-4">
                  <div className="p-3 bg-indigo-100 rounded-xl">
                    {getTypeIcon(job.type)}
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-text-primary">
                      {job.name}
                    </h3>
                    <p className="text-text-secondary text-sm">
                      {job.description}
                    </p>
                    <div className="flex items-center space-x-4 mt-2">
                      <span className="text-sm text-text-secondary">
                        Owner: {job.owner}
                      </span>
                      <span
                        className={`text-sm font-medium ${getPriorityColor(job.priority)}`}
                      >
                        {job.priority.charAt(0).toUpperCase() +
                          job.priority.slice(1)}{" "}
                        Priority
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(job.status)}`}
                  >
                    {job.status}
                  </span>
                </div>
              </div>

              {/* Progress Bar */}
              {job.status === "running" && (
                <div className="mb-4">
                  <div className="flex justify-between text-sm text-text-secondary mb-1">
                    <span>Progress</span>
                    <span>{job.progress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-primary h-2 rounded-full transition-all duration-300"
                      style={{ width: `${job.progress}%` }}
                    ></div>
                  </div>
                </div>
              )}

              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4 text-sm text-text-secondary">
                  <span>
                    Created: {new Date(job.createdAt).toLocaleString()}
                  </span>
                  <span>
                    Updated: {new Date(job.updatedAt).toLocaleString()}
                  </span>
                  {job.status === "running" && (
                    <span>
                      ETA: {new Date(job.estimatedCompletion).toLocaleString()}
                    </span>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  {job.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-1 bg-primary bg-opacity-10 text-primary text-xs rounded-full"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center space-x-2 mt-4 pt-4 border-t border-border">
                <button className="text-primary hover:text-primary-dark text-sm font-medium">
                  View Details
                </button>
                <button className="text-primary hover:text-primary-dark text-sm font-medium">
                  View Logs
                </button>
                {job.status === "running" && (
                  <button
                    onClick={() => handleCancelJob(job.id)}
                    className="text-error hover:text-error-dark text-sm font-medium"
                  >
                    Cancel
                  </button>
                )}
                {job.status === "failed" && (
                  <button
                    onClick={() => handleRetryJob(job.id)}
                    className="text-warning hover:text-warning-dark text-sm font-medium"
                  >
                    Retry
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
              

