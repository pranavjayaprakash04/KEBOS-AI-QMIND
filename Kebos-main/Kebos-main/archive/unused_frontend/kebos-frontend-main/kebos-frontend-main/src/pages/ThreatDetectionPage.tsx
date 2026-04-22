import{ useState } from "react";

import {
  Shield,
  AlertTriangle,
  Eye,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Activity,
} from "lucide-react";

interface ThreatAlert {
  id: string;
  title: string;
  severity: "critical" | "high" | "medium" | "low";
  source: string;
  timestamp: string;
  status: "active" | "investigating" | "resolved" | "mitigated";
  description: string;
  affectedSystems?: string[];
  indicators?: string[];
  mitigations?: string[];
  type?: string;
}

export function ThreatDetectionPage() {
  const [selectedAlert, setSelectedAlert] = useState<ThreatAlert | null>(null);
    const filters = {
    severity: "all" as const,
    status: "all" as const,
    timeRange: "24h" as const,
  };
  const [isUpdating, setIsUpdating] = useState(false);

  // Mock data
  const alerts: ThreatAlert[] = [
    {
      id: "1",
      title: "Suspicious API Access",
      severity: "high",
      source: "API Gateway",
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      status: "active",
      description:
        "Unusual API access pattern detected from an unauthorized IP address.",
      type: "API_SECURITY",
      affectedSystems: ["API Gateway", "Authentication Service"],
      indicators: [
        "Multiple failed authentication attempts",
        "Unusual access patterns",
        "Rate limit exceeded",
      ],
      mitigations: [
        "Block IP address",
        "Enforce additional authentication",
        "Review API access logs",
      ],
    },
    {
      id: "2",
      title: "Prompt Injection Attempt",
      severity: "critical",
      source: "AI Assistant",
      timestamp: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
      status: "investigating",
      description:
        "Detected attempt to manipulate AI system through malicious prompt engineering.",
      type: "PROMPT_INJECTION",
      affectedSystems: ["AI Assistant", "Content Generation Service"],
      indicators: [
        "Suspicious prompt patterns",
        "System instruction override attempts",
        "Abnormal output generation",
      ],
      mitigations: [
        "Block user access",
        "Update prompt filtering rules",
        "Review recent AI interactions",
      ],
    },
    {
      id: "3",
      title: "Data Exfiltration",
      severity: "critical",
      source: "DLP System",
      timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
      status: "active",
      description:
        "Potential data exfiltration detected through unusual data transfer patterns.",
      type: "DATA_SECURITY",
      affectedSystems: ["Database Server", "File Storage Service"],
      indicators: [
        "Large data transfer",
        "Unusual access times",
        "Unauthorized database queries",
      ],
      mitigations: [
        "Isolate affected systems",
        "Review access logs",
        "Implement additional monitoring",
      ],
    },
    {
      id: "4",
      title: "Model Poisoning Attempt",
      severity: "medium",
      source: "Training Pipeline",
      timestamp: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
      status: "mitigated",
      description:
        "Detected attempt to poison training data for machine learning models.",
      type: "MODEL_SECURITY",
      affectedSystems: [
        "Model Training Service",
        "Data Preprocessing Pipeline",
      ],
      indicators: [
        "Anomalous training data",
        "Unexpected model behavior",
        "Data integrity issues",
      ],
      mitigations: [
        "Rollback to previous model version",
        "Implement data validation checks",
        "Review data sources",
      ],
    },
    {
      id: "5",
      title: "Unauthorized Access",
      severity: "medium",
      source: "Admin Console",
      timestamp: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
      status: "resolved",
      description: "Unauthorized access attempt to admin console detected.",
      type: "ACCESS_CONTROL",
      affectedSystems: ["Admin Console", "User Management Service"],
      indicators: [
        "Failed login attempts",
        "Password guessing patterns",
        "Access from unusual location",
      ],
      mitigations: ["Account lockout", "IP blocking", "Enhanced monitoring"],
    },
  ];

  // Filter alerts based on filters
  const filteredAlerts = alerts.filter((alert) => {
    if (filters.severity !== "all" && alert.severity !== filters.severity)
      return false;
    if (filters.status !== "all" && alert.status !== filters.status)
      return false;
    return true;
  });

  // Helper functions
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  const formatTimeAgo = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (seconds < 60) return `${seconds} seconds ago`;

    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes} minute${minutes !== 1 ? "s" : ""} ago`;

    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} hour${hours !== 1 ? "s" : ""} ago`;

    const days = Math.floor(hours / 24);
    return `${days} day${days !== 1 ? "s" : ""} ago`;
  };

  const getSeverityColor = (severity: ThreatAlert["severity"]) => {
    switch (severity) {
      case "critical":
        return "bg-red-100 text-red-700 border-red-200";
      case "high":
        return "bg-orange-100 text-orange-700 border-orange-200";
      case "medium":
        return "bg-amber-100 text-amber-700 border-amber-200";
      case "low":
        return "bg-blue-100 text-blue-700 border-blue-200";
      default:
        return "bg-slate-100 text-slate-700 border-slate-200";
    }
  };

  const getStatusColor = (status: ThreatAlert["status"]) => {
    switch (status) {
      case "active":
        return "bg-red-100 text-red-700 border-red-200";
      case "investigating":
        return "bg-amber-100 text-amber-700 border-amber-200";
      case "mitigated":
        return "bg-blue-100 text-blue-700 border-blue-200";
      case "resolved":
        return "bg-emerald-100 text-emerald-700 border-emerald-200";
      default:
        return "bg-slate-100 text-slate-700 border-slate-200";
    }
  };

  const getStatusIcon = (status: ThreatAlert["status"]) => {
    switch (status) {
      case "active":
        return <AlertCircle className="w-4 h-4" />;
      case "investigating":
        return <Eye className="w-4 h-4" />;
      case "mitigated":
        return <Shield className="w-4 h-4" />;
      case "resolved":
        return <CheckCircle className="w-4 h-4" />;
      default:
        return <Activity className="w-4 h-4" />;
    }
  };

  const getSeverityIcon = (severity: ThreatAlert["severity"]) => {
    switch (severity) {
      case "critical":
        return <XCircle className="w-4 h-4" />;
      case "high":
        return <AlertTriangle className="w-4 h-4" />;
      case "medium":
        return <AlertCircle className="w-4 h-4" />;
      case "low":
        return <Shield className="w-4 h-4" />;
      default:
        return <Activity className="w-4 h-4" />;
    }
  };

  const handleAlertSelect = (alert: ThreatAlert) => {
    setSelectedAlert(alert);
  };

  const handleStatusUpdate = async (alertId: string, status: string) => {
    setIsUpdating(true);
    // Simulate API call to update alert status
    console.log(`Updating alert ${alertId} to status: ${status}`);
    setTimeout(() => {
      setIsUpdating(false);
      // In real app, would update the alert and refresh data
    }, 1500);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm border-b border-slate-200/50 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-gradient-to-br from-red-500 to-orange-600 rounded-lg shadow-lg">
              <AlertTriangle className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">
                Threat Detection
              </h1>
              <p className="text-slate-600">
                Monitor and respond to security threats across your environment
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Statistics Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-6 hover:shadow-2xl transition-all duration-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-3xl font-bold text-red-600">
                  {filteredAlerts.filter((a) => a.status === "active").length}
                </p>
                <p className="text-slate-600 text-sm font-medium">
                  Active Threats
                </p>
              </div>
              <div className="p-3 bg-red-100 rounded-xl">
                <AlertTriangle className="w-6 h-6 text-red-600" />
              </div>
            </div>
          </div>
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-6 hover:shadow-2xl transition-all duration-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-3xl font-bold text-amber-600">
                  {
                    filteredAlerts.filter((a) => a.status === "investigating")
                      .length
                  }
                </p>
                <p className="text-slate-600 text-sm font-medium">
                  Under Investigation
                </p>
              </div>
              <div className="p-3 bg-amber-100 rounded-xl">
                <Eye className="w-6 h-6 text-amber-600" />
              </div>
            </div>
          </div>
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-6 hover:shadow-2xl transition-all duration-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-3xl font-bold text-emerald-600">
                  {filteredAlerts.filter((a) => a.status === "resolved").length}
                </p>
                <p className="text-slate-600 text-sm font-medium">Resolved</p>
              </div>
              <div className="p-3 bg-emerald-100 rounded-xl">
                <CheckCircle className="w-6 h-6 text-emerald-600" />
              </div>
            </div>
          </div>
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-6 hover:shadow-2xl transition-all duration-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-3xl font-bold text-indigo-600">
                  {filteredAlerts.length}
                </p>
                <p className="text-slate-600 text-sm font-medium">
                  Total Alerts
                </p>
              </div>
              <div className="p-3 bg-indigo-100 rounded-xl">
                <Shield className="w-6 h-6 text-indigo-600" />
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Threats list */}
          <div className="lg:col-span-1">
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-6">
              <h3 className="text-xl font-semibold text-slate-800 mb-6">
                Detected Threats
              </h3>
              {filteredAlerts.length > 0 ? (
                <div className="space-y-4 max-h-[calc(100vh-400px)] overflow-y-auto pr-2">
                  {filteredAlerts.map((alert) => (
                    <div
                      key={alert.id}
                      onClick={() => handleAlertSelect(alert)}
                      className={`group p-4 rounded-xl cursor-pointer transition-all duration-200 border ${
                        selectedAlert?.id === alert.id
                          ? "bg-gradient-to-r from-indigo-500 to-purple-600 text-white border-indigo-300 shadow-lg"
                          : "bg-white/80 backdrop-blur-sm hover:bg-white border-slate-200 hover:border-indigo-300 hover:shadow-md"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-3">
                          <div
                            className={`p-2 rounded-lg ${
                              selectedAlert?.id === alert.id
                                ? "bg-white/20"
                                : getSeverityColor(alert.severity)
                            }`}
                          >
                            {getSeverityIcon(alert.severity)}
                          </div>
                          <div>
                            <p
                              className={`font-medium ${
                                selectedAlert?.id === alert.id
                                  ? "text-white"
                                  : "text-slate-800"
                              }`}
                            >
                              {alert.title}
                            </p>
                            <p
                              className={`text-xs ${
                                selectedAlert?.id === alert.id
                                  ? "text-indigo-100"
                                  : "text-slate-500"
                              }`}
                            >
                              {formatTimeAgo(alert.timestamp)}
                            </p>
                          </div>
                        </div>
                        <span
                          className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                            selectedAlert?.id === alert.id
                              ? "bg-white/20 text-white border border-white/30"
                              : getStatusColor(alert.status)
                          }`}
                        >
                          {alert.status}
                        </span>
                      </div>
                      <p
                        className={`text-sm mb-3 line-clamp-2 ${
                          selectedAlert?.id === alert.id
                            ? "text-indigo-100"
                            : "text-slate-600"
                        }`}
                      >
                        {alert.description}
                      </p>
                      <div className="flex items-center justify-between">
                        <div className="flex space-x-2">
                          <span
                            className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                              selectedAlert?.id === alert.id
                                ? "bg-white/20 text-white"
                                : "bg-slate-100 text-slate-700"
                            }`}
                          >
                            {alert.type}
                          </span>
                        </div>
                        <div
                          className={`flex items-center space-x-1 text-xs ${
                            selectedAlert?.id === alert.id
                              ? "text-indigo-100"
                              : "text-slate-500"
                          }`}
                        >
                          <Clock className="w-3 h-3" />
                          <span>{formatTimeAgo(alert.timestamp)}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-12">
                  <div className="p-4 bg-slate-100 rounded-2xl w-16 h-16 flex items-center justify-center mb-4">
                    <Shield className="w-8 h-8 text-slate-400" />
                  </div>
                  <p className="text-slate-500 font-medium mb-2">
                    No threats detected
                  </p>
                  <p className="text-slate-400 text-sm text-center">
                    Your environment is secure
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Threat details */}
          <div className="lg:col-span-2">
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-6">
              {selectedAlert ? (
                <div>
                  <div className="flex justify-between items-start mb-6">
                    <div className="flex items-center space-x-3">
                      <div className="p-3 bg-gradient-to-br from-red-500 to-orange-600 rounded-xl shadow-lg">
                        {getSeverityIcon(selectedAlert.severity)}
                      </div>
                      <div>
                        <h3 className="text-2xl font-semibold text-slate-800">
                          {selectedAlert.title}
                        </h3>
                        <p className="text-slate-600">
                          {selectedAlert.description}
                        </p>
                      </div>
                    </div>
                    <span
                      className={`text-sm px-3 py-1 rounded-full border font-medium ${getSeverityColor(selectedAlert.severity)}`}
                    >
                      {selectedAlert.severity.toUpperCase()}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
                    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-4 rounded-xl border border-blue-100">
                      <p className="text-sm text-slate-600 mb-1">Detected</p>
                      <p className="font-semibold text-slate-800">
                        {formatTimestamp(selectedAlert.timestamp)}
                      </p>
                    </div>
                    <div className="bg-gradient-to-br from-purple-50 to-pink-50 p-4 rounded-xl border border-purple-100">
                      <p className="text-sm text-slate-600 mb-1">Source</p>
                      <p className="font-semibold text-slate-800">
                        {selectedAlert.source}
                      </p>
                    </div>
                    <div className="bg-gradient-to-br from-emerald-50 to-teal-50 p-4 rounded-xl border border-emerald-100">
                      <p className="text-sm text-slate-600 mb-1">Status</p>
                      <p className="font-semibold text-slate-800">
                        {selectedAlert.status}
                      </p>
                    </div>
                    <div className="bg-gradient-to-br from-amber-50 to-orange-50 p-4 rounded-xl border border-amber-100">
                      <p className="text-sm text-slate-600 mb-1">Type</p>
                      <p className="font-semibold text-slate-800">
                        {selectedAlert.type || "Unknown"}
                      </p>
                    </div>
                  </div>

                  {selectedAlert.affectedSystems &&
                    selectedAlert.affectedSystems.length > 0 && (
                      <div className="mb-8">
                        <h4 className="text-lg font-semibold text-slate-800 mb-4">
                          Affected Systems
                        </h4>
                        <div className="flex flex-wrap gap-2">
                          {selectedAlert.affectedSystems.map(
                            (system, index) => (
                              <span
                                key={index}
                                className="bg-indigo-100 text-indigo-700 px-3 py-1 rounded-full text-sm border border-indigo-200"
                              >
                                {system}
                              </span>
                            )
                          )}
                        </div>
                      </div>
                    )}

                  {selectedAlert.indicators &&
                    selectedAlert.indicators.length > 0 && (
                      <div className="mb-8">
                        <h4 className="text-lg font-semibold text-slate-800 mb-4">
                          Indicators
                        </h4>
                        <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
                          <ul className="space-y-2">
                            {selectedAlert.indicators.map(
                              (indicator, index) => (
                                <li
                                  key={index}
                                  className="flex items-start space-x-2"
                                >
                                  <div className="w-1.5 h-1.5 bg-amber-400 rounded-full mt-2 flex-shrink-0"></div>
                                  <span className="text-slate-700">
                                    {indicator}
                                  </span>
                                </li>
                              )
                            )}
                          </ul>
                        </div>
                      </div>
                    )}

                  {selectedAlert.mitigations &&
                    selectedAlert.mitigations.length > 0 && (
                      <div className="mb-8">
                        <h4 className="text-lg font-semibold text-slate-800 mb-4">
                          Recommended Mitigations
                        </h4>
                        <div className="bg-emerald-50 rounded-xl p-4 border border-emerald-200">
                          <ul className="space-y-2">
                            {selectedAlert.mitigations.map(
                              (mitigation, index) => (
                                <li
                                  key={index}
                                  className="flex items-start space-x-2"
                                >
                                  <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full mt-2 flex-shrink-0"></div>
                                  <span className="text-slate-700">
                                    {mitigation}
                                  </span>
                                </li>
                              )
                            )}
                          </ul>
                        </div>
                      </div>
                    )}

                  <div className="border-t border-slate-200 pt-6">
                    <h4 className="text-lg font-semibold text-slate-800 mb-4">
                      Update Status
                    </h4>
                    <div className="flex flex-wrap gap-3">
                      {["active", "investigating", "mitigated", "resolved"].map(
                        (status) => (
                          <button
                            key={status}
                            onClick={() =>
                              handleStatusUpdate(selectedAlert.id, status)
                            }
                            disabled={
                              selectedAlert.status === status || isUpdating
                            }
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 flex items-center space-x-2 ${
                              selectedAlert.status === status
                                ? getStatusColor(
                                    status as ThreatAlert["status"]
                                  ) + " cursor-not-allowed"
                                : "bg-slate-100 hover:bg-slate-200 text-slate-700 hover:shadow-md"
                            }`}
                          >
                            {getStatusIcon(status as ThreatAlert["status"])}
                            <span className="capitalize">{status}</span>
                          </button>
                        )
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-96">
                  <div className="p-6 bg-slate-100 rounded-2xl w-24 h-24 flex items-center justify-center mb-6">
                    <Shield className="w-12 h-12 text-slate-400" />
                  </div>
                  <h3 className="text-xl font-semibold text-slate-700 mb-3">
                    No threat selected
                  </h3>
                  <p className="text-slate-500 text-center max-w-md mb-6">
                    Select a threat from the list to view detailed information
                    and take action.
                  </p>
                  <button className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-lg font-medium shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105">
                    Export Report
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Threat Alerts Table */}
        <div className="mt-8 bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-200/50 bg-white/50">
            <h3 className="text-lg font-semibold text-slate-800">
              Recent Threat Alerts
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50/50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">
                    Alert
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">
                    Severity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">
                    Source
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">
                    Timestamp
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-slate-600 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200/50">
                {filteredAlerts.map((alert) => (
                  <tr
                    key={alert.id}
                    className="hover:bg-white/50 transition-colors duration-200"
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center space-x-3">
                        <div className="p-2 bg-slate-100 rounded-lg">
                          {getSeverityIcon(alert.severity)}
                        </div>
                        <div>
                          <div className="text-sm font-medium text-slate-800">
                            {alert.title}
                          </div>
                          <div className="text-sm text-slate-600 max-w-xs truncate">
                            {alert.description}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getSeverityColor(alert.severity)}`}
                      >
                        {alert.severity.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-700">
                      {alert.source}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(alert.status)}`}
                      >
                        {getStatusIcon(alert.status)}
                        <span className="ml-1">{alert.status}</span>
                      </span>
                    </td>

                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => handleAlertSelect(alert)}
                        className="text-indigo-600 hover:text-indigo-900 transition-colors duration-200"
                      >
                        View Details
                      </button>
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

export default ThreatDetectionPage;
