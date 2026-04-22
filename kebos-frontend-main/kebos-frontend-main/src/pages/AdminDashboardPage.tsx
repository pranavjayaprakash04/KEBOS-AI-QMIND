import { useState, useEffect } from 'react';

interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'analyst' | 'operator' | 'viewer';
  status: 'active' | 'inactive' | 'suspended';
  lastLogin: string;
  createdAt: string;
}

interface SystemHealth {
  cpu: number;
  memory: number;
  disk: number;
  network: number;
  services: {
    name: string;
    status: 'healthy' | 'warning' | 'error';
    uptime: string;
  }[];
}

interface SecurityConfig {
  mfaEnabled: boolean;
  sessionTimeout: number;
  passwordPolicy: {
    minLength: number;
    requireSpecialChars: boolean;
    requireNumbers: boolean;
    requireUppercase: boolean;
  };
  ipWhitelist: string[];
  auditRetention: number;
}

export function AdminDashboardPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [systemHealth] = useState<SystemHealth>({
    cpu: 45,
    memory: 62,
    disk: 78,
    network: 23,
    services: [
      { name: 'API Gateway', status: 'healthy', uptime: '99.9%' },
      { name: 'Database', status: 'healthy', uptime: '99.8%' },
      { name: 'Threat Engine', status: 'warning', uptime: '98.5%' },
      { name: 'ML Pipeline', status: 'healthy', uptime: '99.7%' },
      { name: 'Kafka', status: 'error', uptime: '95.2%' }
    ]
  });
  const [securityConfig, setSecurityConfig] = useState<SecurityConfig>({
    mfaEnabled: true,
    sessionTimeout: 30,
    passwordPolicy: {
      minLength: 12,
      requireSpecialChars: true,
      requireNumbers: true,
      requireUppercase: true
    },
    ipWhitelist: ['192.168.1.0/24', '10.0.0.0/8'],
    auditRetention: 90
  });
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'users' | 'system' | 'security'>('users');

  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setUsers([
        {
          id: '1',
          name: 'John Admin',
          email: 'admin@company.com',
          role: 'admin',
          status: 'active',
          lastLogin: '2024-01-15T10:30:00Z',
          createdAt: '2023-06-15T09:00:00Z'
        },
        {
          id: '2',
          name: 'Sarah Analyst',
          email: 'analyst@company.com',
          role: 'analyst',
          status: 'active',
          lastLogin: '2024-01-15T09:45:00Z',
          createdAt: '2023-08-10T14:30:00Z'
        },
        {
          id: '3',
          name: 'Mike Operator',
          email: 'operator@company.com',
          role: 'operator',
          status: 'active',
          lastLogin: '2024-01-15T08:20:00Z',
          createdAt: '2023-10-05T11:15:00Z'
        },
        {
          id: '4',
          name: 'Lisa Viewer',
          email: 'viewer@company.com',
          role: 'viewer',
          status: 'inactive',
          lastLogin: '2024-01-10T16:00:00Z',
          createdAt: '2023-12-01T10:00:00Z'
        }
      ]);
      setIsLoading(false);
    }, 1000);
  }, []);

  const getRoleColor = (role: User['role']) => {
    switch (role) {
      case 'admin':
        return 'bg-error text-white';
      case 'analyst':
        return 'bg-primary text-white';
      case 'operator':
        return 'bg-warning text-text-primary';
      case 'viewer':
        return 'bg-gray-500 text-white';
      default:
        return 'bg-gray-500 text-white';
    }
  };

  const getStatusColor = (status: User['status']) => {
    switch (status) {
      case 'active':
        return 'bg-success text-white';
      case 'inactive':
        return 'bg-gray-500 text-white';
      case 'suspended':
        return 'bg-error text-white';
      default:
        return 'bg-gray-500 text-white';
    }
  };

  const getServiceStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-success';
      case 'warning':
        return 'text-warning';
      case 'error':
        return 'text-error';
      default:
        return 'text-text-secondary';
    }
  };

  const handleUpdateUser = (userId: string, updates: Partial<User>) => {
    setUsers(users.map(user => 
      user.id === userId ? { ...user, ...updates } : user
    ));
  };

  const handleUpdateSecurityConfig = (config: Partial<SecurityConfig>) => {
    setSecurityConfig({ ...securityConfig, ...config });
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
          <h1 className="text-3xl font-bold text-text-primary mb-2">Admin Dashboard</h1>
          <p className="text-text-secondary">System administration and configuration</p>
        </div>
        <div className="flex space-x-2">
          <button className="bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg font-medium">
            System Backup
          </button>
          <button className="bg-secondary hover:bg-secondary-dark text-text-primary px-4 py-2 rounded-lg font-medium border border-border">
            Export Config
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-background-secondary rounded-lg border border-border mb-6">
        <div className="flex">
          <button
            onClick={() => setActiveTab('users')}
            className={`px-6 py-3 font-medium rounded-tl-lg ${
              activeTab === 'users'
                ? 'bg-primary text-white'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            User Management
          </button>
          <button
            onClick={() => setActiveTab('system')}
            className={`px-6 py-3 font-medium ${
              activeTab === 'system'
                ? 'bg-primary text-white'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            System Health
          </button>
          <button
            onClick={() => setActiveTab('security')}
            className={`px-6 py-3 font-medium rounded-tr-lg ${
              activeTab === 'security'
                ? 'bg-primary text-white'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            Security Config
          </button>
        </div>
      </div>

      {/* User Management Tab */}
      {activeTab === 'users' && (
        <div className="space-y-6">
          <div className="bg-background-secondary rounded-lg border border-border">
            <div className="px-6 py-4 border-b border-border flex justify-between items-center">
              <h3 className="text-lg font-semibold text-text-primary">Users ({users.length})</h3>
              <button className="bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg font-medium">
                Add User
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-background-primary">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                      User
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                      Role
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                      Last Login
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                      Created
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-text-secondary uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {users.map((user) => (
                    <tr key={user.id} className="hover:bg-background-primary">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center space-x-3">
                          <div className="w-10 h-10 bg-primary rounded-full flex items-center justify-center">
                            <span className="text-sm text-white font-medium">
                              {user.name.split(' ').map(n => n[0]).join('')}
                            </span>
                          </div>
                          <div>
                            <div className="text-sm font-medium text-text-primary">{user.name}</div>
                            <div className="text-sm text-text-secondary">{user.email}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRoleColor(user.role)}`}>
                          {user.role}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(user.status)}`}>
                          {user.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-text-primary">
                        {new Date(user.lastLogin).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-text-secondary">
                        {new Date(user.createdAt).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button className="text-primary hover:text-primary-dark mr-3">
                          Edit
                        </button>
                        <button 
                          onClick={() => handleUpdateUser(user.id, { 
                            status: user.status === 'active' ? 'suspended' : 'active' 
                          })}
                          className="text-warning hover:text-warning-dark"
                        >
                          {user.status === 'active' ? 'Suspend' : 'Activate'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* System Health Tab */}
      {activeTab === 'system' && (
        <div className="space-y-6">
          {/* Resource Usage */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-background-secondary rounded-lg p-6 border border-border">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-medium text-text-secondary">CPU Usage</h4>
                <span className="text-lg font-bold text-text-primary">{systemHealth.cpu}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-primary h-2 rounded-full" 
                  style={{ width: `${systemHealth.cpu}%` }}
                ></div>
              </div>
            </div>
            <div className="bg-background-secondary rounded-lg p-6 border border-border">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-medium text-text-secondary">Memory</h4>
                <span className="text-lg font-bold text-text-primary">{systemHealth.memory}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-warning h-2 rounded-full" 
                  style={{ width: `${systemHealth.memory}%` }}
                ></div>
              </div>
            </div>
            <div className="bg-background-secondary rounded-lg p-6 border border-border">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-medium text-text-secondary">Disk Usage</h4>
                <span className="text-lg font-bold text-text-primary">{systemHealth.disk}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-error h-2 rounded-full" 
                  style={{ width: `${systemHealth.disk}%` }}
                ></div>
              </div>
            </div>
            <div className="bg-background-secondary rounded-lg p-6 border border-border">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-medium text-text-secondary">Network</h4>
                <span className="text-lg font-bold text-text-primary">{systemHealth.network}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-success h-2 rounded-full" 
                  style={{ width: `${systemHealth.network}%` }}
                ></div>
              </div>
            </div>
          </div>

          {/* Services Status */}
          <div className="bg-background-secondary rounded-lg border border-border">
            <div className="px-6 py-4 border-b border-border">
              <h3 className="text-lg font-semibold text-text-primary">Service Status</h3>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {systemHealth.services.map((service) => (
                  <div key={service.name} className="flex items-center justify-between p-4 bg-background-primary rounded-lg">
                    <div>
                      <h4 className="text-sm font-medium text-text-primary">{service.name}</h4>
                      <p className="text-xs text-text-secondary">Uptime: {service.uptime}</p>
                    </div>
                    <div className={`w-3 h-3 rounded-full ${getServiceStatusColor(service.status)} bg-current`}></div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Security Configuration Tab */}
      {activeTab === 'security' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Authentication Settings */}
            <div className="bg-background-secondary rounded-lg border border-border">
              <div className="px-6 py-4 border-b border-border">
                <h3 className="text-lg font-semibold text-text-primary">Authentication</h3>
              </div>
              <div className="p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-text-primary">Multi-Factor Authentication</label>
                  <button
                    onClick={() => handleUpdateSecurityConfig({ mfaEnabled: !securityConfig.mfaEnabled })}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full ${
                      securityConfig.mfaEnabled ? 'bg-primary' : 'bg-gray-200'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                        securityConfig.mfaEnabled ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-2">
                    Session Timeout (minutes)
                  </label>
                  <input
                    type="number"
                    value={securityConfig.sessionTimeout}
                    onChange={(e) => handleUpdateSecurityConfig({ sessionTimeout: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border border-border rounded-lg bg-background-primary text-text-primary focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                  />
                </div>
              </div>
            </div>

            {/* Password Policy */}
            <div className="bg-background-secondary rounded-lg border border-border">
              <div className="px-6 py-4 border-b border-border">
                <h3 className="text-lg font-semibold text-text-primary">Password Policy</h3>
              </div>
              <div className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-2">
                    Minimum Length
                  </label>
                  <input
                    type="number"
                    value={securityConfig.passwordPolicy.minLength}
                    onChange={(e) => handleUpdateSecurityConfig({ 
                      passwordPolicy: { 
                        ...securityConfig.passwordPolicy, 
                        minLength: parseInt(e.target.value) 
                      } 
                    })}
                    className="w-full px-3 py-2 border border-border rounded-lg bg-background-primary text-text-primary focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                  />
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="text-sm text-text-primary">Require Special Characters</label>
                    <input
                      type="checkbox"
                      checked={securityConfig.passwordPolicy.requireSpecialChars}
                      onChange={(e) => handleUpdateSecurityConfig({ 
                        passwordPolicy: { 
                          ...securityConfig.passwordPolicy, 
                          requireSpecialChars: e.target.checked 
                        } 
                      })}
                      className="rounded border-border"
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <label className="text-sm text-text-primary">Require Numbers</label>
                    <input
                      type="checkbox"
                      checked={securityConfig.passwordPolicy.requireNumbers}
                      onChange={(e) => handleUpdateSecurityConfig({ 
                        passwordPolicy: { 
                          ...securityConfig.passwordPolicy, 
                          requireNumbers: e.target.checked 
                        } 
                      })}
                      className="rounded border-border"
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <label className="text-sm text-text-primary">Require Uppercase</label>
                    <input
                      type="checkbox"
                      checked={securityConfig.passwordPolicy.requireUppercase}
                      onChange={(e) => handleUpdateSecurityConfig({ 
                        passwordPolicy: { 
                          ...securityConfig.passwordPolicy, 
                          requireUppercase: e.target.checked 
                        } 
                      })}
                      className="rounded border-border"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* IP Whitelist */}
            <div className="bg-background-secondary rounded-lg border border-border lg:col-span-2">
              <div className="px-6 py-4 border-b border-border">
                <h3 className="text-lg font-semibold text-text-primary">IP Whitelist</h3>
              </div>
              <div className="p-6">
                <div className="space-y-2">
                  {securityConfig.ipWhitelist.map((ip, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-background-primary rounded-lg">
                      <span className="text-text-primary font-mono">{ip}</span>
                      <button className="text-error hover:text-error-dark">
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
                <button className="mt-4 bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg font-medium">
                  Add IP Range
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
