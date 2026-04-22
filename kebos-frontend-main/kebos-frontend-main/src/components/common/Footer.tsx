
import { Activity, ExternalLink } from 'lucide-react';

export function Footer() {
  return (
    <footer className="bg-white border-t border-gray-200 px-4 lg:px-6 py-4">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col sm:flex-row items-center justify-between space-y-2 sm:space-y-0">
          {/* Left side */}
          <div className="flex items-center space-x-4 text-sm text-gray-500">
            <span>© {new Date().getFullYear()} KEBOS Cyber Threat Platform</span>
            <span>•</span>
            <span>Version 1.0.0</span>
          </div>
          
          {/* Right side */}
          <div className="flex items-center space-x-6">
            {/* System Status */}
            <div className="flex items-center space-x-2 text-sm">
              <Activity className="h-4 w-4 text-success animate-pulse" />
              <span className="text-gray-600">System Online</span>
            </div>

            {/* Links */}
            <div className="flex items-center space-x-4 text-sm">
              <a 
                href="/docs" 
                className="text-gray-500 hover:text-white transition-colors flex items-center space-x-1"
              >
                <span>Documentation</span>
                <ExternalLink className="h-3 w-3" />
              </a>
              <a 
                href="/support" 
                className="text-gray-500 hover:text-white transition-colors"
              >
                Support
              </a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
