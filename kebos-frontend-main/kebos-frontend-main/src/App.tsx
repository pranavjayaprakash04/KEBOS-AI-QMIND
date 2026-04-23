import { Routes, Route } from 'react-router-dom';
import { Layout } from '@/components/common/Layout';

// Import actual page components
import { DashboardPage } from '@/pages/DashboardPage';
import { LoginPage } from '@/pages/LoginPage';
import { ThreatDetectionPage } from '@/pages/ThreatDetectionPage';
import { AssistantPage } from '@/pages/AssistantPage';
import { AuditPage } from '@/pages/AuditPage';
import { JobManagerPage } from '@/pages/JobManagerPage';
import { AdminDashboardPage } from '@/pages/AdminDashboardPage';
import { SettingsPage } from '@/pages/SettingsPage';
import { NetworkAnalyticsPage } from '@/pages/NetworkAnalyticsPage';
import { SecureMessagingPage } from '@/pages/SecureMessagingPage';
import ModelManagementPage from '@/pages/ModelManagementPage';
import SIEMIntegrationPage from '@/pages/SIEMIntegrationPage';

// Temporary placeholder pages for components not yet created

function ReportsPage() {
  return <div className="p-6"><h1 className="text-2xl font-bold">Reports</h1></div>;
}

// Protected Route component
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  // This will be implemented to check authentication
  return <>{children}</>;
}

function App() {
  return (
    <div className="app">
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        
        {/* Protected routes */}
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <Layout>
                <Routes>
                  <Route path="/" element={<DashboardPage />} />
                  <Route path="/threat-detection" element={<ThreatDetectionPage />} />
                  <Route path="/assistant" element={<AssistantPage />} />
                  <Route path="/audit" element={<AuditPage />} />
                  <Route path="/network-analytics" element={<NetworkAnalyticsPage />} />
                  <Route path="/job-manager" element={<JobManagerPage />} />
                  <Route path="/siem-integration" element={<SIEMIntegrationPage />} />
                  <Route path="/admin" element={<AdminDashboardPage />} />
                  <Route path="/reports" element={<ReportsPage />} />
                  <Route path="/settings" element={<SettingsPage />} />
                  <Route path="/secure-messaging" element={<SecureMessagingPage />} />
                  <Route path="/model-management" element={<ModelManagementPage />} />
                </Routes>
              </Layout>
            </ProtectedRoute>
          }
        />
      </Routes>
    </div>
  );
}

export default App;
