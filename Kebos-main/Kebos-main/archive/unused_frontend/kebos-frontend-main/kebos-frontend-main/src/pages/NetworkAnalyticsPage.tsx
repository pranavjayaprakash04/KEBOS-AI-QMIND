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
      
      // In a real implementation, this would call the backend API
      // const nodesResponse = await apiClient.get('/api/network-analytics/nodes');
      // const flowsResponse = await apiClient.get('/api/network-analytics/flows');
      
      // Mock data for now
      setTimeout(() => {
        setNodes([
          {
            id: '1',
            ip: '192.168.1.1',
            hostname: 'firewall-01',
            type: 'firewall',
            status: 'online',
            connections: ['2', '3', '4'],
            threatLevel: 'low'
          },
          {
            id: '2',
            ip: '192.168.1.10',
            hostname: 'server-web-01',
            type: 'server',
            status: 'online',
            connections: ['1', '5'],
            threatLevel: 'medium'
          },
          {
            id: '3',
            ip: '192.168.1.20',
            hostname: 'server-db-01',
            type: 'server',
            status: 'warning',
            connections: ['1', '2'],
            threatLevel: 'high'
          },
          {
            id: '4',
            ip: '192.168.1.100',
            hostname: 'workstation-01',
            type: 'workstation',
            status: 'online',
            connections: ['1'],
            threatLevel: 'low'
          },
          {
            id: '5',
            ip: '192.168.1.50',
            hostname: 'switch-core-01',
            type: 'switch',
            status: 'online',
            connections: ['2', '6'],
            threatLevel: 'low'
          }
        ]);

        setFlows([
          {
            id: '1',
            sourceIp: '192.168.1.100',
            destinationIp: '203.0.113.45',
            protocol: 'HTTPS',
            port: 443,
            bytes: 2048576,
            packets: 1543,
            timestamp: '2024-01-15T10:30:00Z',
            suspicious: true
          },
          {
            id: '2',
            sourceIp: '192.168.1.10',
            destinationIp: '192.168.1.20',
            protocol: 'MySQL',
            port: 3306,
            bytes: 512000,
            packets: 256,
            timestamp: '2024-01-15T10:25:00Z',
            suspicious: false
          },
          {
            id: '3',
            sourceIp: '10.0.0.15',
            destinationIp: '192.168.1.10',
            protocol: 'HTTP',
            port: 80,
            bytes: 1024000,
            packets: 798,
            timestamp: '2024-01-15T10:20:00Z',
            suspicious: false
          },
          {
            id: '4',
            sourceIp: '192.168.1.100',
            destinationIp: '192.168.1.1',
            protocol: 'SSH',
            port: 22,
            bytes: 8192,
            packets: 12,
            timestamp: '2024-01-15T10:15:00Z',
            suspicious: true
          }
        ]);
        
        setStats({
          totalNodes: 5,
          activeConnections: 12,
          suspiciousActivities: 3,
          blockedAttempts: 7,
          bandwidth: { inbound: 145.7, outbound: 89.2 }
        });
        
        setIsLoading(false);
      }, 1000);
    };

    fetchData();
  }, []);

  const getNodeStatusColor = (status: NetworkNode['status']) => {
    switch (status) {
      case 'online':
        return 'bg-success';
      case 'offline':
        return 'bg-gray-500';
      case 'warning':
        return 'bg-warning';
      default:
        return 'bg-gray-500';
    }
  };

  const getThreatLevelColor = (level: NetworkNode['threatLevel']) => {
    switch (level) {
      case 'low':
        return 'text-success';
      case 'medium':
        return 'text-warning';
      case 'high':
        return 'text-error';
      default:
        return 'text-text-secondary';
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
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm border-b border-slate-200/50 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg shadow-lg">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">
                Network Analytics
              </h1>
              <p className="text-slate-600">Real-time network topology and traffic analysis</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Statistics Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-6">
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-6 hover:shadow-2xl transition-all duration-200">
            <div className="text-center">
              <p className="text-3xl font-bold text-indigo-600">{stats.totalNodes}</p>
              <p className="text-slate-600 text-sm font-medium">Total Nodes</p>
            </div>
          </div>
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-6 hover:shadow-2xl transition-all duration-200">
            <div className="text-center">
              <p className="text-3xl font-bold text-green-600">{stats.activeConnections}</p>
              <p className="text-slate-600 text-sm font-medium">Active Connections</p>
            </div>
          </div>
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-6 hover:shadow-2xl transition-all duration-200">
            <div className="text-center">
              <p className="text-3xl font-bold text-yellow-600">{stats.suspiciousActivities}</p>
              <p className="text-slate-600 text-sm font-medium">Suspicious Activities</p>
            </div>
          </div>
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-6 hover:shadow-2xl transition-all duration-200">
            <div className="text-center">
              <p className="text-3xl font-bold text-red-600">{stats.blockedAttempts}</p>
              <p className="text-slate-600 text-sm font-medium">Blocked Attempts</p>
            </div>
          </div>
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-6 hover:shadow-2xl transition-all duration-200">
            <div className="text-center">
              <p className="text-lg font-bold text-indigo-600">{stats.bandwidth.inbound} MB/s</p>
              <p className="text-lg font-bold text-purple-600">{stats.bandwidth.outbound} MB/s</p>
              <p className="text-slate-600 text-sm font-medium">In / Out</p>
            </div>
          </div>
        </div>

        {/* View Mode Tabs */}
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50">
          <div className="flex">
            <button
              onClick={() => setViewMode('topology')}
              className={`px-6 py-3 font-medium rounded-tl-2xl ${
                viewMode === 'topology'
                  ? 'bg-indigo-600 text-white'
                  : 'text-slate-600 hover:text-indigo-600'
              }`}
            >
              Network Topology
            </button>
            <button
              onClick={() => setViewMode('flows')}
              className={`px-6 py-3 font-medium ${
                viewMode === 'flows'
                  ? 'bg-indigo-600 text-white'
                  : 'text-slate-600 hover:text-indigo-600'
              }`}
            >
              Traffic Flows
            </button>
            <button
              onClick={() => setViewMode('analytics')}
              className={`px-6 py-3 font-medium rounded-tr-2xl ${
                viewMode === 'analytics'
                  ? 'bg-indigo-600 text-white'
                  : 'text-slate-600 hover:text-indigo-600'
              }`}
            >
              Analytics Dashboard
            </button>
          </div>
        </div>

        {/* Conditional Views */}
        {viewMode === 'topology' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Network Map */}
            <div className="lg:col-span-2 bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50">
              <div className="px-6 py-4 border-b border-slate-200">
                <h3 className="text-lg font-semibold text-slate-800">Network Topology Map</h3>
              </div>
              <div className="p-6">
                <div className="bg-slate-100 rounded-xl h-96 flex items-center justify-center">
                  <p className="text-slate-500">Interactive network topology visualization</p>
                </div>
              </div>
            </div>

            {/* Node Details */}
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50">
              <div className="px-6 py-4 border-b border-slate-200">
                <h3 className="text-lg font-semibold text-slate-800">Network Nodes</h3>
              </div>
              <div className="p-6 space-y-4">
                {nodes.map((node) => (
                  <div key={node.id} className="p-4 bg-slate-50 rounded-xl shadow-sm border border-slate-200">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-3">
                        <div className="text-indigo-600">{getNodeIcon(node.type)}</div>
                        <div>
                          <h4 className="text-sm font-medium text-slate-800">{node.hostname}</h4>
                          <p className="text-xs text-slate-500">{node.ip}</p>
                        </div>
                      </div>
                      <div className={`w-3 h-3 rounded-full ${getNodeStatusColor(node.status)}`}></div>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-500">{node.type}</span>
                      <span className={`font-medium ${getThreatLevelColor(node.threatLevel)}`}>
                        {node.threatLevel} risk
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {viewMode === 'flows' && (
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50">
            <div className="px-6 py-4 border-b border-slate-200">
              <h3 className="text-lg font-semibold text-slate-800">Network Traffic Flows</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">
                      Source
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">
                      Destination
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">
                      Protocol
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">
                      Data Transfer
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">
                      Timestamp
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {flows.map((flow) => (
                    <tr key={flow.id} className="hover:bg-slate-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-800 font-mono">
                        {flow.sourceIp}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-800 font-mono">
                        {flow.destinationIp}:{flow.port}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-700">
                          {flow.protocol}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-800">
                        <div>
                          <div>{formatBytes(flow.bytes)}</div>
                          <div className="text-xs text-slate-500">{flow.packets} packets</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                        {new Date(flow.timestamp).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {flow.suspicious ? (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700">
                            Suspicious
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
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

        {viewMode === 'analytics' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Analytics Cards */}
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50">
              <div className="px-6 py-4 border-b border-slate-200">
                <h3 className="text-lg font-semibold text-slate-800">Bandwidth Usage</h3>
              </div>
              <div className="p-6">
                <div className="bg-slate-100 rounded-xl h-64 flex items-center justify-center">
                  <p className="text-slate-500">Bandwidth chart</p>
                </div>
              </div>
            </div>
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50">
              <div className="px-6 py-4 border-b border-slate-200">
                <h3 className="text-lg font-semibold text-slate-800">Protocol Distribution</h3>
              </div>
              <div className="p-6">
                <div className="bg-slate-100 rounded-xl h-64 flex items-center justify-center">
                  <p className="text-slate-500">Protocol pie chart</p>
                </div>
              </div>
            </div>
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50">
              <div className="px-6 py-4 border-b border-slate-200">
                <h3 className="text-lg font-semibold text-slate-800">Threat Heat Map</h3>
              </div>
              <div className="p-6">
                <div className="bg-slate-100 rounded-xl h-64 flex items-center justify-center">
                  <p className="text-slate-500">Threat intensity map</p>
                </div>
              </div>
            </div>
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50">
              <div className="px-6 py-4 border-b border-slate-200">
                <h3 className="text-lg font-semibold text-slate-800">Connection Timeline</h3>
              </div>
              <div className="p-6">
                <div className="bg-slate-100 rounded-xl h-64 flex items-center justify-center">
                  <p className="text-slate-500">Timeline visualization</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
         