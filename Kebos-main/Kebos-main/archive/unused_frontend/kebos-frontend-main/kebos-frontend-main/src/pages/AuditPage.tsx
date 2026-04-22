import { useState, useEffect } from "react";
import CustomDropdown from "../components/CustomDropdown";

interface AuditLog {
  id: string;
  timestamp: string;
  user: string;
  action: string;
  resource: string;
  result: "success" | "failure" | "warning";
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
    configChanges: 12,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState("all");

  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setAuditLogs([
        {
          id: "1",
          timestamp: "2024-01-15T10:30:00Z",
          user: "admin@company.com",
          action: "LOGIN_SUCCESS",
          resource: "Authentication System",
          result: "success",
          ipAddress: "192.168.1.100",
          userAgent: "Mozilla/5.0 Chrome/120.0",
          details: "Successful administrator login from corporate network",
        },
        {
          id: "2",
          timestamp: "2024-01-15T10:25:00Z",
          user: "analyst@company.com",
          action: "DATA_ACCESS",
          resource: "Threat Intelligence Database",
          result: "success",
          ipAddress: "192.168.1.105",
          userAgent: "Mozilla/5.0 Chrome/120.0",
          details: "Accessed threat intelligence data for analysis",
        },
        {
          id: "3",
          timestamp: "2024-01-15T10:20:00Z",
          user: "unknown",
          action: "LOGIN_FAILED",
          resource: "Authentication System",
          result: "failure",
          ipAddress: "203.0.113.45",
          userAgent: "curl/7.68.0",
          details: "Failed login attempt with invalid credentials",
        },
        {
          id: "4",
          timestamp: "2024-01-15T10:15:00Z",
          user: "sysadmin@company.com",
          action: "CONFIG_CHANGE",
          resource: "Firewall Rules",
          result: "success",
          ipAddress: "192.168.1.50",
          userAgent: "Mozilla/5.0 Firefox/120.0",
          details: "Updated firewall rules to block suspicious IP range",
        },
        {
          id: "5",
          timestamp: "2024-01-15T10:10:00Z",
          user: "operator@company.com",
          action: "THREAT_INVESTIGATION",
          resource: "Security Dashboard",
          result: "warning",
          ipAddress: "192.168.1.110",
          userAgent: "Mozilla/5.0 Chrome/120.0",
          details: "Investigated security alert - potential false positive",
        },
      ]);
      setIsLoading(false);
    }, 1000);
  }, []);

  const getResultColor = (result: AuditLog["result"]) => {
    switch (result) {
      case "success":
        return "bg-success text-white";
      case "failure":
        return "bg-error text-white";
      case "warning":
        return "bg-warning text-text-primary";
      default:
        return "bg-gray-500 text-white";
    }
  };

  const getActionIcon = (action: string) => {
    if (action.includes("LOGIN")) {
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
            d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"
          />
        </svg>
      );
    }
    if (action.includes("DATA")) {
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
            d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"
          />
        </svg>
      );
    }
    if (action.includes("CONFIG")) {
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
            d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
          />
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
          />
        </svg>
      );
    }
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
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
        />
      </svg>
    );
  };

  const filteredLogs = auditLogs.filter((log) => {
    const matchesSearch =
      log.user.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.resource.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterType === "all" || log.result === filterType;
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

  // Add filter options
  const filterOptions = [
    { value: "all", label: "All Results" },
    { value: "success", label: "Success" },
    { value: "failure", label: "Failure" },
    { value: "warning", label: "Warning" },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm border-b border-slate-200/50 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-gradient-to-br from-yellow-500 to-amber-600 rounded-lg shadow-lg">
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
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                />
              </svg>
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">
                Audit & Monitoring
              </h1>
              <p className="text-slate-600">
                Security audit trails and threat monitoring
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Action Buttons */}
        <div className="flex justify-end space-x-4">
          <button className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-lg font-medium shadow-lg hover:shadow-xl transition-all duration-200">
            Export Logs
          </button>
          <button className="px-6 py-3 bg-white/80 backdrop-blur-sm text-slate-700 rounded-lg font-medium border border-slate-200 hover:shadow-lg transition-all duration-200">
            Generate Report
          </button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-6 relative z-10">
          {/* Total Actions */}
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-6 hover:shadow-2xl transition-all duration-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-3xl font-bold text-indigo-600">
                  {stats.totalActions.toLocaleString()}
                </p>
                <p className="text-slate-600 text-sm font-medium">
                  Total Actions
                </p>
              </div>
              
            </div>
          </div>

          {/* Similar styled cards for other stats... */}
        </div>

        {/* Search and Filter */}
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-6 relative z-30">
          <div className="flex flex-col md:flex-row md:items-end md:justify-between space-y-4 md:space-y-0 md:space-x-6">
            <div className="flex-1">
              <label className="block text-sm font-semibold text-slate-700 mb-2">
                Search Logs
              </label>
              <input
                type="text"
                placeholder="Search by user, action, or resource..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-700 placeholder-slate-400 focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-shadow"
              />
            </div>
            <div className="min-w-[200px] relative z-40">
              <CustomDropdown
                label="Filter by Result"
                value={filterType}
                options={filterOptions}
                onChange={setFilterType}
              />
            </div>
          </div>
        </div>

        {/* Audit Logs Table */}
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 overflow-hidden relative z-10">
          <div className="px-6 py-4 border-b border-slate-200/50">
            <h3 className="text-lg font-semibold text-slate-800">
              Audit Logs ({filteredLogs.length} entries)
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50/50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">
                    Timestamp
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">
                    Action
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">
                    Resource
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">
                    Result
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">
                    IP Address
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200/50 bg-white/50">
                {filteredLogs.map((log) => (
                  <tr
                    key={log.id}
                    className="hover:bg-white/80 transition-colors duration-200"
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-700">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-700">
                      {log.user}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-700">
                      <div className="flex items-center space-x-2">
                        {getActionIcon(log.action)}
                        <span>{log.action.replace("_", " ")}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-700">
                      {log.resource}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-semibold ${getResultColor(log.result)}`}
                      >
                        {log.result.charAt(0).toUpperCase() +
                          log.result.slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-700">
                      {log.ipAddress}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
