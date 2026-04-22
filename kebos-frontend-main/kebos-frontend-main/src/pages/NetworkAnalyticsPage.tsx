import { useState, useEffect } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { networkAnalyticsService } from '../services/networkAnalyticsService';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface NetworkNode {
  id: string;
  ip: string;
  hostname: string;
  type: 'server' | 'workstation' | 'router' | 'switch' | 'firewall';
  status: 'online' | 'offline' | 'warning';
  connections: string[];
  threatLevel: 'low' | 'medium' | 'high';
}

interface NetworkFlow {
  id: string;
  sourceIp: string;
  destinationIp: string;
  protocol: string;
  port: number;
  bytes: number;
  packets: number;
  timestamp: string;
  suspicious: boolean;
}

interface NetworkStats {
  totalNodes: number;
  activeConnections: number;
  suspiciousActivities: number;
  blockedAttempts: number;
  bandwidth: {
    inbound: number;
    outbound: number;
  };
}

export function NetworkAnalyticsPage() {
  const [viewMode, setViewMode] = useState<'topology' | 'flows' | 'analytics'>('topology');
  const [nodes, setNodes] = useState<NetworkNode[]>([]);
  const [flows, setFlows] = useState<NetworkFlow[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [stats, setStats] = useState<NetworkStats>({
    totalNodes: 0,
    activeConnections: 0,
    suspiciousActivities: 0,
    blockedAttempts: 0,
    bandwidth: { inbound: 0, outbound: 0 }
  });

  // Fetch network data on component mount
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      
      try {
        // Fetch real data from network analytics service
        const [topologyData, flowsData, statsData] = await Promise.all([
          networkAnalyticsService.getNetworkTopology(),
          networkAnalyticsService.getNetworkFlows({ limit: 50 }),
          networkAnalyticsService.getNetworkStats()
        ]);

        // Map topology data to NetworkNode format
        const mappedNodes: NetworkNode[] = topologyData.map(node => ({
          id: node.id,
          ip: node.metadata.ip_address || 'Unknown',
          hostname: node.name,
          type: (node.node_type as any) || 'server',
          status: node.metadata.status || 'online',
          connections: node.connections,
          threatLevel: node.metadata.threat_level || 'low'
        }));

        // Map flows data to NetworkFlow format
        const mappedFlows: NetworkFlow[] = flowsData.map(flow => ({
          id: flow.id,
          sourceIp: flow.source_ip,
          destinationIp: flow.destination_ip,
          protocol: flow.protocol,
          port: flow.destination_port,
          bytes: flow.bytes,
          packets: flow.packets,
          timestamp: flow.timestamp,
          suspicious: false // You might want to add this logic based on your threat detection
        }));

        // Map stats data to NetworkStats format
        const mappedStats: NetworkStats = {
          totalNodes: mappedNodes.length,
          activeConnections: statsData.total_flows,
          suspiciousActivities: 0, // You might want to fetch this from threat detection
          blockedAttempts: 0, // You might want to fetch this from SIEM
          bandwidth: {
            inbound: statsData.total_bytes / 1024 / 1024, // Convert to MB
            outbound: statsData.total_bytes / 1024 / 1024 / 2 // Rough estimate
          }
        };

        setNodes(mappedNodes);
        setFlows(mappedFlows);
        setStats(mappedStats);
      } catch (error) {
        console.error('Failed to fetch network analytics data:', error);
        
        // Fallback to empty data on error
        setNodes([]);
        setFlows([]);
        setStats({
          totalNodes: 0,
          activeConnections: 0,
          suspiciousActivities: 0,
          blockedAttempts: 0,
          bandwidth: { inbound: 0, outbound: 0 }
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  const getNodeStatusColor = (status: NetworkNode['status']) => {
    switch (status) {
      case 'online':
        return 'bg-green-600';
      case 'offline':
        return 'bg-gray-500';
      case 'warning':
        return 'bg-yellow-600';
      default:
        return 'bg-gray-500';
    }
  };

  const getThreatLevelColor = (level: NetworkNode['threatLevel']) => {
    switch (level) {
      case 'low':
        return 'text-green-600';
      case 'medium':
        return 'text-yellow-600';
      case 'high':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getNodeIcon = (type: NetworkNode['type']) => {
    switch (type) {
      case 'server':
        return (
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M7 16h.01" />
          </svg>
        );
      case 'workstation':
        return (
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        );
      case 'firewall':
        return (
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        );
      case 'router':
      case 'switch':
        return (
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" />
          </svg>
        );
      default:
        return (
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
          </svg>
        );
    }
  };

  const formatBytes = (bytes: number) => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
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

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-black mb-2">Network Analytics</h1>
          <p className="text-black">Real-time network topology and traffic analysis</p>
        </div>
        <div className="flex space-x-2">
          <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium hover:shadow-md transition-shadow duration-200">
            Export Report
          </button>
          <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium hover:shadow-md transition-shadow duration-200">
            Scan Network
          </button>
        </div>
      </div>

      {/* Network Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8 place-items-center">
        <div className="bg-white rounded-lg p-6 border border-gray-200 shadow-md hover:shadow-lg transition-shadow duration-300">
          <div className="text-center">
            <p className="text-2xl font-bold text-blue-600">{stats.totalNodes}</p>
            <p className="text-black text-sm">Total Nodes</p>
          </div>
        </div>
        <div className="bg-white rounded-lg p-6 border border-gray-200 shadow-md hover:shadow-lg transition-shadow duration-300">
          <div className="text-center">
            <p className="text-2xl font-bold text-green-600">{stats.activeConnections}</p>
            <p className="text-black text-sm">Active Connections</p>
          </div>
        </div>
        <div className="bg-white rounded-lg p-6 border border-gray-200 shadow-md hover:shadow-lg transition-shadow duration-300">
          <div className="text-center">
            <p className="text-2xl font-bold text-yellow-600">{stats.suspiciousActivities}</p>
            <p className="text-black text-sm">Suspicious Activities</p>
          </div>
        </div>
        <div className="bg-white rounded-lg p-6 border border-gray-200 shadow-md hover:shadow-lg transition-shadow duration-300">
          <div className="text-center">
            <p className="text-2xl font-bold text-red-600">{stats.blockedAttempts}</p>
            <p className="text-black text-sm">Blocked Attempts</p>
          </div>
        </div>
        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <div className="text-center">
            <p className="text-lg font-bold text-blue-600">{stats.bandwidth.inbound} MB/s</p>
            <p className="text-lg font-bold text-gray-600">{stats.bandwidth.outbound} MB/s</p>
            <p className="text-gray-600 text-sm">In / Out</p>
          </div>
        </div>
      </div>

      {/* View Mode Tabs */}
      <div className="bg-white rounded-lg border border-gray-200 mb-6">
        <div className="flex">
          <button
            onClick={() => setViewMode('topology')}
            className={`px-6 py-3 font-medium rounded-tl-lg ${
              viewMode === 'topology'
                ? 'bg-blue-600 text-white'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Network Topology
          </button>
          <button
            onClick={() => setViewMode('flows')}
            className={`px-6 py-3 font-medium ${
              viewMode === 'flows'
                ? 'bg-blue-600 text-white'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Traffic Flows
          </button>
          <button
            onClick={() => setViewMode('analytics')}
            className={`px-6 py-3 font-medium rounded-tr-lg ${
              viewMode === 'analytics'
                ? 'bg-blue-600 text-white'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Analytics Dashboard
          </button>
        </div>
      </div>

      {/* Network Topology View */}
      {viewMode === 'topology' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 place-items-center">
          {/* Network Map */}
          <div className="lg:col-span-2 bg-white rounded-lg border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Network Topology Map</h3>
            </div>
            <div className="p-6">
              <div className="bg-gray-50 rounded-lg h-96 flex items-center justify-center">
                <div className="text-center">
                  <svg className="w-16 h-16 text-gray-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                  <p className="text-gray-600">Interactive network topology visualization</p>
                  <p className="text-sm text-gray-600 mt-2">Real-time network graph will appear here</p>
                </div>
              </div>
            </div>
          </div>

          {/* Node Details */}
          <div className="bg-white rounded-lg border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Network Nodes</h3>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                {nodes.map((node) => (
                  <div key={node.id} className="p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-3">
                        <div className="text-blue-600">
                          {getNodeIcon(node.type)}
                        </div>
                        <div>
                          <h4 className="text-sm font-medium text-gray-900">{node.hostname}</h4>
                          <p className="text-xs text-gray-600">{node.ip}</p>
                        </div>
                      </div>
                      <div className={`w-3 h-3 rounded-full ${getNodeStatusColor(node.status)}`}></div>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-600">{node.type}</span>
                      <span className={`font-medium ${getThreatLevelColor(node.threatLevel)}`}>
                        {node.threatLevel} risk
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Traffic Flows View */}
      {viewMode === 'flows' && (
        <div className="bg-background-secondary rounded-lg border border-border">
          <div className="px-6 py-4 border-b border-border">
            <h3 className="text-lg font-semibold text-text-primary">Network Traffic Flows</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-background-primary">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                    Source
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                    Destination
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                    Protocol
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                    Data Transfer
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                    Timestamp
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {flows.map((flow) => (
                  <tr key={flow.id} className="hover:bg-background-primary">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-text-primary font-mono">
                      {flow.sourceIp}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-text-primary font-mono">
                      {flow.destinationIp}:{flow.port}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary bg-opacity-10 text-primary">
                        {flow.protocol}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-text-primary">
                      <div>
                        <div>{formatBytes(flow.bytes)}</div>
                        <div className="text-xs text-text-secondary">{flow.packets} packets</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-text-secondary">
                      {new Date(flow.timestamp).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {flow.suspicious ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-error text-white">
                          Suspicious
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-success text-white">
                          Normal
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Analytics Dashboard View */}
      {viewMode === 'analytics' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 place-items-center">
          <div className="bg-background-secondary rounded-lg border border-border">
            <div className="px-6 py-4 border-b border-border">
              <h3 className="text-lg font-semibold text-text-primary">Bandwidth Usage</h3>
            </div>
            <div className="p-6">
              <div className="bg-background-primary rounded-lg h-64 flex items-center justify-center">
                <div className="text-center">
                  <svg className="w-12 h-12 text-text-secondary mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  <p className="text-text-secondary text-sm">Bandwidth chart</p>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-background-secondary rounded-lg border border-border">
            <div className="px-6 py-4 border-b border-border">
              <h3 className="text-lg font-semibold text-text-primary">Protocol Distribution</h3>
            </div>
            <div className="p-6">
              <div className="bg-background-primary rounded-lg h-64 flex items-center justify-center">
                <div className="text-center">
                  <svg className="w-12 h-12 text-text-secondary mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z" />
                  </svg>
                  <p className="text-text-secondary text-sm">Protocol pie chart</p>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-background-secondary rounded-lg border border-border">
            <div className="px-6 py-4 border-b border-border">
              <h3 className="text-lg font-semibold text-text-primary">Threat Heat Map</h3>
            </div>
            <div className="p-6">
              <div className="bg-background-primary rounded-lg h-64 flex items-center justify-center">
                <div className="text-center">
                  <svg className="w-12 h-12 text-text-secondary mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.879 16.121A3 3 0 1012.015 11L11 14H9c0 .768.293 1.536.879 2.121z" />
                  </svg>
                  <p className="text-text-secondary text-sm">Threat intensity map</p>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-background-secondary rounded-lg border border-border">
            <div className="px-6 py-4 border-b border-border">
              <h3 className="text-lg font-semibold text-text-primary">Connection Timeline</h3>
            </div>
            <div className="p-6">
              <div className="bg-background-primary rounded-lg h-64 flex items-center justify-center">
                <div className="text-center">
                  <svg className="w-12 h-12 text-text-secondary mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="text-text-secondary text-sm">Timeline visualization</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
