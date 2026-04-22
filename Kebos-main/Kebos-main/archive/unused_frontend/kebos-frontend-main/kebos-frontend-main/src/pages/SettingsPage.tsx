import { useState } from "react";

interface UserProfile {
  name: string;
  email: string;
  avatar: string;
  department: string;
  timezone: string;
  language: string;
}

interface NotificationSettings {
  emailNotifications: boolean;
  pushNotifications: boolean;
  threatAlerts: boolean;
  systemUpdates: boolean;
  weeklyReports: boolean;
  criticalAlertsOnly: boolean;
}

interface APISettings {
  apiKey: string;
  rateLimit: number;
  allowedIPs: string[];
  webhookUrl: string;
  enableWebhooks: boolean;
}

export default function SettingsPage() {
  const [userProfile, setUserProfile] = useState<UserProfile>({
    name: "John Doe",
    email: "john.doe@company.com",
    avatar: "",
    department: "Security Operations",
    timezone: "UTC-5",
    language: "English",
  });
  const [notifications, setNotifications] = useState<NotificationSettings>({
    emailNotifications: true,
    pushNotifications: true,
    threatAlerts: true,
    systemUpdates: false,
    weeklyReports: true,
    criticalAlertsOnly: false,
  });
  const [apiSettings, setApiSettings] = useState<APISettings>({
    apiKey: "sk-1234567890abcdef",
    rateLimit: 1000,
    allowedIPs: ["192.168.1.0/24"],
    webhookUrl: "https://api.company.com/webhooks",
    enableWebhooks: true,
  });
  const [activeTab, setActiveTab] = useState<
    "profile" | "notifications" | "api" | "appearance"
  >("profile");
  const [isLoading, setIsLoading] = useState(false);

  const handleSaveProfile = async () => {
    setIsLoading(true);
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setIsLoading(false);
    // Show success message
    alert("Profile updated successfully!");
  };

  const handleSaveNotifications = async () => {
    setIsLoading(true);
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setIsLoading(false);
    // Show success message
    alert("Notification settings updated successfully!");
  };

  const handleSaveAPISettings = async () => {
    setIsLoading(true);
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setIsLoading(false);
    // Show success message
    alert("API settings updated successfully!");
  };

  const handleGenerateNewAPIKey = () => {
    const newKey = "sk-" + Math.random().toString(36).substring(2, 18);
    setApiSettings({ ...apiSettings, apiKey: newKey });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm border-b border-slate-200/50 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent mb-2">
              Settings
            </h1>
            <p className="text-slate-600">
              Manage your account and application preferences
            </p>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Tab Navigation */}
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50">
          <div className="flex overflow-x-auto rounded-t-2xl">
            <button
              onClick={() => setActiveTab("profile")}
              className={`px-6 py-3 font-medium whitespace-nowrap rounded-tl-2xl transition-colors ${
                activeTab === "profile"
                  ? "bg-indigo-600 text-white"
                  : "text-slate-600 hover:text-indigo-600 hover:bg-slate-50"
              }`}
            >
              Profile
            </button>
            <button
              onClick={() => setActiveTab("notifications")}
              className={`px-6 py-3 font-medium whitespace-nowrap transition-colors ${
                activeTab === "notifications"
                  ? "bg-indigo-600 text-white"
                  : "text-slate-600 hover:text-indigo-600 hover:bg-slate-50"
              }`}
            >
              Notifications
            </button>
            <button
              onClick={() => setActiveTab("api")}
              className={`px-6 py-3 font-medium whitespace-nowrap transition-colors ${
                activeTab === "api"
                  ? "bg-indigo-600 text-white"
                  : "text-slate-600 hover:text-indigo-600 hover:bg-slate-50"
              }`}
            >
              API Settings
            </button>
            <button
              onClick={() => setActiveTab("appearance")}
              className={`px-6 py-3 font-medium whitespace-nowrap rounded-tr-2xl transition-colors ${
                activeTab === "appearance"
                  ? "bg-indigo-600 text-white"
                  : "text-slate-600 hover:text-indigo-600 hover:bg-slate-50"
              }`}
            >
              Appearance
            </button>
          </div>
        </div>

        {/* Profile Tab */}
        {activeTab === "profile" && (
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50">
            <div className="px-6 py-4 border-b border-slate-200">
              <h3 className="text-lg font-semibold text-slate-800">
                User Profile
              </h3>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      Full Name
                    </label>
                    <input
                      type="text"
                      value={userProfile.name}
                      onChange={(e) =>
                        setUserProfile({ ...userProfile, name: e.target.value })
                      }
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-shadow"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      Email Address
                    </label>
                    <input
                      type="email"
                      value={userProfile.email}
                      onChange={(e) =>
                        setUserProfile({
                          ...userProfile,
                          email: e.target.value,
                        })
                      }
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-shadow"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      Department
                    </label>
                    <select
                      value={userProfile.department}
                      onChange={(e) =>
                        setUserProfile({
                          ...userProfile,
                          department: e.target.value,
                        })
                      }
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-shadow"
                    >
                      <option value="Security Operations">
                        Security Operations
                      </option>
                      <option value="Threat Intelligence">
                        Threat Intelligence
                      </option>
                      <option value="Incident Response">
                        Incident Response
                      </option>
                      <option value="Penetration Testing">
                        Penetration Testing
                      </option>
                      <option value="IT Administration">
                        IT Administration
                      </option>
                    </select>
                  </div>
                </div>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      Timezone
                    </label>
                    <select
                      value={userProfile.timezone}
                      onChange={(e) =>
                        setUserProfile({
                          ...userProfile,
                          timezone: e.target.value,
                        })
                      }
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-shadow"
                    >
                      <option value="UTC-8">UTC-8 (Pacific)</option>
                      <option value="UTC-7">UTC-7 (Mountain)</option>
                      <option value="UTC-6">UTC-6 (Central)</option>
                      <option value="UTC-5">UTC-5 (Eastern)</option>
                      <option value="UTC+0">UTC+0 (GMT)</option>
                      <option value="UTC+1">UTC+1 (CET)</option>
                      <option value="UTC+8">UTC+8 (CST)</option>
                      <option value="UTC+9">UTC+9 (JST)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      Language
                    </label>
                    <select
                      value={userProfile.language}
                      onChange={(e) =>
                        setUserProfile({
                          ...userProfile,
                          language: e.target.value,
                        })
                      }
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-shadow"
                    >
                      <option value="English">English</option>
                      <option value="Spanish">Spanish</option>
                      <option value="French">French</option>
                      <option value="German">German</option>
                      <option value="Japanese">Japanese</option>
                      <option value="Chinese">Chinese</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      Profile Avatar
                    </label>
                    <div className="flex items-center space-x-4">
                      <div className="w-16 h-16 bg-indigo-600 rounded-full flex items-center justify-center">
                        <span className="text-lg text-white font-medium">
                          {userProfile.name
                            .split(" ")
                            .map((n) => n[0])
                            .join("")}
                        </span>
                      </div>
                      <button className="bg-slate-100 hover:bg-slate-200 text-slate-700 px-4 py-2 rounded-lg font-medium border border-slate-300 transition-colors">
                        Upload New Avatar
                      </button>
                    </div>
                  </div>
                </div>
              </div>
              <div className="flex justify-end mt-6">
                <button
                  onClick={handleSaveProfile}
                  disabled={isLoading}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded-lg font-medium disabled:opacity-50 transition-colors"
                >
                  {isLoading ? "Saving..." : "Save Profile"}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Notifications Tab */}
        {activeTab === "notifications" && (
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50">
            <div className="px-6 py-4 border-b border-slate-200">
              <h3 className="text-lg font-semibold text-slate-800">
                Notification Preferences
              </h3>
            </div>
            <div className="p-6">
              <div className="space-y-6">
                <div className="space-y-4">
                  <h4 className="text-md font-medium text-slate-700">
                    General Notifications
                  </h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="text-sm font-medium text-slate-700">
                          Email Notifications
                        </label>
                        <p className="text-xs text-slate-500">
                          Receive notifications via email
                        </p>
                      </div>
                      <button
                        onClick={() =>
                          setNotifications({
                            ...notifications,
                            emailNotifications:
                              !notifications.emailNotifications,
                          })
                        }
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                          notifications.emailNotifications
                            ? "bg-indigo-600"
                            : "bg-gray-200"
                        }`}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            notifications.emailNotifications
                              ? "translate-x-6"
                              : "translate-x-1"
                          }`}
                        />
                      </button>
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="text-sm font-medium text-slate-700">
                          Push Notifications
                        </label>
                        <p className="text-xs text-slate-500">
                          Receive browser push notifications
                        </p>
                      </div>
                      <button
                        onClick={() =>
                          setNotifications({
                            ...notifications,
                            pushNotifications: !notifications.pushNotifications,
                          })
                        }
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                          notifications.pushNotifications
                            ? "bg-indigo-600"
                            : "bg-gray-200"
                        }`}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            notifications.pushNotifications
                              ? "translate-x-6"
                              : "translate-x-1"
                          }`}
                        />
                      </button>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <h4 className="text-md font-medium text-slate-700">
                    Security Alerts
                  </h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="text-sm font-medium text-slate-700">
                          Threat Alerts
                        </label>
                        <p className="text-xs text-slate-500">
                          High priority security threats
                        </p>
                      </div>
                      <button
                        onClick={() =>
                          setNotifications({
                            ...notifications,
                            threatAlerts: !notifications.threatAlerts,
                          })
                        }
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                          notifications.threatAlerts
                            ? "bg-indigo-600"
                            : "bg-gray-200"
                        }`}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            notifications.threatAlerts
                              ? "translate-x-6"
                              : "translate-x-1"
                          }`}
                        />
                      </button>
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="text-sm font-medium text-slate-700">
                          Critical Alerts Only
                        </label>
                        <p className="text-xs text-slate-500">
                          Only receive critical security alerts
                        </p>
                      </div>
                      <button
                        onClick={() =>
                          setNotifications({
                            ...notifications,
                            criticalAlertsOnly:
                              !notifications.criticalAlertsOnly,
                          })
                        }
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                          notifications.criticalAlertsOnly
                            ? "bg-indigo-600"
                            : "bg-gray-200"
                        }`}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            notifications.criticalAlertsOnly
                              ? "translate-x-6"
                              : "translate-x-1"
                          }`}
                        />
                      </button>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <h4 className="text-md font-medium text-slate-700">
                    Reports & Updates
                  </h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="text-sm font-medium text-slate-700">
                          System Updates
                        </label>
                        <p className="text-xs text-slate-500">
                          Platform updates and maintenance
                        </p>
                      </div>
                      <button
                        onClick={() =>
                          setNotifications({
                            ...notifications,
                            systemUpdates: !notifications.systemUpdates,
                          })
                        }
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                          notifications.systemUpdates
                            ? "bg-indigo-600"
                            : "bg-gray-200"
                        }`}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            notifications.systemUpdates
                              ? "translate-x-6"
                              : "translate-x-1"
                          }`}
                        />
                      </button>
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="text-sm font-medium text-slate-700">
                          Weekly Reports
                        </label>
                        <p className="text-xs text-slate-500">
                          Weekly security summary reports
                        </p>
                      </div>
                      <button
                        onClick={() =>
                          setNotifications({
                            ...notifications,
                            weeklyReports: !notifications.weeklyReports,
                          })
                        }
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                          notifications.weeklyReports
                            ? "bg-indigo-600"
                            : "bg-gray-200"
                        }`}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            notifications.weeklyReports
                              ? "translate-x-6"
                              : "translate-x-1"
                          }`}
                        />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
              <div className="flex justify-end mt-6">
                <button
                  onClick={handleSaveNotifications}
                  disabled={isLoading}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded-lg font-medium disabled:opacity-50 transition-colors"
                >
                  {isLoading ? "Saving..." : "Save Preferences"}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* API Settings Tab */}
        {activeTab === "api" && (
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50">
            <div className="px-6 py-4 border-b border-slate-200">
              <h3 className="text-lg font-semibold text-slate-800">
                API Configuration
              </h3>
            </div>
            <div className="p-6">
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    API Key
                  </label>
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      value={apiSettings.apiKey}
                      readOnly
                      className="flex-1 px-3 py-2 border border-slate-300 rounded-lg bg-gray-50 text-slate-700 font-mono text-sm"
                    />
                    <button
                      onClick={handleGenerateNewAPIKey}
                      className="bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                    >
                      Generate New
                    </button>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">
                    Keep your API key secure and don't share it publicly
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Rate Limit (requests per hour)
                  </label>
                  <input
                    type="number"
                    value={apiSettings.rateLimit}
                    onChange={(e) =>
                      setApiSettings({
                        ...apiSettings,
                        rateLimit: parseInt(e.target.value),
                      })
                    }
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-shadow"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Webhook URL
                  </label>
                  <div className="space-y-2">
                    <input
                      type="url"
                      value={apiSettings.webhookUrl}
                      onChange={(e) =>
                        setApiSettings({
                          ...apiSettings,
                          webhookUrl: e.target.value,
                        })
                      }
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-shadow"
                      placeholder="https://your-domain.com/webhooks"
                    />
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-medium text-slate-700">
                        Enable Webhooks
                      </label>
                      <button
                        onClick={() =>
                          setApiSettings({
                            ...apiSettings,
                            enableWebhooks: !apiSettings.enableWebhooks,
                          })
                        }
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                          apiSettings.enableWebhooks
                            ? "bg-indigo-600"
                            : "bg-gray-200"
                        }`}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            apiSettings.enableWebhooks
                              ? "translate-x-6"
                              : "translate-x-1"
                          }`}
                        />
                      </button>
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Allowed IP Addresses
                  </label>
                  <div className="space-y-2">
                    {apiSettings.allowedIPs.map((ip, index) => (
                      <div key={index} className="flex items-center space-x-2">
                        <input
                          type="text"
                          value={ip}
                          onChange={(e) => {
                            const newIPs = [...apiSettings.allowedIPs];
                            newIPs[index] = e.target.value;
                            setApiSettings({
                              ...apiSettings,
                              allowedIPs: newIPs,
                            });
                          }}
                          className="flex-1 px-3 py-2 border border-slate-300 rounded-lg bg-white text-slate-900 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-shadow"
                        />
                        <button
                          onClick={() => {
                            const newIPs = apiSettings.allowedIPs.filter(
                              (_, i) => i !== index
                            );
                            setApiSettings({
                              ...apiSettings,
                              allowedIPs: newIPs,
                            });
                          }}
                          className="text-red-500 hover:text-red-700 p-2 transition-colors"
                        >
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
                              d="M6 18L18 6M6 6l12 12"
                            />
                          </svg>
                        </button>
                      </div>
                    ))}
                    <button
                      onClick={() =>
                        setApiSettings({
                          ...apiSettings,
                          allowedIPs: [...apiSettings.allowedIPs, ""],
                        })
                      }
                      className="text-indigo-600 hover:text-indigo-700 text-sm font-medium transition-colors"
                    >
                      + Add IP Address
                    </button>
                  </div>
                </div>
              </div>
              <div className="flex justify-end mt-6">
                <button
                  onClick={handleSaveAPISettings}
                  disabled={isLoading}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded-lg font-medium disabled:opacity-50 transition-colors"
                >
                  {isLoading ? "Saving..." : "Save API Settings"}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Appearance Tab */}
        {activeTab === "appearance" && (
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50">
            <div className="px-6 py-4 border-b border-slate-200">
              <h3 className="text-lg font-semibold text-slate-800">
                Appearance Settings
              </h3>
            </div>
            <div className="p-6">
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-3">
                    Theme Preview
                  </label>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 border border-slate-300 rounded-lg bg-white">
                      <div className="w-full h-3 bg-indigo-600 rounded mb-2"></div>
                      <div className="w-3/4 h-2 bg-slate-300 rounded mb-1"></div>
                      <div className="w-1/2 h-2 bg-slate-300 rounded"></div>
                    </div>
                    <div className="p-4 border border-slate-300 rounded-lg bg-slate-100">
                      <div className="w-full h-3 bg-slate-400 rounded mb-2"></div>
                      <div className="w-2/3 h-2 bg-slate-700 rounded mb-1"></div>
                      <div className="w-3/4 h-2 bg-slate-700 rounded"></div>
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Sidebar Density
                  </label>
                  <select className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-shadow">
                    <option value="comfortable">Comfortable</option>
                    <option value="compact">Compact</option>
                    <option value="spacious">Spacious</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Font Size
                  </label>
                  <select className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-shadow">
                    <option value="small">Small</option>
                    <option value="medium">Medium</option>
                    <option value="large">Large</option>
                  </select>
                </div>

                <div className="flex justify-end mt-6">
                  <button className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded-lg font-medium transition-colors">
                    Save Appearance
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
