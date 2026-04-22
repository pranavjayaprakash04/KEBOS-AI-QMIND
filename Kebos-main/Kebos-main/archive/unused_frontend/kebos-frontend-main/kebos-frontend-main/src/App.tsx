import { Routes, Route } from 'react-router-dom';
import { Layout } from '@/components/common/Layout';

// Import actual page components
import { DashboardPage } from '@/pages/DashboardPage';
import { LoginPage } from '@/pages/LoginPage';
import { CampaignsPage } from '@/pages/attacksim/CampaignsPage';
import { AttackSimDashboard } from '@/pages/attacksim/AttackSimDashboard';
import { ThreatDetectionPage } from '@/pages/ThreatDetectionPage';
import { AssistantPage } from '@/pages/AssistantPage';
import { AuditPage } from '@/pages/AuditPage';
import { JobManagerPage } from '@/pages/JobManagerPage';
import { AdminDashboardPage } from '@/pages/AdminDashboardPage';
import SettingsPage from './pages/SettingsPage';
import { NetworkAnalyticsPage } from '@/pages/NetworkAnalyticsPage';
import { SecureMessagingPage } from '@/pages/SecureMessagingPage';
import AttackSimulationPage from '@/pages/AttackSimulationPage';

// Temporary placeholder pages for components not yet created

function ScenariosPage() {
  return <div className="p-6"><h1 className="text-2xl font-bold">Scenarios</h1></div>;
}

function IntelligencePage() {
  return <div className="p-6"><h1 className="text-2xl font-bold">Intelligence</h1></div>;
}

function PromptShieldPage() {
  return <div className="p-6"><h1 className="text-2xl font-bold">PromptShield</h1></div>;
}

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
                  <Route path="/attacksim" element={<AttackSimDashboard />} />
                  <Route path="/attacksim/campaigns" element={<CampaignsPage />} />
                  <Route path="/attacksim/scenarios" element={<ScenariosPage />} />
                  <Route path="/attacksim/intelligence" element={<IntelligencePage />} />
                  <Route path="/attack-simulation" element={<AttackSimulationPage />} />
                  <Route path="/threat-detection" element={<ThreatDetectionPage />} />
                  <Route path="/promptshield" element={<PromptShieldPage />} />
                  <Route path="/assistant" element={<AssistantPage />} />
                  <Route path="/audit" element={<AuditPage />} />
                  <Route path="/network-analytics" element={<NetworkAnalyticsPage />} />
                  <Route path="/job-manager" element={<JobManagerPage />} />
                  <Route path="/admin" element={<AdminDashboardPage />} />
                  <Route path="/reports" element={<ReportsPage />} />
                  <Route path="/settings" element={<SettingsPage />} />
                  <Route path="/secure-messaging" element={<SecureMessagingPage />} />
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
