

export function AttackSimDashboard() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-text-primary mb-2">Attack Simulation Dashboard</h1>
        <p className="text-text-secondary">Monitor and manage your security simulation campaigns</p>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-background-secondary rounded-lg p-6 border border-border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-text-secondary text-sm">Active Campaigns</p>
              <p className="text-2xl font-bold text-primary">5</p>
            </div>
            <div className="w-12 h-12 bg-primary-light rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-background-secondary rounded-lg p-6 border border-border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-text-secondary text-sm">Total Targets</p>
              <p className="text-2xl font-bold text-warning">1,245</p>
            </div>
            <div className="w-12 h-12 bg-warning-light rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-warning" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-background-secondary rounded-lg p-6 border border-border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-text-secondary text-sm">Success Rate</p>
              <p className="text-2xl font-bold text-error">23%</p>
            </div>
            <div className="w-12 h-12 bg-error-light rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-error" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="bg-background-secondary rounded-lg p-6 border border-border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-text-secondary text-sm">Scenarios</p>
              <p className="text-2xl font-bold text-success">12</p>
            </div>
            <div className="w-12 h-12 bg-success-light rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v6a2 2 0 002 2h6a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="bg-background-secondary rounded-lg p-6 border border-border">
          <h3 className="text-lg font-semibold text-text-primary mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <button className="w-full bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg font-medium">
              Create New Campaign
            </button>
            <button className="w-full bg-secondary hover:bg-secondary-dark text-text-primary px-4 py-2 rounded-lg font-medium border border-border">
              Launch Scenario
            </button>
            <button className="w-full bg-secondary hover:bg-secondary-dark text-text-primary px-4 py-2 rounded-lg font-medium border border-border">
              View Reports
            </button>
          </div>
        </div>

        <div className="bg-background-secondary rounded-lg p-6 border border-border">
          <h3 className="text-lg font-semibold text-text-primary mb-4">Recent Activity</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-background-primary rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-3 h-3 bg-success rounded-full"></div>
                <span className="text-text-primary text-sm">Phishing campaign completed</span>
              </div>
              <span className="text-text-secondary text-xs">2h ago</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-background-primary rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-3 h-3 bg-warning rounded-full"></div>
                <span className="text-text-primary text-sm">New scenario created</span>
              </div>
              <span className="text-text-secondary text-xs">4h ago</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-background-primary rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-3 h-3 bg-error rounded-full"></div>
                <span className="text-text-primary text-sm">High-risk target identified</span>
              </div>
              <span className="text-text-secondary text-xs">6h ago</span>
            </div>
          </div>
        </div>

        <div className="bg-background-secondary rounded-lg p-6 border border-border">
          <h3 className="text-lg font-semibold text-text-primary mb-4">Campaign Performance</h3>
          <div className="h-40 flex items-center justify-center text-text-secondary">
            <div className="text-center">
              <svg className="w-12 h-12 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <p className="text-sm">Chart placeholder</p>
              <p className="text-xs opacity-75">Install Chart.js for visualization</p>
            </div>
          </div>
        </div>
      </div>

      {/* Current Campaigns Table */}
      <div className="bg-background-secondary rounded-lg border border-border overflow-hidden">
        <div className="px-6 py-4 border-b border-border">
          <h3 className="text-lg font-semibold text-text-primary">Active Campaigns</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-background-primary">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                  Campaign
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                  Progress
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                  Success Rate
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-text-secondary uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              <tr className="hover:bg-background-primary">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-text-primary">Q1 Phishing Assessment</div>
                  <div className="text-sm text-text-secondary">250 targets</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-text-primary">Phishing</td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="w-16 bg-gray-200 rounded-full h-2 mr-3">
                      <div className="bg-primary h-2 rounded-full" style={{ width: '65%' }}></div>
                    </div>
                    <span className="text-sm text-text-secondary">65%</span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-error">23%</td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <button className="text-primary hover:text-primary-dark mr-3">View</button>
                  <button className="text-warning hover:text-warning-dark">Pause</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
