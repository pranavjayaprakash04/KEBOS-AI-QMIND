import { Line, Pie, Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  BarElement,
} from "chart.js";
import { RecentActivity as ServiceRecentActivity } from "@/services/dashboardService";
import { ThreatSeverity } from "@/types";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  BarElement
);

export function DashboardPage() {
  // Fetch dashboard metrics
  const { data: metrics, isLoading: metricsLoading } = useQuery({
    queryKey: ["dashboardMetrics"],
    queryFn: async () => {
      try {
        // In a real implementation, this would fetch from the backend
        // const response = await apiClient.get('/api/dashboard/metrics');
        // return response.data;

        // Mock data for demonstration
        return {
          activeThreats: 24,
          attackSimulations: 8,
          activeJobs: 12,
          threatsByType: {
            malware: 8,
            phishing: 6,
            intrusion: 4,
            ddos: 2,
            data_exfiltration: 3,
            vulnerability_exploit: 1,
          },
          threatsBySeverity: {
            critical: 5,
            high: 8,
            medium: 7,
            low: 4,
          },
        };
      } catch (error) {
        console.error("Failed to fetch dashboard metrics:", error);
        throw error;
      }
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  // Fetch threat activity data
  const { data: threatActivity, isLoading: threatActivityLoading } = useQuery({
    queryKey: ["threatActivity"],
    queryFn: async () => {
      try {
        // In a real implementation, this would fetch from the backend
        // const response = await apiClient.get('/api/dashboard/threat-activity');
        // return response.data;

        // Mock data for demonstration
        return {
          labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"],
          datasets: [
            {
              label: "Critical Threats",
              data: [3, 5, 2, 8, 15, 12, 5],
              borderColor: "#ef4444",
              backgroundColor: "rgba(239, 68, 68, 0.2)",
            },
            {
              label: "High Threats",
              data: [7, 11, 5, 14, 22, 18, 8],
              borderColor: "#f97316",
              backgroundColor: "rgba(249, 115, 22, 0.2)",
            },
          ],
        };
      } catch (error) {
        console.error("Failed to fetch threat activity:", error);
        throw error;
      }
    },
    refetchInterval: 60000, // Refetch every minute
  });

  // Fetch recent activity
  const { data: recentActivity, isLoading: recentActivityLoading } = useQuery({
    queryKey: ["recentActivity"],
    queryFn: async () => {
      try {
        // In a real implementation, this would fetch from the backend
        // const response = await apiClient.get('/api/dashboard/recent-activity');
        // return response.data;

        // Mock data for demonstration
        return [
          {
            id: "1",
            type: "threat",
            message: "High severity threat detected",
            timestamp: new Date(Date.now() - 2 * 60 * 1000).toISOString(),
            severity: ThreatSeverity.HIGH,
          },
          {
            id: "2",
            type: "simulation",
            message: "Attack simulation completed",
            timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
          },
          {
            id: "3",
            type: "threat",
            message: "Critical vulnerability exploit attempt",
            timestamp: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
            severity: ThreatSeverity.CRITICAL,
          },
          {
            id: "4",
            type: "job",
            message: "Threat intelligence update completed",
            timestamp: new Date(Date.now() - 120 * 60 * 1000).toISOString(),
          },
          {
            id: "5",
            type: "job",
            message: "System maintenance completed",
            timestamp: new Date(Date.now() - 180 * 60 * 1000).toISOString(),
          },
        ] as ServiceRecentActivity[];
      } catch (error) {
        console.error("Failed to fetch recent activity:", error);
        throw error;
      }
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  // Format time ago
  const formatTimeAgo = (timestamp: string) => {
    const now = new Date();
    const date = new Date(timestamp);
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (seconds < 60) return `${seconds} sec ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes} min ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} hr ago`;
    const days = Math.floor(hours / 24);
    return `${days} day${days > 1 ? "s" : ""} ago`;
  };

  // Prepare threat distribution data for pie chart
  const threatDistributionData = {
    labels: metrics?.threatsByType
      ? Object.keys(metrics.threatsByType).map((key) =>
          key
            .split("_")
            .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
            .join(" ")
        )
      : [],
    datasets: [
      {
        data: metrics?.threatsByType
          ? Object.values(metrics.threatsByType)
          : [],
        backgroundColor: [
          "#ef4444", // red
          "#f97316", // orange
          "#eab308", // yellow
          "#22c55e", // green
          "#3b82f6", // blue
          "#8b5cf6", // purple
        ],
        borderWidth: 1,
      },
    ],
  };

  // Prepare severity distribution data for bar chart
  const severityDistributionData = {
    labels: metrics?.threatsBySeverity
      ? Object.keys(metrics.threatsBySeverity).map(
          (key) => key.charAt(0).toUpperCase() + key.slice(1)
        )
      : [],
    datasets: [
      {
        label: "Threats by Severity",
        data: metrics?.threatsBySeverity
          ? Object.values(metrics.threatsBySeverity)
          : [],
        backgroundColor: [
          "#ef4444", // critical - red
          "#f97316", // high - orange
          "#eab308", // medium - yellow
          "#22c55e", // low - green
        ],
      },
    ],
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm border-b border-slate-200/50 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg shadow-lg">
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
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">
                Cyber Threat Platform Dashboard
              </h1>
              <p className="text-slate-600">
                Real-time threat intelligence and security posture
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="card-hover p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-black text-sm font-medium">Active Threats</p>
                <p className="text-2xl font-bold text-error">
                  {metricsLoading ? "..." : metrics?.activeThreats}
                </p>
                <p className="text-xs text-gray-500 mt-1">+5% from last week</p>
              </div>
              <div className="w-12 h-12 bg-error-light rounded-lg flex items-center justify-center">
                <svg
                  className="w-6 h-6 text-error"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
                  />
                </svg>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.1 }}
            className="card-hover p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-text-primaryprimary text-sm font-medium">
                  Attack Simulations
                </p>
                <p className="text-2xl font-bold text-primary-dark">
                  {metricsLoading ? "..." : metrics?.attackSimulations}
                </p>
                <p className="text-xs text-gray-500 mt-1">2 scheduled today</p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <svg
                  className="w-6 h-6 text-blue-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  />
                </svg>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.2 }}
            className="card-hover p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-black text-sm font-medium">Active Jobs</p>
                <p className="text-2xl font-bold text-yellow-600">
                  {metricsLoading ? "..." : metrics?.activeJobs}
                </p>
                <p className="text-xs text-gray-500 mt-1">3 high priority</p>
              </div>
              <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center">
                <svg
                  className="w-6 h-6 text-yellow-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                  />
                </svg>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Charts and Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="card-hover p-6 lg:col-span-2"
          >
            <h3 className="text-lg font-semibold text-black mb-4">
              Threat Activity
            </h3>
            <div className="h-64">
              {threatActivityLoading ? (
                <div className="h-full flex items-center justify-center">
                  <p className="text-gray-500">Loading chart data...</p>
                </div>
              ) : threatActivity ? (
                <Line
                  data={threatActivity}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        position: "top",
                      },
                      tooltip: {
                        mode: "index",
                        intersect: false,
                      },
                    },
                    scales: {
                      y: {
                        beginAtZero: true,
                        title: {
                          display: true,
                          text: "Number of Threats",
                        },
                      },
                      x: {
                        title: {
                          display: true,
                          text: "Month",
                        },
                      },
                    },
                  }}
                />
              ) : (
                <div className="h-full flex items-center justify-center">
                  <p className="text-gray-500">No data available</p>
                </div>
              )}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="card-hover p-6"
          >
            <h3 className="text-lg font-semibold text-black mb-4">
              Threat Distribution
            </h3>
            <div className="h-64">
              {metricsLoading ? (
                <div className="h-full flex items-center justify-center">
                  <p className="text-gray-500">Loading chart data...</p>
                </div>
              ) : metrics?.threatsByType ? (
                <Pie
                  data={threatDistributionData}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        position: "bottom",
                      },
                    },
                  }}
                />
              ) : (
                <div className="h-full flex items-center justify-center">
                  <p className="text-gray-500">No data available</p>
                </div>
              )}
            </div>
          </motion.div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="card-hover p-6"
          >
            <h3 className="text-lg font-semibold text-black mb-4">
              Threats by Severity
            </h3>
            <div className="h-64">
              {metricsLoading ? (
                <div className="h-full flex items-center justify-center">
                  <p className="text-gray-500">Loading chart data...</p>
                </div>
              ) : metrics?.threatsBySeverity ? (
                <Bar
                  data={severityDistributionData}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        display: false,
                      },
                    },
                    scales: {
                      y: {
                        beginAtZero: true,
                        title: {
                          display: true,
                          text: "Count",
                        },
                      },
                    },
                  }}
                />
              ) : (
                <div className="h-full flex items-center justify-center">
                  <p className="text-gray-500">No data available</p>
                </div>
              )}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="card-hover p-6 lg:col-span-2"
          >
            <h3 className="text-lg font-semibold text-black mb-4">
              Recent Activity
            </h3>
            <div className="space-y-4 max-h-64 overflow-y-auto">
              {recentActivityLoading ? (
                <div className="h-32 flex items-center justify-center">
                  <p className="text-gray-500">Loading activity data...</p>
                </div>
              ) : recentActivity && recentActivity.length > 0 ? (
                recentActivity.map((activity) => (
                  <motion.div
                    key={activity.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.3 }}
                    className="flex items-center justify-between p-3 bg-background-primary rounded-lg hover:bg-background-light transition-colors duration-200"
                  >
                    <div className="flex items-center space-x-3">
                      <div
                        className={`w-3 h-3 rounded-full ${
                          activity.type === "threat"
                            ? activity.severity === ThreatSeverity.CRITICAL
                              ? "bg-error animate-pulse"
                              : activity.severity === ThreatSeverity.HIGH
                                ? "bg-orange-500"
                                : "bg-yellow-500"
                            : activity.type === "simulation"
                              ? "bg-blue-500"
                              : "bg-purple-500"
                        }`}
                      ></div>
                      <span className="text-black">{activity.message}</span>
                    </div>
                    <span className="text-gray-600 text-sm">
                      {formatTimeAgo(activity.timestamp)}
                    </span>
                  </motion.div>
                ))
              ) : (
                <div className="h-32 flex items-center justify-center">
                  <p className="text-gray-500">No recent activity</p>
                </div>
              )}
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
