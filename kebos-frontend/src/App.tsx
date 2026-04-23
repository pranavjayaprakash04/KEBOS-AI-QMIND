import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Cases from './pages/Cases';
import Reports from './pages/Reports';
import Settings from './pages/Settings';

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

const App: React.FC = () => {
  return (
    <Router>
      <div className="min-h-screen bg-gray-100">
        <nav className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 py-3">
            <div className="flex gap-2">
              <NavLink to="/" label="Dashboard" />
              <NavLink to="/cases" label="Cases" />
              <NavLink to="/reports" label="Reports" />
              <NavLink to="/settings" label="Settings" />
            </div>
          </div>
        </nav>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/cases" element={<Cases />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/settings" element={<Settings />} />
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
