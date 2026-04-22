import { useState, useEffect } from "react";

interface Campaign {
  id: string;
  name: string;
  status: "draft" | "running" | "completed" | "paused";
  type: string;
  targets: number;
  successRate: number;
  startDate: string;
  endDate?: string;
}

export function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setCampaigns([
        {
          id: "1",
          name: "Phishing Awareness Training",
          status: "running",
          type: "Phishing",
          targets: 250,
          successRate: 23,
          startDate: "2024-01-15",
        },
        {
          id: "2",
          name: "Social Engineering Test",
          status: "completed",
          type: "Social Engineering",
          targets: 100,
          successRate: 45,
          startDate: "2024-01-10",
          endDate: "2024-01-14",
        },
        {
          id: "3",
          name: "Malware Detection Drill",
          status: "draft",
          type: "Malware",
          targets: 150,
          successRate: 0,
          startDate: "2024-01-20",
        },
        {
          id: "4",
          name: "USB Baiting Campaign",
          status: "paused",
          type: "Physical",
          targets: 75,
          successRate: 67,
          startDate: "2024-01-05",
        },
      ]);
      setIsLoading(false);
    });
  }, []);

  const getStatusColor = (status: Campaign["status"]) => {
    switch (status) {
      case "running":
        return "bg-gradient-to-r from-emerald-500 to-green-600 text-white shadow-lg shadow-emerald-200";
      case "completed":
        return "bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-200";
      case "paused":
        return "bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-lg shadow-amber-200";
      case "draft":
        return "bg-gradient-to-r from-slate-500 to-slate-600 text-white shadow-lg shadow-slate-200";
      default:
        return "bg-gradient-to-r from-slate-500 to-slate-600 text-white shadow-lg shadow-slate-200";
    }
  };

  const getStatusIcon = (status: Campaign["status"]) => {
    switch (status) {
      case "running":
        return (
          <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
        );
      case "completed":
        return <div className="w-2 h-2 bg-white rounded-full"></div>;
      case "paused":
        return (
          <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
        );
      case "draft":
        return <div className="w-2 h-2 bg-white rounded-full"></div>;
      default:
        return <div className="w-2 h-2 bg-white rounded-full"></div>;
    }
  };

  const getCampaignInitials = (name: string) => {
    return name
      .split(" ")
      .map((word) => word.charAt(0))
      .slice(0, 2)
      .join("")
      .toUpperCase();
  };

  const getCampaignAvatarColor = (id: string) => {
    const colors = [
      "from-blue-500 to-purple-600",
      "from-purple-500 to-pink-600",
      "from-green-500 to-emerald-600",
      "from-orange-500 to-red-500",
      "from-cyan-500 to-blue-500",
    ];
    return colors[parseInt(id) % colors.length];
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
        <div className="flex items-center justify-center h-64">
          <div className="relative">
            <div className="animate-spin rounded-full h-16 w-16 border-4 border-slate-200"></div>
            <div className="animate-spin rounded-full h-16 w-16 border-4 border-indigo-500 border-t-transparent absolute top-0 left-0"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header Section */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 bg-white rounded-2xl p-6 shadow-lg border border-slate-200">
          <div>
            <h1 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-2 bg-gradient-to-r from-blue-500 to-blue-800 bg-clip-text text-transparent">
              Attack Simulation Campaigns
            </h1>
            <p className="text-amber-600 font-medium text-lg">
              Manage and monitor your security awareness campaigns
            </p>
          </div>
          <button className="mt-4 sm:mt-0 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white px-6 py-3 rounded-xl font-semibold transform hover:scale-105 transition-all duration-200 shadow-lg hover:shadow-indigo-200">
            Create Campaign
          </button>
        </div>

        {/* Campaign Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-2xl p-6 shadow-lg border border-slate-200 hover:shadow-xl transition-all duration-300 group flex items-center justify-center">
            <div className="text-center">
              <div className="w-12 h-12 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center text-white font-bold mx-auto mb-3 group-hover:scale-110 transition-transform duration-200">
                {campaigns.length}
              </div>

              <p className="text-slate-600 text-sm font-medium">
                Total Campaigns
              </p>
            </div>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-lg border border-slate-200 hover:shadow-xl transition-all duration-300 group flex items-center justify-center">
            <div className="text-center">
              <div className="w-12 h-12 bg-gradient-to-r from-emerald-500 to-green-600 rounded-xl flex items-center justify-center text-white font-bold mx-auto mb-3 group-hover:scale-110 transition-transform duration-200">
                {campaigns.filter((c) => c.status === "running").length}
              </div>

              <p className="text-slate-600 text-sm font-medium">
                Active Campaigns
              </p>
            </div>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-lg border border-slate-200 hover:shadow-xl transition-all duration-300 group flex items-center justify-center">
            <div className="text-center">
              <div className="w-12 h-12 bg-gradient-to-r from-amber-500 to-orange-500 rounded-xl flex items-center justify-center text-white font-bold mx-auto mb-3 group-hover:scale-110 transition-transform duration-200">
                {campaigns
                  .reduce((acc, c) => acc + c.targets, 0)
                  .toLocaleString()}
                K
              </div>

              <p className="text-slate-600 text-sm font-medium">
                Total Targets
              </p>
            </div>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-lg border border-slate-200 hover:shadow-xl transition-all duration-300 group">
            <div className="text-center">
              <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-emerald-600 rounded-xl flex items-center justify-center text-white font-bold mx-auto mb-3 group-hover:scale-110 transition-transform duration-200">
                {Math.round(
                  campaigns.reduce((acc, c) => acc + c.successRate, 0) /
                    campaigns.length
                )}
                %
              </div>
             
              <p className="text-slate-600 text-sm font-medium">
                Avg Success Rate
              </p>
            </div>
          </div>
        </div>

        {/* Campaigns Table */}
        <div className="bg-white rounded-2xl shadow-lg border border-slate-200 overflow-hidden">
          <div className="px-6 py-4 bg-gradient-to-r from-slate-50 to-slate-100 border-b border-slate-200">
            <h3 className="text-xl font-bold text-slate-900">
              Security Campaigns
            </h3>
            <p className="text-slate-600 text-sm mt-1">
              Monitor your attack simulation progress
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gradient-to-r from-slate-50 to-slate-100 border-b-2 border-slate-200">
                <tr>
                  <th className="px-6 py-5 text-left text-xs font-semibold text-slate-700 uppercase tracking-wider">
                    Campaign
                  </th>
                  <th className="px-6 py-5 text-left text-xs font-semibold text-slate-700 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-5 text-left text-xs font-semibold text-slate-700 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-5 text-left text-xs font-semibold text-slate-700 uppercase tracking-wider">
                    Targets
                  </th>
                  <th className="px-6 py-5 text-left text-xs font-semibold text-slate-700 uppercase tracking-wider">
                    Success Rate
                  </th>
                  <th className="px-6 py-5 text-left text-xs font-semibold text-slate-700 uppercase tracking-wider">
                    Start Date
                  </th>
                  <th className="px-6 py-5 text-right text-xs font-semibold text-slate-700 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {campaigns.map((campaign, index) => (
                  <tr
                    key={campaign.id}
                    className="group hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 transition-all duration-300 hover:shadow-lg hover:shadow-blue-100/50"
                    style={{ animationDelay: `${index * 100}ms` }}
                  >
                    <td className="px-6 py-6 whitespace-nowrap">
                      <div className="flex items-center space-x-4">
                        <div
                          className={`w-12 h-12 bg-gradient-to-br ${getCampaignAvatarColor(campaign.id)} rounded-xl flex items-center justify-center text-white font-bold shadow-lg group-hover:scale-110 transition-transform duration-200`}
                        >
                          {getCampaignInitials(campaign.name)}
                        </div>
                        <div>
                          <div className="text-sm font-semibold text-slate-900 group-hover:text-indigo-700 transition-colors">
                            {campaign.name}
                          </div>
                          <div className="text-sm text-slate-500 font-mono">
                            ID: #{campaign.id}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-6 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center space-x-2 px-3 py-2 rounded-full text-xs font-semibold ${getStatusColor(campaign.status)} group-hover:scale-105 transition-transform duration-200`}
                      >
                        {getStatusIcon(campaign.status)}
                        <span className="capitalize">{campaign.status}</span>
                      </span>
                    </td>
                    <td className="px-6 py-6 whitespace-nowrap">
                      <span className="text-sm font-medium text-slate-700 bg-slate-100 px-3 py-1 rounded-lg group-hover:bg-slate-200 transition-colors">
                        {campaign.type}
                      </span>
                    </td>
                    <td className="px-6 py-6 whitespace-nowrap">
                      <span className="text-sm font-semibold text-slate-900">
                        {campaign.targets.toLocaleString()}
                      </span>
                    </td>
                    <td className="px-6 py-6 whitespace-nowrap">
                      <div className="flex items-center space-x-3">
                        <div className="flex-1 bg-slate-200 rounded-full h-2 overflow-hidden max-w-20">
                          <div
                            className={`h-2 rounded-full transition-all duration-500 ${
                              campaign.successRate >= 70
                                ? "bg-gradient-to-r from-green-500 to-emerald-600"
                                : campaign.successRate >= 40
                                  ? "bg-gradient-to-r from-amber-500 to-orange-500"
                                  : campaign.successRate > 0
                                    ? "bg-gradient-to-r from-red-500 to-red-600"
                                    : "bg-gradient-to-r from-slate-400 to-slate-500"
                            }`}
                            style={{ width: `${campaign.successRate}%` }}
                          ></div>
                        </div>
                        <span className="text-sm font-semibold text-slate-700 min-w-12">
                          {campaign.successRate}%
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-6 whitespace-nowrap text-sm text-slate-500">
                      {new Date(campaign.startDate).toLocaleDateString(
                        "en-US",
                        {
                          year: "numeric",
                          month: "short",
                          day: "numeric",
                        }
                      )}
                    </td>
                    <td className="px-6 py-6 whitespace-nowrap text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <button className="px-4 py-2 bg-gradient-to-r from-blue-500 to-blue-600 text-white text-xs font-medium rounded-lg hover:from-blue-600 hover:to-blue-700 transform hover:scale-105 transition-all duration-200 shadow-lg hover:shadow-blue-200">
                          View
                        </button>
                        <button className="px-4 py-2 bg-gradient-to-r from-amber-500 to-orange-500 text-white text-xs font-medium rounded-lg hover:from-amber-600 hover:to-orange-600 transform hover:scale-105 transition-all duration-200 shadow-lg hover:shadow-amber-200">
                          Edit
                        </button>
                        <button className="px-4 py-2 bg-gradient-to-r from-red-500 to-red-600 text-white text-xs font-medium rounded-lg hover:from-red-600 hover:to-red-700 transform hover:scale-105 transition-all duration-200 shadow-lg hover:shadow-red-200">
                          Delete
                        </button>
                      </div>
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

export default CampaignsPage;
