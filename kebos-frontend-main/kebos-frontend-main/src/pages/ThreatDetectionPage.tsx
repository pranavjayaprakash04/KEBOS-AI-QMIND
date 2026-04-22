import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';
import { 
  Shield, AlertTriangle, Eye, CheckCircle, Clock, 
  Filter, Search, Download, RefreshCw, MoreVertical 
} from 'lucide-react';
import { threatDetectionService, ThreatAlert, ThreatFilters } from '@/services/threatDetectionService';

export function ThreatDetectionPage() {
  const queryClient = useQueryClient();
  const [selectedAlert, setSelectedAlert] = useState<ThreatAlert | null>(null);
  const [filters, setFilters] = useState<ThreatFilters>({
    severity: [],
    status: [],
    search: '',
  });
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch threats using React Query
  const { data: alerts, isLoading, refetch } = useQuery({
    queryKey: ['threats', filters],
    queryFn: async () => {
      try {
        const response = await threatDetectionService.getThreats(filters);
        return response.data;
      } catch (error) {
        console.error('Failed to fetch threats:', error);
        
        // Return empty array instead of mock data
        return [];
      }
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  // Update threat status mutation
  const updateAlertStatusMutation = useMutation({
    mutationFn: async ({ alertId, status }: { alertId: string; status: string }) => {
      try {
        const response = await threatDetectionService.updateThreatStatus(alertId, status);
        return response.data;
      } catch (error) {
        console.error('Failed to update threat status:', error);
        throw error;
      }
    },
    onSuccess: (_, variables) => {
      toast.success(`Alert status updated to ${variables.status}`);
      queryClient.invalidateQueries({ queryKey: ['threats'] });
    },
    onError: (error) => {
      toast.error(`Failed to update alert status: ${error.message}`);
    },
  });

  // Format timestamp
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  // Format time ago
  const formatTimeAgo = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    
    if (seconds < 60) return `${seconds} seconds ago`;
    
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
    
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
    
    const days = Math.floor(hours / 24);
    return `${days} day${days !== 1 ? 's' : ''} ago`;
  };

  const getSeverityColor = (severity: ThreatAlert['severity']) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-600 text-white';
      case 'high':
        return 'bg-yellow-600 text-white';
      case 'medium':
        return 'bg-orange-500 text-white';
      case 'low':
        return 'bg-blue-500 text-white';
      default:
        return 'bg-gray-500 text-white';
    }
  };

  const getStatusColor = (status: ThreatAlert['status']) => {
    switch (status) {
      case 'active':
        return 'bg-red-50 text-red-600';
      case 'investigating':
        return 'bg-yellow-50 text-yellow-600';
      case 'false_positive':
        return 'bg-blue-50 text-blue-600';
      case 'resolved':
        return 'bg-green-50 text-green-600';
      default:
        return 'bg-gray-200 text-gray-700';
    }
  };

  // Handle filter change
  const handleFilterChange = (filterKey: string, value: any) => {
    setFilters(prev => ({ ...prev, [filterKey]: value }));
  };

  // Handle search query change
  const handleSearchChange = (query: string) => {
    setSearchQuery(query);
    setFilters(prev => ({ ...prev, search: query }));
  };

  // Handle alert selection
  const handleAlertSelect = (alert: ThreatAlert) => {
    setSelectedAlert(alert);
  };

  // Handle status update
  const handleStatusUpdate = (alertId: string, status: string) => {
    updateAlertStatusMutation.mutate({ alertId, status });
  };

  return (
    <div className="space-y-4">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-gray-800">Threat Detection</h1>
          <p className="text-base text-gray-600">Monitor and respond to security threats</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => refetch()}
            className="btn-ghost flex items-center gap-2 text-sm px-4 py-2 hover:text-white"
          >
            <RefreshCw className="h-5 w-5" />
            <span>Refresh</span>
          </button>
          <button className="btn-outline-primary flex items-center gap-2 text-sm px-4 py-2 hover:text-white">
            <Download className="h-5 w-5" />
            <span>Export</span>
          </button>
        </div>
      </div>

      {/* Threat Statistics Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 place-items-center">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="card-elegant p-4 w-full"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-700">Active Threats</p>
              <p className="text-3xl font-bold text-red-600">
                {(alerts ?? []).filter(a => a.status === 'active').length}
              </p>
            </div>
            <div className="p-3 bg-red-50 rounded-lg">
              <AlertTriangle className="h-7 w-7 text-red-600" />
            </div>
          </div>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
          className="card-elegant p-4 w-full"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-700">Under Investigation</p>
              <p className="text-3xl font-bold text-yellow-600">
                {(alerts ?? []).filter(a => a.status === 'investigating').length}
              </p>
            </div>
            <div className="p-3 bg-yellow-50 rounded-lg">
              <Eye className="h-7 w-7 text-yellow-600" />
            </div>
          </div>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
          className="card-elegant p-4 w-full"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-700">Resolved</p>
              <p className="text-3xl font-bold text-green-600">
                {(alerts ?? []).filter(a => a.status === 'resolved').length}
              </p>
            </div>
            <div className="p-3 bg-green-50 rounded-lg">
              <CheckCircle className="h-7 w-7 text-green-600" />
            </div>
          </div>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.3 }}
          className="card-elegant p-4 w-full"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-700">Total Alerts</p>
              <p className="text-3xl font-bold text-blue-600">{(alerts ?? []).length}</p>
            </div>
            <div className="p-3 bg-blue-50 rounded-lg">
              <Shield className="h-7 w-7 text-blue-600" />
            </div>
          </div>
        </motion.div>
      </div>

      {/* Filters and Search */}
      <div className="card-elegant p-4">
        <div className="flex flex-col lg:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => handleSearchChange(e.target.value)}
                placeholder="Search threats..."
                className="w-full pl-12 pr-4 py-3 text-base border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </div>

          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="min-w-40">
              <select
                value={(filters.severity?.[0] ?? 'all')}
                onChange={(e) =>
                  handleFilterChange(
                    'severity',
                    e.target.value === 'all' ? [] : [e.target.value]
                  )
                }
                className="w-full px-3 py-3 text-base border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="all">All Severities</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>

            <div className="min-w-40">
              <select
                value={(filters.status?.[0] ?? 'all')}
                onChange={(e) =>
                  handleFilterChange(
                    'status',
                    e.target.value === 'all' ? [] : [e.target.value]
                  )
                }
                className="w-full px-3 py-3 text-base border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="all">All Statuses</option>
                <option value="active">Active</option>
                <option value="investigating">Investigating</option>
                <option value="resolved">Resolved</option>
                <option value="false_positive">False Positive</option>
              </select>
            </div>

            <button className="btn-ghost flex items-center gap-2 text-base px-4 py-3 hover:text-white">
              <Filter className="h-5 w-5" />
              <span>More</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 place-items-center">
        {/* Threats List */}
        <div className="lg:col-span-1 w-full">
          <div className="card-elegant">
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-800">Recent Threats</h3>
              <p className="text-sm text-gray-600 mt-1">
                {isLoading ? 'Loading...' : `${(alerts ?? []).length} total alerts`}
              </p>
            </div>
            
            {isLoading ? (
              <div className="flex justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
              </div>
            ) : alerts && alerts.length > 0 ? (
              <div className="max-h-[calc(100vh-400px)] overflow-y-auto">
                {(alerts ?? []).map((alert) => (
                  <motion.div 
                    key={alert.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.2 }}
                    onClick={() => handleAlertSelect(alert)}
                    className={`p-4 border-b border-gray-100 cursor-pointer transition-all duration-200 hover:bg-gray-50 ${
                      selectedAlert?.id === alert.id ? 'bg-blue-50 border-l-4 border-l-blue-600' : ''
                    }`}
                  >
                    <div className="flex justify-between items-start mb-3">
                      <h4 className={`font-medium text-gray-800 line-clamp-2 text-sm ${
                        selectedAlert?.id === alert.id ? 'text-blue-900' : ''
                      }`}>
                        {alert.title}
                      </h4>
                      <span className={`text-sm px-2 py-1 rounded-full ${getSeverityColor(alert.severity)}`}>
                        {alert.severity}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 line-clamp-2 mb-3">
                      {alert.description}
                    </p>
                    <div className="flex justify-between items-center text-sm">
                      <span className={`px-2 py-1 rounded-full ${getStatusColor(alert.status)}`}>
                        {alert.status}
                      </span>
                      <span className="text-gray-600 flex items-center gap-2">
                        <Clock className="h-4 w-4" />
                        <span>{formatTimeAgo(alert.timestamp)}</span>
                      </span>
                    </div>
                  </motion.div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-12">
                <Shield className="w-14 h-14 text-gray-300 mb-4" />
                <h3 className="text-lg font-medium text-gray-700 mb-2">No threats detected</h3>
                <p className="text-gray-600 text-center text-sm">
                  Your environment is secure. New threats will appear here.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Threat Details */}
        <div className="lg:col-span-2 w-full">
          <div className="card-elegant h-full">
            {selectedAlert ? (
              <div className="h-full flex flex-col">
                {/* Header */}
                <div className="p-4 border-b border-gray-200">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h2 className="text-xl font-semibold text-gray-800 mb-1">{selectedAlert.title}</h2>
                      <p className="text-gray-600 text-sm">{selectedAlert.description}</p>
                    </div>
                    <div className="flex items-center gap-3 ml-4">
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${getSeverityColor(selectedAlert.severity)}`}>
                        {selectedAlert.severity}
                      </span>
                      <button className="btn-ghost p-2 hover:text-white">
                        <MoreVertical className="h-5 w-5" />
                      </button>
                    </div>
                  </div>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {/* Basic Info */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h4 className="text-sm font-medium text-gray-700 mb-1">Detected</h4>
                      <p className="text-sm text-gray-800">{formatTimestamp(selectedAlert.timestamp)}</p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h4 className="text-sm font-medium text-gray-700 mb-1">Source</h4>
                      <p className="text-sm text-gray-800">{selectedAlert.source}</p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h4 className="text-sm font-medium text-gray-700 mb-1">Status</h4>
                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(selectedAlert.status)}`}>
                        {selectedAlert.status}
                      </span>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h4 className="text-sm font-medium text-gray-700 mb-1">Type</h4>
                      <p className="text-sm text-gray-800">{selectedAlert.type || 'Unknown'}</p>
                    </div>
                  </div>

                  {/* Affected Systems */}
                  {selectedAlert.affectedSystems && selectedAlert.affectedSystems.length > 0 && (
                    <div>
                      <h4 className="text-base font-semibold text-gray-800 mb-3">Affected Systems</h4>
                      <div className="flex flex-wrap gap-3">
                        {selectedAlert.affectedSystems.map((system, index) => (
                          <span key={index} className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm">
                            {system}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Indicators */}
                  {selectedAlert.indicators && selectedAlert.indicators.length > 0 && (
                    <div>
                      <h4 className="text-base font-semibold text-gray-800 mb-3">Threat Indicators</h4>
                      <ul className="space-y-1">
                        {selectedAlert.indicators.map((indicator, index) => (
                          <li key={index} className="flex items-start gap-3">
                            <div className="w-2 h-2 bg-red-500 rounded-full mt-2 flex-shrink-0"></div>
                            <span className="text-gray-700 text-sm">{indicator}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Mitigations */}
                  {selectedAlert.mitigations && selectedAlert.mitigations.length > 0 && (
                    <div>
                      <h4 className="text-base font-semibold text-gray-800 mb-3">Recommended Actions</h4>
                      <ul className="space-y-1">
                        {selectedAlert.mitigations.map((mitigation, index) => (
                          <li key={index} className="flex items-start gap-3">
                            <div className="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0"></div>
                            <span className="text-gray-700 text-sm">{mitigation}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="p-4 border-t border-gray-200 bg-gray-50">
                  <h4 className="text-base font-semibold text-gray-800 mb-3">Update Status</h4>
                  <div className="flex flex-wrap gap-3">
                    {['active', 'investigating', 'false_positive', 'resolved'].map((status) => (
                      <button
                        key={status}
                        onClick={() => handleStatusUpdate(selectedAlert.id, status)}
                        disabled={selectedAlert.status === status || updateAlertStatusMutation.isPending}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200 ${
                          selectedAlert.status === status 
                            ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                            : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 hover:text-white'
                        }`}
                      >
                        {status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-96">
                <Shield className="w-16 h-16 text-gray-300 mb-4" />
                <h3 className="text-lg font-semibold text-gray-700 mb-2">No threat selected</h3>
                <p className="text-gray-600 text-center max-w-md text-sm">
                  Select a threat from the list to view detailed information and take action.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
