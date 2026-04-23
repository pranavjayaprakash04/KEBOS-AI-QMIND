import { useState, useEffect } from 'react';
import { Play, CheckCircle, XCircle, AlertTriangle, Trash2, RefreshCw, Upload, Settings } from 'lucide-react';
import toast from 'react-hot-toast';
import { 
  modelManagementService, 
  ModelInfo, 
  formatFileSize, 
  formatDate, 
  formatPercentage 
} from '../services/modelManagementService';

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

interface ModelSettings {
  autoBackup: boolean;
  backupRetentionDays: number;
  performanceMonitoring: boolean;
  alertThreshold: number;
  autoValidation: boolean;
  maxModels: number;
}

export function SettingsPage() {
  const [userProfile, setUserProfile] = useState<UserProfile>({
    name: 'John Doe',
    email: 'john.doe@company.com',
    avatar: '',
    department: 'Security Operations',
    timezone: 'UTC-5',
    language: 'English'
  });
  const [notifications, setNotifications] = useState<NotificationSettings>({
    emailNotifications: true,
    pushNotifications: true,
    threatAlerts: true,
    systemUpdates: false,
    weeklyReports: true,
    criticalAlertsOnly: false
  });
  const [apiSettings, setApiSettings] = useState<APISettings>({
    apiKey: 'sk-1234567890abcdef',
    rateLimit: 1000,
    allowedIPs: ['192.168.1.0/24'],
    webhookUrl: 'https://api.company.com/webhooks',
    enableWebhooks: true
  });
  
  // Model management state
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [activeModel, setActiveModel] = useState<ModelInfo | null>(null);
  const [modelSettings, setModelSettings] = useState<ModelSettings>({
    autoBackup: true,
    backupRetentionDays: 30,
    performanceMonitoring: true,
    alertThreshold: 0.8,
    autoValidation: true,
    maxModels: 10
  });
  const [modelsLoading, setModelsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'profile' | 'notifications' | 'api' | 'models' | 'appearance'>('profile');
  const [isLoading, setIsLoading] = useState(false);

  // Load models on component mount
  useEffect(() => {
    if (activeTab === 'models') {
      fetchModels();
      fetchActiveModel();
    }
  }, [activeTab]);

  // Model management functions
  const fetchModels = async () => {
    setModelsLoading(true);
    try {
      const data = await modelManagementService.fetchModels();
      setModels(data);
    } catch (error) {
      toast.error('Failed to fetch models');
    } finally {
      setModelsLoading(false);
    }
  };

  const fetchActiveModel = async () => {
    try {
      const data = await modelManagementService.fetchActiveModel();
      setActiveModel(data.active_model || null);
    } catch (error) {
      console.error('Failed to fetch active model:', error);
    }
  };

  const handleActivateModel = async (modelId: string) => {
    try {
      await modelManagementService.activateModel(modelId);
      toast.success('Model activated successfully');
      fetchModels();
      fetchActiveModel();
    } catch (error) {
      toast.error('Failed to activate model');
    }
  };

  const handleDeleteModel = async (modelId: string) => {
    if (!confirm('Are you sure you want to delete this model?')) {
      return;
    }

    try {
      await modelManagementService.deleteModel(modelId);
      toast.success('Model deleted successfully');
      fetchModels();
      fetchActiveModel();
    } catch (error) {
      toast.error('Failed to delete model');
    }
  };

  const handleSaveModelSettings = async () => {
    setIsLoading(true);
    try {
      // Simulate API call to save model settings
      await new Promise(resolve => setTimeout(resolve, 1000));
      toast.success('Model settings updated successfully!');
    } catch (error) {
      toast.error('Failed to update model settings');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveProfile = async () => {
    setIsLoading(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    setIsLoading(false);
    // Show success message
    alert('Profile updated successfully!');
  };

  const handleSaveNotifications = async () => {
    setIsLoading(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    setIsLoading(false);
    // Show success message
    alert('Notification settings updated successfully!');
  };

  const handleSaveAPISettings = async () => {
    setIsLoading(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    setIsLoading(false);
    // Show success message
    alert('API settings updated successfully!');
  };

  const handleGenerateNewAPIKey = () => {
    const newKey = 'sk-' + Math.random().toString(36).substring(2, 18);
    setApiSettings({ ...apiSettings, apiKey: newKey });
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Settings</h1>
          <p className="text-gray-600">Manage your account and application preferences</p>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white rounded-lg border border-gray-200 mb-6">
        <div className="flex overflow-x-auto">
          <button
            onClick={() => setActiveTab('profile')}
            className={`px-6 py-3 font-medium whitespace-nowrap rounded-tl-lg ${
              activeTab === 'profile'
                ? 'bg-blue-600 text-white'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Profile
          </button>
          <button
            onClick={() => setActiveTab('notifications')}
            className={`px-6 py-3 font-medium whitespace-nowrap ${
              activeTab === 'notifications'
                ? 'bg-blue-600 text-white'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Notifications
          </button>
          <button
            onClick={() => setActiveTab('api')}
            className={`px-6 py-3 font-medium whitespace-nowrap ${
              activeTab === 'api'
                ? 'bg-blue-600 text-white'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            API Settings
          </button>
          <button
            onClick={() => setActiveTab('models')}
            className={`px-6 py-3 font-medium whitespace-nowrap ${
              activeTab === 'models'
                ? 'bg-blue-600 text-white'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Model Management
          </button>
          <button
            onClick={() => setActiveTab('appearance')}
            className={`px-6 py-3 font-medium whitespace-nowrap rounded-tr-lg ${
              activeTab === 'appearance'
                ? 'bg-blue-600 text-white'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Appearance
          </button>
        </div>
      </div>

      {/* Profile Tab */}
      {activeTab === 'profile' && (
        <div className="bg-white rounded-lg border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">User Profile</h3>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={userProfile.name}
                    onChange={(e) => setUserProfile({ ...userProfile, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">
                    Email Address
                  </label>
                  <input
                    type="email"
                    value={userProfile.email}
                    onChange={(e) => setUserProfile({ ...userProfile, email: e.target.value })}
                    className="w-full px-3 py-2 border border-border rounded-lg bg-background-primary text-text-primary focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-2">
                    Department
                  </label>
                  <select
                    value={userProfile.department}
                    onChange={(e) => setUserProfile({ ...userProfile, department: e.target.value })}
                    className="w-full px-3 py-2 border border-border rounded-lg bg-background-primary text-text-primary focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                  >
                    <option value="Security Operations">Security Operations</option>
                    <option value="Threat Intelligence">Threat Intelligence</option>
                    <option value="Incident Response">Incident Response</option>
                    <option value="Penetration Testing">Penetration Testing</option>
                    <option value="IT Administration">IT Administration</option>
                  </select>
                </div>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-2">
                    Timezone
                  </label>
                  <select
                    value={userProfile.timezone}
                    onChange={(e) => setUserProfile({ ...userProfile, timezone: e.target.value })}
                    className="w-full px-3 py-2 border border-border rounded-lg bg-background-primary text-text-primary focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
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
                  <label className="block text-sm font-medium text-text-primary mb-2">
                    Language
                  </label>
                  <select
                    value={userProfile.language}
                    onChange={(e) => setUserProfile({ ...userProfile, language: e.target.value })}
                    className="w-full px-3 py-2 border border-border rounded-lg bg-background-primary text-text-primary focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
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
                  <label className="block text-sm font-medium text-text-primary mb-2">
                    Profile Avatar
                  </label>
                  <div className="flex items-center space-x-4">
                    <div className="w-16 h-16 bg-primary rounded-full flex items-center justify-center">
                      <span className="text-lg text-white font-medium">
                        {userProfile.name.split(' ').map(n => n[0]).join('')}
                      </span>
                    </div>
                    <button className="bg-secondary hover:bg-secondary-dark text-text-primary px-4 py-2 rounded-lg font-medium border border-border">
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
                className="bg-primary hover:bg-primary-dark text-white px-6 py-2 rounded-lg font-medium disabled:opacity-50"
              >
                {isLoading ? 'Saving...' : 'Save Profile'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Notifications Tab */}
      {activeTab === 'notifications' && (
        <div className="bg-background-secondary rounded-lg border border-border">
          <div className="px-6 py-4 border-b border-border">
            <h3 className="text-lg font-semibold text-text-primary">Notification Preferences</h3>
          </div>
          <div className="p-6">
            <div className="space-y-6">
              <div className="space-y-4">
                <h4 className="text-md font-medium text-text-primary">General Notifications</h4>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-sm font-medium text-text-primary">Email Notifications</label>
                      <p className="text-xs text-text-secondary">Receive notifications via email</p>
                    </div>
                    <button
                      onClick={() => setNotifications({ ...notifications, emailNotifications: !notifications.emailNotifications })}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full ${
                        notifications.emailNotifications ? 'bg-primary' : 'bg-gray-200'
                      }`}
                    >
                      <span
                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                          notifications.emailNotifications ? 'translate-x-6' : 'translate-x-1'
                        }`}
                      />
                    </button>
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-sm font-medium text-text-primary">Push Notifications</label>
                      <p className="text-xs text-text-secondary">Receive browser push notifications</p>
                    </div>
                    <button
                      onClick={() => setNotifications({ ...notifications, pushNotifications: !notifications.pushNotifications })}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full ${
                        notifications.pushNotifications ? 'bg-primary' : 'bg-gray-200'
                      }`}
                    >
                      <span
                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                          notifications.pushNotifications ? 'translate-x-6' : 'translate-x-1'
                        }`}
                      />
                    </button>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <h4 className="text-md font-medium text-text-primary">Security Alerts</h4>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-sm font-medium text-text-primary">Threat Alerts</label>
                      <p className="text-xs text-text-secondary">High priority security threats</p>
                    </div>
                    <button
                      onClick={() => setNotifications({ ...notifications, threatAlerts: !notifications.threatAlerts })}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full ${
                        notifications.threatAlerts ? 'bg-primary' : 'bg-gray-200'
                      }`}
                    >
                      <span
                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                          notifications.threatAlerts ? 'translate-x-6' : 'translate-x-1'
                        }`}
                      />
                    </button>
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-sm font-medium text-text-primary">Critical Alerts Only</label>
                      <p className="text-xs text-text-secondary">Only receive critical security alerts</p>
                    </div>
                    <button
                      onClick={() => setNotifications({ ...notifications, criticalAlertsOnly: !notifications.criticalAlertsOnly })}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full ${
                        notifications.criticalAlertsOnly ? 'bg-primary' : 'bg-gray-200'
                      }`}
                    >
                      <span
                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                          notifications.criticalAlertsOnly ? 'translate-x-6' : 'translate-x-1'
                        }`}
                      />
                    </button>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <h4 className="text-md font-medium text-text-primary">Reports & Updates</h4>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-sm font-medium text-text-primary">System Updates</label>
                      <p className="text-xs text-text-secondary">Platform updates and maintenance</p>
                    </div>
                    <button
                      onClick={() => setNotifications({ ...notifications, systemUpdates: !notifications.systemUpdates })}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full ${
                        notifications.systemUpdates ? 'bg-primary' : 'bg-gray-200'
                      }`}
                    >
                      <span
                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                          notifications.systemUpdates ? 'translate-x-6' : 'translate-x-1'
                        }`}
                      />
                    </button>
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="text-sm font-medium text-text-primary">Weekly Reports</label>
                      <p className="text-xs text-text-secondary">Weekly security summary reports</p>
                    </div>
                    <button
                      onClick={() => setNotifications({ ...notifications, weeklyReports: !notifications.weeklyReports })}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full ${
                        notifications.weeklyReports ? 'bg-primary' : 'bg-gray-200'
                      }`}
                    >
                      <span
                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                          notifications.weeklyReports ? 'translate-x-6' : 'translate-x-1'
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
                className="bg-primary hover:bg-primary-dark text-white px-6 py-2 rounded-lg font-medium disabled:opacity-50"
              >
                {isLoading ? 'Saving...' : 'Save Preferences'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* API Settings Tab */}
      {activeTab === 'api' && (
        <div className="bg-background-secondary rounded-lg border border-border">
          <div className="px-6 py-4 border-b border-border">
            <h3 className="text-lg font-semibold text-text-primary">API Configuration</h3>
          </div>
          <div className="p-6">
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  API Key
                </label>
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={apiSettings.apiKey}
                    readOnly
                    className="flex-1 px-3 py-2 border border-border rounded-lg bg-gray-50 text-text-primary font-mono text-sm"
                  />
                  <button
                    onClick={handleGenerateNewAPIKey}
                    className="bg-warning hover:bg-warning-dark text-text-primary px-4 py-2 rounded-lg font-medium"
                  >
                    Generate New
                  </button>
                </div>
                <p className="text-xs text-text-secondary mt-1">Keep your API key secure and don't share it publicly</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  Rate Limit (requests per hour)
                </label>
                <input
                  type="number"
                  value={apiSettings.rateLimit}
                  onChange={(e) => setApiSettings({ ...apiSettings, rateLimit: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background-primary text-text-primary focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  Webhook URL
                </label>
                <div className="space-y-2">
                  <input
                    type="url"
                    value={apiSettings.webhookUrl}
                    onChange={(e) => setApiSettings({ ...apiSettings, webhookUrl: e.target.value })}
                    className="w-full px-3 py-2 border border-border rounded-lg bg-background-primary text-text-primary focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                    placeholder="https://your-domain.com/webhooks"
                  />
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium text-text-primary">Enable Webhooks</label>
                    <button
                      onClick={() => setApiSettings({ ...apiSettings, enableWebhooks: !apiSettings.enableWebhooks })}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full ${
                        apiSettings.enableWebhooks ? 'bg-primary' : 'bg-gray-200'
                      }`}
                    >
                      <span
                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                          apiSettings.enableWebhooks ? 'translate-x-6' : 'translate-x-1'
                        }`}
                      />
                    </button>
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
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
                          setApiSettings({ ...apiSettings, allowedIPs: newIPs });
                        }}
                        className="flex-1 px-3 py-2 border border-border rounded-lg bg-background-primary text-text-primary font-mono text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                      />
                      <button
                        onClick={() => {
                          const newIPs = apiSettings.allowedIPs.filter((_, i) => i !== index);
                          setApiSettings({ ...apiSettings, allowedIPs: newIPs });
                        }}
                        className="text-error hover:text-error-dark p-2"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  ))}
                  <button
                    onClick={() => setApiSettings({ ...apiSettings, allowedIPs: [...apiSettings.allowedIPs, ''] })}
                    className="text-primary hover:text-primary-dark text-sm font-medium"
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
                className="bg-primary hover:bg-primary-dark text-white px-6 py-2 rounded-lg font-medium disabled:opacity-50"
              >
                {isLoading ? 'Saving...' : 'Save API Settings'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Model Management Tab */}
      {activeTab === 'models' && (
        <div className="space-y-6">
          {/* Active Model Status */}
          <div className="bg-background-secondary rounded-lg border border-border">
            <div className="px-6 py-4 border-b border-border">
              <h3 className="text-lg font-semibold text-text-primary flex items-center">
                <Settings className="w-5 h-5 mr-2" />
                Active Model Status
              </h3>
            </div>
            <div className="p-6">
              {activeModel ? (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-semibold text-green-800">{activeModel.name}</h4>
                      <p className="text-green-600 text-sm">
                        Version {activeModel.version} • {activeModel.model_type}
                      </p>
                      <p className="text-green-600 text-sm">
                        Uploaded: {formatDate(activeModel.uploaded_at)}
                      </p>
                    </div>
                    <CheckCircle className="w-8 h-8 text-green-600" />
                  </div>
                  {activeModel.performance_metrics && (
                    <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
                      {activeModel.performance_metrics.precision && (
                        <div className="text-center">
                          <p className="text-sm text-green-600">Precision</p>
                          <p className="font-semibold text-green-800">
                            {formatPercentage(activeModel.performance_metrics.precision)}
                          </p>
                        </div>
                      )}
                      {activeModel.performance_metrics.recall && (
                        <div className="text-center">
                          <p className="text-sm text-green-600">Recall</p>
                          <p className="font-semibold text-green-800">
                            {formatPercentage(activeModel.performance_metrics.recall)}
                          </p>
                        </div>
                      )}
                      {activeModel.performance_metrics.f1_score && (
                        <div className="text-center">
                          <p className="text-sm text-green-600">F1 Score</p>
                          <p className="font-semibold text-green-800">
                            {formatPercentage(activeModel.performance_metrics.f1_score)}
                          </p>
                        </div>
                      )}
                      {activeModel.performance_metrics.auc_roc && (
                        <div className="text-center">
                          <p className="text-sm text-green-600">AUC ROC</p>
                          <p className="font-semibold text-green-800">
                            {formatPercentage(activeModel.performance_metrics.auc_roc)}
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ) : (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <div className="flex items-center">
                    <AlertTriangle className="w-6 h-6 text-yellow-600 mr-3" />
                    <div>
                      <h4 className="font-semibold text-yellow-800">No Active Model</h4>
                      <p className="text-yellow-600 text-sm">
                        No model is currently active. Upload and activate a model to start threat detection.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Model Settings */}
          <div className="bg-background-secondary rounded-lg border border-border">
            <div className="px-6 py-4 border-b border-border">
              <h3 className="text-lg font-semibold text-text-primary">Model Management Settings</h3>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-2">
                    <input
                      type="checkbox"
                      checked={modelSettings.autoBackup}
                      onChange={(e) => setModelSettings({ ...modelSettings, autoBackup: e.target.checked })}
                      className="mr-2"
                    />
                    Enable Automatic Backups
                  </label>
                  <p className="text-sm text-text-secondary">
                    Automatically create backups before model changes
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-text-primary mb-2">
                    Backup Retention (Days)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="365"
                    value={modelSettings.backupRetentionDays}
                    onChange={(e) => setModelSettings({ ...modelSettings, backupRetentionDays: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-text-primary mb-2">
                    <input
                      type="checkbox"
                      checked={modelSettings.performanceMonitoring}
                      onChange={(e) => setModelSettings({ ...modelSettings, performanceMonitoring: e.target.checked })}
                      className="mr-2"
                    />
                    Performance Monitoring
                  </label>
                  <p className="text-sm text-text-secondary">
                    Monitor model performance and trigger alerts
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-text-primary mb-2">
                    Alert Threshold
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="1"
                    step="0.1"
                    value={modelSettings.alertThreshold}
                    onChange={(e) => setModelSettings({ ...modelSettings, alertThreshold: parseFloat(e.target.value) })}
                    className="w-full px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                  />
                  <p className="text-sm text-text-secondary">
                    Trigger alerts when accuracy drops below this threshold
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-text-primary mb-2">
                    <input
                      type="checkbox"
                      checked={modelSettings.autoValidation}
                      onChange={(e) => setModelSettings({ ...modelSettings, autoValidation: e.target.checked })}
                      className="mr-2"
                    />
                    Auto-validate Uploads
                  </label>
                  <p className="text-sm text-text-secondary">
                    Automatically validate models during upload
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-text-primary mb-2">
                    Maximum Models
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="50"
                    value={modelSettings.maxModels}
                    onChange={(e) => setModelSettings({ ...modelSettings, maxModels: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border border-border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                  />
                  <p className="text-sm text-text-secondary">
                    Maximum number of models to keep in storage
                  </p>
                </div>
              </div>

              <div className="flex justify-end mt-6">
                <button
                  onClick={handleSaveModelSettings}
                  disabled={isLoading}
                  className="bg-primary hover:bg-primary-dark text-white px-6 py-2 rounded-lg font-medium disabled:opacity-50"
                >
                  {isLoading ? 'Saving...' : 'Save Model Settings'}
                </button>
              </div>
            </div>
          </div>

          {/* Available Models */}
          <div className="bg-background-secondary rounded-lg border border-border">
            <div className="px-6 py-4 border-b border-border">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold text-text-primary">Available Models</h3>
                <button
                  onClick={fetchModels}
                  disabled={modelsLoading}
                  className="flex items-center px-3 py-1 text-sm bg-primary hover:bg-primary-dark text-white rounded-lg disabled:opacity-50"
                >
                  <RefreshCw className={`w-4 h-4 mr-1 ${modelsLoading ? 'animate-spin' : ''}`} />
                  Refresh
                </button>
              </div>
            </div>
            <div className="p-6">
              {modelsLoading ? (
                <div className="text-center py-8">
                  <RefreshCw className="w-8 h-8 animate-spin mx-auto text-text-secondary mb-2" />
                  <p className="text-text-secondary">Loading models...</p>
                </div>
              ) : models.length === 0 ? (
                <div className="text-center py-8">
                  <Upload className="w-12 h-12 mx-auto text-text-secondary mb-4" />
                  <p className="text-text-secondary mb-2">No models available</p>
                  <p className="text-sm text-text-secondary">
                    Upload your first model using the Model Management page
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {models.map((model) => (
                    <div key={model.id} className="border border-border rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center">
                            <h4 className="font-semibold text-text-primary">{model.name}</h4>
                            {model.status === 'active' && (
                              <CheckCircle className="w-5 h-5 text-green-600 ml-2" />
                            )}
                            {model.status === 'error' && (
                              <XCircle className="w-5 h-5 text-red-600 ml-2" />
                            )}
                          </div>
                          <p className="text-sm text-text-secondary">
                            Version {model.version} • {model.model_type} • 
                            {formatFileSize(model.file_size)}
                          </p>
                          <p className="text-sm text-text-secondary">
                            Uploaded: {formatDate(model.uploaded_at)}
                          </p>
                          {model.description && (
                            <p className="text-sm text-text-secondary mt-1">{model.description}</p>
                          )}
                        </div>
                        <div className="flex items-center space-x-2">
                          {model.status !== 'active' && (
                            <button
                              onClick={() => handleActivateModel(model.id)}
                              className="flex items-center px-3 py-1 text-sm bg-green-600 hover:bg-green-700 text-white rounded-lg"
                            >
                              <Play className="w-4 h-4 mr-1" />
                              Activate
                            </button>
                          )}
                          <button
                            onClick={() => handleDeleteModel(model.id)}
                            className="flex items-center px-3 py-1 text-sm bg-red-600 hover:bg-red-700 text-white rounded-lg"
                          >
                            <Trash2 className="w-4 h-4 mr-1" />
                            Delete
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Appearance Tab */}
      {activeTab === 'appearance' && (
        <div className="bg-background-secondary rounded-lg border border-border">
          <div className="px-6 py-4 border-b border-border">
            <h3 className="text-lg font-semibold text-text-primary">Appearance Settings</h3>
          </div>
          <div className="p-6">
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-3">
                  Theme Preview
                </label>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 border border-border rounded-lg bg-background-primary">
                    <div className="w-full h-3 bg-primary rounded mb-2"></div>
                    <div className="w-3/4 h-2 bg-text-secondary rounded mb-1"></div>
                    <div className="w-1/2 h-2 bg-text-secondary rounded"></div>
                  </div>
                  <div className="p-4 border border-border rounded-lg bg-background-secondary">
                    <div className="w-full h-3 bg-secondary rounded mb-2"></div>
                    <div className="w-2/3 h-2 bg-text-primary rounded mb-1"></div>
                    <div className="w-3/4 h-2 bg-text-primary rounded"></div>
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  Sidebar Density
                </label>
                <select className="w-full px-3 py-2 border border-border rounded-lg bg-background-primary text-text-primary focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent">
                  <option value="comfortable">Comfortable</option>
                  <option value="compact">Compact</option>
                  <option value="spacious">Spacious</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  Font Size
                </label>
                <select className="w-full px-3 py-2 border border-border rounded-lg bg-background-primary text-text-primary focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent">
                  <option value="small">Small</option>
                  <option value="medium">Medium</option>
                  <option value="large">Large</option>
                </select>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
