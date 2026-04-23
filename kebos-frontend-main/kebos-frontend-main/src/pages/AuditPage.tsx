import { useState, useEffect } from 'react';

interface AuditLog {
  id: string;
  timestamp: string;
  user: string;
  action: string;
  resource: string;
  result: 'success' | 'failure' | 'warning';
  ipAddress: string;
  userAgent: string;
  details: string;
}

interface AuditStats {
  totalActions: number;
  successRate: number;
  criticalActions: number;
  failedLogins: number;
  dataAccess: number;
  configChanges: number;
}

export function AuditPage() {
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [stats, _setStats] = useState<AuditStats>({
    totalActions: 15847,
    successRate: 94.2,
    criticalActions: 23,
    failedLogins: 45,
    dataAccess: 892,
    configChanges: 12
  });
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');

  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setAuditLogs([
        {
          id: '1',
          timestamp: '2024-01-15T10:30:00Z',
          user: 'admin@company.com',
          action: 'LOGIN_SUCCESS',
          resource: 'Authentication System',
          result: 'success',
          ipAddress: '192.168.1.100',
          userAgent: 'Mozilla/5.0 Chrome/120.0',
          details: 'Successful administrator login from corporate network'
        },
        {
          id: '2',
          timestamp: '2024-01-15T10:25:00Z',
          user: 'analyst@company.com',
          action: 'DATA_ACCESS',
          resource: 'Threat Intelligence Database',
          result: 'success',
          ipAddress: '192.168.1.105',
          userAgent: 'Mozilla/5.0 Chrome/120.0',
          details: 'Accessed threat intelligence data for analysis'
        },
        {
          id: '3',
          timestamp: '2024-01-15T10:20:00Z',
          user: 'unknown',
          action: 'LOGIN_FAILED',
          resource: 'Authentication System',
          result: 'failure',
          ipAddress: '203.0.113.45',
          userAgent: 'curl/7.68.0',
          details: 'Failed login attempt with invalid credentials'
        },
        {
          id: '4',
          timestamp: '2024-01-15T10:15:00Z',
          user: 'sysadmin@company.com',
          action: 'CONFIG_CHANGE',
          resource: 'Firewall Rules',
          result: 'success',
          ipAddress: '192.168.1.50',
          userAgent: 'Mozilla/5.0 Firefox/120.0',
          details: 'Updated firewall rules to block suspicious IP range'
        },
        {
          id: '5',
          timestamp: '2024-01-15T10:10:00Z',
          user: 'operator@company.com',
          action: 'THREAT_INVESTIGATION',
          resource: 'Security Dashboard',
          result: 'warning',
          ipAddress: '192.168.1.110',
          userAgent: 'Mozilla/5.0 Chrome/120.0',
          details: 'Investigated security alert - potential false positive'
        }
      ]);
      setIsLoading(false);
    }, 1000);
  }, []);

  const getResultColor = (result: AuditLog['result']) => {
    switch (result) {
      case 'success':
        return 'bg-success text-white';
      case 'failure':
        return 'bg-error text-white';
      case 'warning':
        return 'bg-warning text-text-primary';
      default:
        return 'bg-gray-500 text-white';
    }
  };

  const getActionIcon = (action: string) => {
    if (action.includes('LOGIN')) {
      return (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
        </svg>
      );
    }
    if (action.includes('DATA')) {
      return (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
        </svg>
      );
    }
    if (action.includes('CONFIG')) {
      return (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      );
    }
    return (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    );
  };

  const filteredLogs = auditLogs.filter(log => {
    const matchesSearch = log.user.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         log.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         log.resource.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterType === 'all' || log.result === filterType;
    return matchesSearch && matchesFilter;
  });

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
          <h1 className="text-3xl font-bold text-black mb-2">Audit & Monitoring</h1>
          <p className="text-black">Security audit trails and threat monitoring</p>
        </div>
        <div className="flex space-x-2">
          <button className="bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg font-medium">
            Export Logs
          </button>
          <button className="bg-secondary hover:bg-secondary-dark text-text-primary px-4 py-2 rounded-lg font-medium border border-border hover:shadow-md transition-shadow duration-200">
            Generate Report
          </button>
        </div>
      </div>

      {/* Audit Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-6 mb-8">
        <div className="bg-background-secondary rounded-lg p-6 border border-border">
          <div className="text-center">
            <p className="text-2xl font-bold text-primary">{stats.totalActions.toLocaleString()}</p>
            <p className="text-black text-sm">Total Actions</p>
          </div>
        </div>
        <div className="bg-background-secondary rounded-lg p-6 border border-border">
          <div className="text-center">
            <p className="text-2xl font-bold text-success">{stats.successRate}%</p>
            <p className="text-black text-sm">Success Rate</p>
          </div>
        </div>
        <div className="bg-background-secondary rounded-lg p-6 border border-border">
          <div className="text-center">
            <p className="text-2xl font-bold text-error">{stats.criticalActions}</p>
            <p className="text-black text-sm">Critical Actions</p>
          </div>
        </div>
        <div className="bg-background-secondary rounded-lg p-6 border border-border">
          <div className="text-center">
            <p className="text-2xl font-bold text-warning">{stats.failedLogins}</p>
            <p className="text-black text-sm">Failed Logins</p>
          </div>
        </div>
        <div className="bg-background-secondary rounded-lg p-6 border border-border">
          <div className="text-center">
            <p className="text-2xl font-bold text-primary">{stats.dataAccess}</p>
            <p className="text-black text-sm">Data Access</p>
          </div>
        </div>
        <div className="bg-background-secondary rounded-lg p-6 border border-border">
          <div className="text-center">
            <p className="text-2xl font-bold text-warning">{stats.configChanges}</p>
            <p className="text-black text-sm">Config Changes</p>
          </div>
        </div>
      </div>

      {/* Search and Filter */}
      <div className="bg-background-secondary rounded-lg p-6 border border-border mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0 md:space-x-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search logs by user, action, or resource..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-lg bg-background-primary text-text-primary placeholder-text-secondary focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>
          <div className="flex space-x-2">
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-3 py-2 border border-border rounded-lg bg-background-primary text-text-primary focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
            >
              <option value="all">All Results</option>
              <option value="success">Success</option>
              <option value="failure">Failure</option>
              <option value="warning">Warning</option>
            </select>
          </div>
        </div>
      </div>

      {/* Audit Logs Table */}
      <div className="bg-background-secondary rounded-lg border border-border overflow-hidden">
        <div className="px-6 py-4 border-b border-border">
          <h3 className="text-lg font-semibold text-text-primary">
            Audit Logs ({filteredLogs.length} entries)
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-background-primary">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                  Timestamp
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                  Action
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                  Resource
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                  Result
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                  IP Address
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-text-secondary uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filteredLogs.map((log) => (
                <tr key={log.id} className="hover:bg-background-primary">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-text-primary">
                    {new Date(log.timestamp).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center space-x-2">
                      <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
                        <span className="text-xs text-white font-medium">
                          {log.user.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <span className="text-sm text-text-primary">{log.user}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center space-x-2">
                      {getActionIcon(log.action)}
                      <span className="text-sm text-text-primary">{log.action}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-text-primary">
                    {log.resource}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getResultColor(log.result)}`}>
                      {log.result}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-text-secondary">
                    {log.ipAddress}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button className="text-primary hover:text-primary-dark mr-3">
                      View Details
                    </button>
                    <button className="text-warning hover:text-warning-dark">
                      Investigate
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
