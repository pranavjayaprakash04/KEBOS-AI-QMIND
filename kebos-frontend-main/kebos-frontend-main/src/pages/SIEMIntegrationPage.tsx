import React, { useState, useEffect, useCallback } from 'react';
import { Plus, Shield, Server, Activity, AlertTriangle, CheckCircle, XCircle, Search, Filter, Download, RefreshCw, Eye, Settings } from 'lucide-react';
import { toast } from 'react-hot-toast';
import {
  siemIntegrationService,
  SIEMConfig,
  SIEMEvent,
  SIEMHealthStatus,
  SIEMStatistics,
  SIEMType,
  SIEMAuthType,
  SIEMEventSeverity,
  SIEMEventCategory,
  SIEMConnectionStatus,
  SIEMEventQuery,
  SIEMConfigCreateRequest,
  SIEMConfigUpdateRequest
} from '@/services/siemIntegrationService';

const SIEMIntegrationPage: React.FC = () => {
  const [configs, setConfigs] = useState<SIEMConfig[]>([]);
  const [events, setEvents] = useState<SIEMEvent[]>([]);
  const [statistics, setStatistics] = useState<SIEMStatistics | null>(null);
  const [healthStatuses, setHealthStatuses] = useState<Record<string, SIEMHealthStatus>>({});
  
  const [loading, setLoading] = useState(true);
  const [configsLoading, setConfigsLoading] = useState(false);
  const [eventsLoading, setEventsLoading] = useState(false);
  const [statsLoading, setStatsLoading] = useState(false);
  
  const [activeTab, setActiveTab] = useState<'configs' | 'events' | 'stats'>('configs');
  const [selectedConfig, setSelectedConfig] = useState<string>('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingConfig, setEditingConfig] = useState<SIEMConfig | null>(null);
  
  // Event filtering
  const [eventFilters, setEventFilters] = useState<SIEMEventQuery>({
    page: 1,
    limit: 20,
    sort_by: 'timestamp',
    sort_desc: true
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  
  // Pagination
  const [totalEvents, setTotalEvents] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // Auto-refresh
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timeout | null>(null);

  const loadConfigs = useCallback(async () => {
    try {
      setConfigsLoading(true);
      const data = await siemIntegrationService.getConfigs();
      setConfigs(data);
      
      // Load health status for each config
      const healthPromises = data.map(async (config) => {
        if (config.id) {
          try {
            const health = await siemIntegrationService.getHealthStatus(config.id);
            return { configId: config.id, health };
          } catch (error) {
            console.warn(`Failed to load health for config ${config.id}:`, error);
            return null;
          }
        }
        return null;
      });
      
      const healthResults = await Promise.all(healthPromises);
      const healthMap: Record<string, SIEMHealthStatus> = {};
      healthResults.forEach((result) => {
        if (result) {
          healthMap[result.configId] = result.health;
        }
      });
      setHealthStatuses(healthMap);
      
    } catch (error) {
      console.error('Failed to load SIEM configurations:', error);
      toast.error('Failed to load SIEM configurations');
    } finally {
      setConfigsLoading(false);
    }
  }, []);

  const loadEvents = useCallback(async () => {
    try {
      setEventsLoading(true);
      const data = await siemIntegrationService.getEvents({
        ...eventFilters,
        search: searchTerm || undefined
      });
      setEvents(data.items);
      setTotalEvents(data.total);
      setCurrentPage(data.page);
      setTotalPages(data.pages);
    } catch (error) {
      console.error('Failed to load events:', error);
      toast.error('Failed to load events');
    } finally {
      setEventsLoading(false);
    }
  }, [eventFilters, searchTerm]);

  const loadStatistics = useCallback(async () => {
    try {
      setStatsLoading(true);
      const data = await siemIntegrationService.getStatistics();
      setStatistics(data);
    } catch (error) {
      console.error('Failed to load statistics:', error);
      toast.error('Failed to load statistics');
    } finally {
      setStatsLoading(false);
    }
  }, []);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadConfigs(),
        loadEvents(),
        loadStatistics()
      ]);
    } finally {
      setLoading(false);
    }
  }, [loadConfigs, loadEvents, loadStatistics]);

  // Initial load
  useEffect(() => {
    loadData();
  }, [loadData]);

  // Auto-refresh setup
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        if (activeTab === 'events') {
          loadEvents();
        } else if (activeTab === 'stats') {
          loadStatistics();
        }
      }, 30000); // Refresh every 30 seconds
      setRefreshInterval(interval);
      return () => clearInterval(interval);
    } else if (refreshInterval) {
      clearInterval(refreshInterval);
      setRefreshInterval(null);
    }
  }, [autoRefresh, activeTab, loadEvents, loadStatistics]);

  // Load events when filters change
  useEffect(() => {
    if (activeTab === 'events') {
      loadEvents();
    }
  }, [activeTab, eventFilters, searchTerm, loadEvents]);

  const handleCreateConfig = async (configData: SIEMConfigCreateRequest) => {
    try {
      await siemIntegrationService.createConfig(configData);
      toast.success('SIEM configuration created successfully');
      setShowCreateModal(false);
      loadConfigs();
    } catch (error) {
      console.error('Failed to create config:', error);
      toast.error('Failed to create SIEM configuration');
    }
  };

  const handleUpdateConfig = async (configId: string, updates: SIEMConfigUpdateRequest) => {
    try {
      await siemIntegrationService.updateConfig(configId, updates);
      toast.success('SIEM configuration updated successfully');
      setShowEditModal(false);
      setEditingConfig(null);
      loadConfigs();
    } catch (error) {
      console.error('Failed to update config:', error);
      toast.error('Failed to update SIEM configuration');
    }
  };

  const handleDeleteConfig = async (configId: string) => {
    if (!confirm('Are you sure you want to delete this SIEM configuration?')) {
      return;
    }
    
    try {
      await siemIntegrationService.deleteConfig(configId);
      toast.success('SIEM configuration deleted successfully');
      loadConfigs();
    } catch (error) {
      console.error('Failed to delete config:', error);
      toast.error('Failed to delete SIEM configuration');
    }
  };

  const handleTestConnection = async (configId: string) => {
    try {
      const health = await siemIntegrationService.testConnection(configId);
      setHealthStatuses(prev => ({ ...prev, [configId]: health }));
      
      if (health.status === SIEMConnectionStatus.CONNECTED) {
        toast.success('Connection test successful');
      } else {
        toast.error(`Connection test failed: ${health.error_message || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Failed to test connection:', error);
      toast.error('Failed to test connection');
    }
  };

  const getStatusColor = (status: SIEMConnectionStatus) => {
    switch (status) {
      case SIEMConnectionStatus.CONNECTED:
        return 'text-green-600';
      case SIEMConnectionStatus.DISCONNECTED:
        return 'text-red-600';
      case SIEMConnectionStatus.ERROR:
        return 'text-red-600';
      case SIEMConnectionStatus.TESTING:
        return 'text-yellow-600';
      case SIEMConnectionStatus.MAINTENANCE:
        return 'text-orange-600';
      default:
        return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: SIEMConnectionStatus) => {
    switch (status) {
      case SIEMConnectionStatus.CONNECTED:
        return <CheckCircle className="h-4 w-4" />;
      case SIEMConnectionStatus.DISCONNECTED:
      case SIEMConnectionStatus.ERROR:
        return <XCircle className="h-4 w-4" />;
      case SIEMConnectionStatus.TESTING:
        return <RefreshCw className="h-4 w-4 animate-spin" />;
      case SIEMConnectionStatus.MAINTENANCE:
        return <AlertTriangle className="h-4 w-4" />;
      default:
        return <AlertTriangle className="h-4 w-4" />;
    }
  };

  const getSeverityColor = (severity: SIEMEventSeverity) => {
    switch (severity) {
      case SIEMEventSeverity.CRITICAL:
        return 'bg-red-100 text-red-800';
      case SIEMEventSeverity.HIGH:
        return 'bg-orange-100 text-orange-800';
      case SIEMEventSeverity.MEDIUM:
        return 'bg-yellow-100 text-yellow-800';
      case SIEMEventSeverity.LOW:
        return 'bg-blue-100 text-blue-800';
      case SIEMEventSeverity.INFO:
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const handleExportEvents = async () => {
    try {
      await siemIntegrationService.exportEvents(eventFilters, 'csv');
      toast.success('Events exported successfully');
    } catch (error) {
      console.error('Failed to export events:', error);
      toast.error('Failed to export events');
    }
  };

  const handlePageChange = (page: number) => {
    setEventFilters(prev => ({ ...prev, page }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-500" />
        <span className="ml-2 text-gray-600">Loading SIEM integration data...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center">
            <Shield className="h-8 w-8 text-blue-600 mr-3" />
            SIEM Integration
          </h1>
          <p className="text-gray-600 mt-1">
            Manage security information and event management integrations
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded"
            />
            <span className="ml-2 text-sm text-gray-600">Auto-refresh</span>
          </label>
          <button
            onClick={loadData}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Statistics Cards */}
      {statistics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <Server className="h-8 w-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Configs</p>
                <p className="text-2xl font-bold text-gray-900">{statistics.total_configs}</p>
                <p className="text-xs text-gray-500">{statistics.active_configs} active</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <Activity className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Events</p>
                <p className="text-2xl font-bold text-gray-900">{statistics.total_events.toLocaleString()}</p>
                <p className="text-xs text-gray-500">{statistics.events_last_24h} in 24h</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <AlertTriangle className="h-8 w-8 text-red-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Critical Events</p>
                <p className="text-2xl font-bold text-gray-900">
                  {(statistics.events_by_severity[SIEMEventSeverity.CRITICAL] || 0) + 
                   (statistics.events_by_severity[SIEMEventSeverity.HIGH] || 0)}
                </p>
                <p className="text-xs text-gray-500">Requiring attention</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <CheckCircle className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Health Status</p>
                <p className="text-2xl font-bold text-gray-900">{statistics.connection_health.healthy}</p>
                <p className="text-xs text-gray-500">
                  {statistics.connection_health.failed} failed, {statistics.connection_health.degraded} degraded
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'configs', label: 'Configurations', icon: Settings },
            { id: 'events', label: 'Events', icon: Activity },
            { id: 'stats', label: 'Statistics', icon: Shield }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <tab.icon className="h-4 w-4 mr-2" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'configs' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold text-gray-900">SIEM Configurations</h2>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center"
            >
              <Plus className="h-4 w-4 mr-2" />
              Add Configuration
            </button>
          </div>

          {configsLoading ? (
            <div className="flex items-center justify-center h-32">
              <RefreshCw className="h-6 w-6 animate-spin text-blue-500" />
              <span className="ml-2 text-gray-600">Loading configurations...</span>
            </div>
          ) : configs.length === 0 ? (
            <div className="text-center py-12">
              <Server className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No SIEM configurations</h3>
              <p className="text-gray-600 mb-4">Get started by adding your first SIEM configuration.</p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Add Configuration
              </button>
            </div>
          ) : (
            <div className="grid gap-4">
              {configs.map((config) => (
                <div key={config.id} className="bg-white p-6 rounded-lg shadow border">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center">
                        <h3 className="text-lg font-medium text-gray-900">{config.display_name || config.name}</h3>
                        {config.is_primary && (
                          <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded">
                            Primary
                          </span>
                        )}
                        <span className={`ml-2 px-2 py-1 text-xs font-medium rounded ${
                          config.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                        }`}>
                          {config.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                      <p className="text-gray-600 mt-1">{config.description}</p>
                      <div className="flex items-center mt-2 space-x-4">
                        <span className="text-sm text-gray-500">
                          <strong>Type:</strong> {config.siem_type}
                        </span>
                        <span className="text-sm text-gray-500">
                          <strong>Auth:</strong> {config.auth_type}
                        </span>
                        <span className="text-sm text-gray-500">
                          <strong>Endpoint:</strong> {config.endpoint_url}
                        </span>
                      </div>
                      {healthStatuses[config.id!] && (
                        <div className="flex items-center mt-2">
                          <span className={`flex items-center text-sm ${getStatusColor(healthStatuses[config.id!].status)}`}>
                            {getStatusIcon(healthStatuses[config.id!].status)}
                            <span className="ml-1 capitalize">{healthStatuses[config.id!].status}</span>
                          </span>
                          {healthStatuses[config.id!].response_time_ms && (
                            <span className="ml-4 text-sm text-gray-500">
                              Response: {healthStatuses[config.id!].response_time_ms}ms
                            </span>
                          )}
                          <span className="ml-4 text-sm text-gray-500">
                            Last check: {formatTimestamp(healthStatuses[config.id!].last_check)}
                          </span>
                        </div>
                      )}
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleTestConnection(config.id!)}
                        className="px-3 py-1 bg-green-100 text-green-700 rounded hover:bg-green-200"
                      >
                        Test
                      </button>
                      <button
                        onClick={() => {
                          setEditingConfig(config);
                          setShowEditModal(true);
                        }}
                        className="px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDeleteConfig(config.id!)}
                        className="px-3 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'events' && (
        <div className="space-y-4">
          {/* Events Header and Filters */}
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold text-gray-900">Security Events</h2>
            <div className="flex items-center space-x-3">
              <button
                onClick={handleExportEvents}
                className="px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center"
              >
                <Download className="h-4 w-4 mr-2" />
                Export
              </button>
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="px-3 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 flex items-center"
              >
                <Filter className="h-4 w-4 mr-2" />
                Filters
              </button>
            </div>
          </div>

          {/* Search and Filters */}
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="flex items-center space-x-4 mb-4">
              <div className="flex-1 relative">
                <Search className="h-5 w-5 absolute left-3 top-3 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search events..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              <select
                value={selectedConfig}
                onChange={(e) => {
                  setSelectedConfig(e.target.value);
                  setEventFilters(prev => ({ 
                    ...prev, 
                    siem_config_id: e.target.value || undefined,
                    page: 1 
                  }));
                }}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All SIEMs</option>
                {configs.map((config) => (
                  <option key={config.id} value={config.id}>
                    {config.display_name || config.name}
                  </option>
                ))}
              </select>
            </div>

            {showFilters && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Severity</label>
                  <select
                    multiple
                    value={eventFilters.severity || []}
                    onChange={(e) => {
                      const values = Array.from(e.target.selectedOptions, option => option.value as SIEMEventSeverity);
                      setEventFilters(prev => ({ ...prev, severity: values.length ? values : undefined, page: 1 }));
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    {Object.values(SIEMEventSeverity).map((severity) => (
                      <option key={severity} value={severity}>
                        {severity.toUpperCase()}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                  <select
                    multiple
                    value={eventFilters.category || []}
                    onChange={(e) => {
                      const values = Array.from(e.target.selectedOptions, option => option.value as SIEMEventCategory);
                      setEventFilters(prev => ({ ...prev, category: values.length ? values : undefined, page: 1 }));
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    {Object.values(SIEMEventCategory).map((category) => (
                      <option key={category} value={category}>
                        {category.replace('_', ' ').toUpperCase()}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Date Range</label>
                  <div className="space-y-2">
                    <input
                      type="datetime-local"
                      value={eventFilters.start_time ? new Date(eventFilters.start_time).toISOString().slice(0, 16) : ''}
                      onChange={(e) => setEventFilters(prev => ({ 
                        ...prev, 
                        start_time: e.target.value ? new Date(e.target.value).toISOString() : undefined,
                        page: 1 
                      }))}
                      className="w-full px-3 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                    <input
                      type="datetime-local"
                      value={eventFilters.end_time ? new Date(eventFilters.end_time).toISOString().slice(0, 16) : ''}
                      onChange={(e) => setEventFilters(prev => ({ 
                        ...prev, 
                        end_time: e.target.value ? new Date(e.target.value).toISOString() : undefined,
                        page: 1 
                      }))}
                      className="w-full px-3 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Events List */}
          {eventsLoading ? (
            <div className="flex items-center justify-center h-32">
              <RefreshCw className="h-6 w-6 animate-spin text-blue-500" />
              <span className="ml-2 text-gray-600">Loading events...</span>
            </div>
          ) : events.length === 0 ? (
            <div className="text-center py-12">
              <Activity className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No events found</h3>
              <p className="text-gray-600">No security events match your current filters.</p>
            </div>
          ) : (
            <>
              <div className="bg-white rounded-lg shadow overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Timestamp
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Severity
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Category
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Type
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Description
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Source
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {events.map((event) => (
                        <tr key={event.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {formatTimestamp(event.timestamp)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 py-1 text-xs font-medium rounded-full ${getSeverityColor(event.severity)}`}>
                              {event.severity.toUpperCase()}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {event.category.replace('_', ' ').toUpperCase()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {event.event_type}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate">
                            {event.description}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {event.source_ip || 'N/A'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            <button
                              onClick={() => {
                                // TODO: Implement event details modal
                                console.log('View event details:', event);
                              }}
                              className="text-blue-600 hover:text-blue-900"
                            >
                              <Eye className="h-4 w-4" />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between bg-white px-4 py-3 rounded-lg shadow">
                  <div className="flex items-center">
                    <p className="text-sm text-gray-700">
                      Showing page {currentPage} of {totalPages} ({totalEvents} total events)
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handlePageChange(currentPage - 1)}
                      disabled={currentPage === 1}
                      className="px-3 py-1 bg-white border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Previous
                    </button>
                    <span className="text-sm text-gray-700">
                      Page {currentPage} of {totalPages}
                    </span>
                    <button
                      onClick={() => handlePageChange(currentPage + 1)}
                      disabled={currentPage === totalPages}
                      className="px-3 py-1 bg-white border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {activeTab === 'stats' && statistics && (
        <div className="space-y-6">
          <h2 className="text-lg font-semibold text-gray-900">Statistics & Analytics</h2>
          
          {statsLoading ? (
            <div className="flex items-center justify-center h-32">
              <RefreshCw className="h-6 w-6 animate-spin text-blue-500" />
              <span className="ml-2 text-gray-600">Loading statistics...</span>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Events by Severity */}
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Events by Severity</h3>
                <div className="space-y-3">
                  {Object.entries(statistics.events_by_severity).map(([severity, count]) => (
                    <div key={severity} className="flex items-center justify-between">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getSeverityColor(severity as SIEMEventSeverity)}`}>
                        {severity.toUpperCase()}
                      </span>
                      <span className="text-lg font-semibold text-gray-900">{count.toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Events by Category */}
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Events by Category</h3>
                <div className="space-y-3">
                  {Object.entries(statistics.events_by_category).map(([category, count]) => (
                    <div key={category} className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">
                        {category.replace('_', ' ').toUpperCase()}
                      </span>
                      <span className="text-lg font-semibold text-gray-900">{count.toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Events by SIEM */}
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Events by SIEM</h3>
                <div className="space-y-3">
                  {Object.entries(statistics.events_by_siem).map(([siemId, count]) => {
                    const config = configs.find(c => c.id === siemId);
                    return (
                      <div key={siemId} className="flex items-center justify-between">
                        <span className="text-sm font-medium text-gray-700">
                          {config?.display_name || config?.name || siemId}
                        </span>
                        <span className="text-lg font-semibold text-gray-900">{count.toLocaleString()}</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Query Performance */}
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Query Performance</h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">Total Queries</span>
                    <span className="text-lg font-semibold text-gray-900">{statistics.total_queries.toLocaleString()}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">Queries (24h)</span>
                    <span className="text-lg font-semibold text-gray-900">{statistics.queries_last_24h.toLocaleString()}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">Avg Response Time</span>
                    <span className="text-lg font-semibold text-gray-900">{statistics.avg_query_time_ms.toFixed(1)}ms</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Create Configuration Modal */}
      {showCreateModal && (
        <ConfigurationModal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          onSubmit={handleCreateConfig}
          title="Create SIEM Configuration"
        />
      )}

      {/* Edit Configuration Modal */}
      {showEditModal && editingConfig && (
        <ConfigurationModal
          isOpen={showEditModal}
          onClose={() => {
            setShowEditModal(false);
            setEditingConfig(null);
          }}
          onSubmit={(data) => handleUpdateConfig(editingConfig.id!, data)}
          initialData={editingConfig}
          title="Edit SIEM Configuration"
        />
      )}
    </div>
  );
};

// Configuration Modal Component
interface ConfigurationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: SIEMConfigCreateRequest) => void;
  initialData?: SIEMConfig;
  title: string;
}

const ConfigurationModal: React.FC<ConfigurationModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  initialData,
  title
}) => {
  const [formData, setFormData] = useState<SIEMConfigCreateRequest>({
    name: '',
    display_name: '',
    description: '',
    siem_type: SIEMType.GENERIC,
    endpoint_url: '',
    auth_type: SIEMAuthType.API_KEY,
    auth_config: {},
    connection_settings: {},
    is_active: true,
    is_primary: false,
    tags: {}
  });

  useEffect(() => {
    if (initialData) {
      setFormData({
        name: initialData.name,
        display_name: initialData.display_name || '',
        description: initialData.description || '',
        siem_type: initialData.siem_type,
        endpoint_url: initialData.endpoint_url,
        auth_type: initialData.auth_type,
        auth_config: initialData.auth_config,
        connection_settings: initialData.connection_settings,
        is_active: initialData.is_active,
        is_primary: initialData.is_primary,
        tags: initialData.tags || {}
      });
    }
  }, [initialData]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">{title}</h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Display Name</label>
              <input
                type="text"
                value={formData.display_name}
                onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              rows={3}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">SIEM Type *</label>
              <select
                value={formData.siem_type}
                onChange={(e) => setFormData({ ...formData, siem_type: e.target.value as SIEMType })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              >
                {Object.values(SIEMType).map((type) => (
                  <option key={type} value={type}>
                    {type.replace('_', ' ').toUpperCase()}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Authentication Type *</label>
              <select
                value={formData.auth_type}
                onChange={(e) => setFormData({ ...formData, auth_type: e.target.value as SIEMAuthType })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              >
                {Object.values(SIEMAuthType).map((type) => (
                  <option key={type} value={type}>
                    {type.replace('_', ' ').toUpperCase()}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Endpoint URL *</label>
            <input
              type="url"
              value={formData.endpoint_url}
              onChange={(e) => setFormData({ ...formData, endpoint_url: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Authentication Configuration (JSON)</label>
            <textarea
              value={JSON.stringify(formData.auth_config, null, 2)}
              onChange={(e) => {
                try {
                  const parsed = JSON.parse(e.target.value);
                  setFormData({ ...formData, auth_config: parsed });
                } catch {
                  // Invalid JSON, don't update
                }
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
              rows={4}
            />
          </div>

          <div className="flex items-center space-x-6">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                className="rounded"
              />
              <span className="ml-2 text-sm text-gray-700">Active</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.is_primary}
                onChange={(e) => setFormData({ ...formData, is_primary: e.target.checked })}
                className="rounded"
              />
              <span className="ml-2 text-sm text-gray-700">Primary</span>
            </label>
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              {initialData ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default SIEMIntegrationPage;
