
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';

export function Header() {
  const { user, logout } = useAuth();
  const { toggleSidebar } = useTheme();

  return (
    <header className="fixed top-0 left-0 right-0 h-16 bg-blue-900 text-white z-50 border-b-2 border-blue-700">
      <div className="flex items-center justify-between h-full px-4">
        {/* Left side - Logo and menu toggle */}
        <div className="flex items-center space-x-4">
          <button
            onClick={toggleSidebar}
            className="p-2 rounded-md hover:bg-blue-700 transition-colors bg-blue-800"
            aria-label="Toggle sidebar"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-white rounded-md flex items-center justify-center">
              <span className="text-blue-900 font-bold text-sm">AI</span>
            </div>
            <h1 className="text-xl font-bold">Kebos AI</h1>
          </div>
        </div>

        {/* Center - Breadcrumbs (could be added later) */}
        <div className="flex-1"></div>

        {/* Right side - User info and actions */}
        <div className="flex items-center space-x-4">
          {/* Notifications */}
          <button
            className="p-2 rounded-md hover:bg-blue-700 transition-colors relative"
            aria-label="Notifications"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            <span className="absolute top-1 right-1 w-2 h-2 bg-error rounded-full"></span>
          </button>

          {/* User menu */}
          <div className="relative">
            <button className="flex items-center space-x-2 p-2 rounded-md hover:bg-blue-700 transition-colors">
              <div className="w-8 h-8 bg-white rounded-full flex items-center justify-center">
                <span className="text-blue-900 text-sm font-medium">
                  {user?.username?.charAt(0).toUpperCase() || 'U'}
                </span>
              </div>
              <div className="text-left">
                <div className="text-sm font-medium text-white">{user?.username || 'User'}</div>
                <div className="text-xs text-blue-200">{user?.role || 'Role'}</div>
              </div>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          </div>

          {/* Quick logout */}
          <button
            onClick={logout}
            className="p-2 rounded-md hover:bg-blue-700 transition-colors"
            aria-label="Logout"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
          </button>
        </div>
      </div>
    </header>
  );
}
