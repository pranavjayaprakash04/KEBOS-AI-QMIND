import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation, Navigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Cases from './pages/Cases';
import Reports from './pages/Reports';
import Settings from './pages/Settings';
import Login from './pages/Login';
import DeceptionLayer from './pages/DeceptionLayer';
import { useBackendHealth } from './hooks/useBackendHealth';
import { ServiceUnavailableBanner } from './components/ServiceUnavailableBanner';
import { LoadingSpinner } from './components/LoadingSpinner';
import { useAuthStore } from './store/authStore';

const NavItem: React.FC<{ to: string; label: string; current: boolean }> = ({ to, label, current }) => (
  <Link
    to={to}
    className={`px-4 py-2 rounded font-medium transition-colors ${
      current ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
    }`}
  >
    {label}
  </Link>
);

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuthStore();
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
};

const App: React.FC = () => {
  const backendStatus = useBackendHealth();
  const { isAuthenticated, logout } = useAuthStore();

  if (backendStatus === 'checking') return <LoadingSpinner />;
  if (backendStatus === 'unhealthy') return <ServiceUnavailableBanner />;

  return (
    <Router>
      <div className="min-h-screen bg-gray-100">
        {isAuthenticated && (
          <nav className="bg-white shadow-sm border-b border-gray-200">
            <div className="max-w-7xl mx-auto px-4 py-3">
              <div className="flex gap-2 items-center">
                <NavLink to="/dashboard" label="Dashboard" />
                <NavLink to="/deception" label="Deception Layer" />
                <NavLink to="/cases" label="Cases" />
                <NavLink to="/reports" label="Reports" />
                <NavLink to="/settings" label="Settings" />
                <button
                  onClick={logout}
                  className="ml-auto px-4 py-2 bg-red-100 text-red-700 rounded font-medium hover:bg-red-200 transition-colors"
                >
                  Logout
                </button>
              </div>
            </div>
          </nav>
        )}
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />
          <Route path="/deception" element={
            <ProtectedRoute>
              <DeceptionLayer />
            </ProtectedRoute>
          } />
          <Route path="/cases" element={
            <ProtectedRoute>
              <Cases />
            </ProtectedRoute>
          } />
          <Route path="/reports" element={
            <ProtectedRoute>
              <Reports />
            </ProtectedRoute>
          } />
          <Route path="/settings" element={
            <ProtectedRoute>
              <Settings />
            </ProtectedRoute>
          } />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </div>
    </Router>
  );
};

const NavLink: React.FC<{ to: string; label: string }> = ({ to, label }) => {
  const location = useLocation();
  const current = location.pathname === to;
  return <NavItem to={to} label={label} current={current} />;
};

export default App;
