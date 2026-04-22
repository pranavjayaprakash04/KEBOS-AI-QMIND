import { NavLink } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { 
  Home, Shield, BarChart3, Briefcase, ShieldCheck, 
  FileText, MessageSquare, Bot, Database, ClipboardList, 
  Settings, ChevronDown, ChevronRight, Activity
} from 'lucide-react';
import { useTheme } from '@/contexts/ThemeContext';

interface SidebarItem {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  path: string;
  badge?: string;
  children?: SidebarItem[];
}

const sidebarItems: SidebarItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    path: '/',
    icon: Home,
  },
  {
    id: 'threat-detection',
    label: 'Threat Detection',
    path: '/threat-detection',
    icon: Shield,
    badge: '12',
  },
  {
    id: 'network-analytics',
    label: 'Network Analytics',
    path: '/network-analytics',
    icon: BarChart3,
  },
  {
    id: 'assistant',
    label: 'AI Assistant',
    path: '/assistant',
    icon: Bot,
  },
  {
    id: 'job-manager',
    label: 'Job Manager',
    path: '/job-manager',
    icon: Briefcase,
  },
  {
    id: 'siem-integration',
    label: 'SIEM Integration',
    path: '/siem-integration',
    icon: ShieldCheck,
  },
  {
    id: 'secure-messaging',
    label: 'Secure Messaging',
    path: '/secure-messaging',
    icon: MessageSquare,
  },
  {
    id: 'model-management',
    label: 'Model Management',
    path: '/model-management',
    icon: Database,
  },
  {
    id: 'audit',
    label: 'Audit & Monitoring',
    path: '/audit',
    icon: ClipboardList,
  },
  {
    id: 'reports',
    label: 'Reports',
    path: '/reports',
    icon: FileText,
  },
  {
    id: 'settings',
    label: 'Settings',
    path: '/settings',
    icon: Settings,
  },
];

interface SidebarItemComponentProps {
  item: SidebarItem;
  depth?: number;
  isCollapsed?: boolean;
}

function SidebarItemComponent({ item, depth = 0, isCollapsed = false }: SidebarItemComponentProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const hasChildren = item.children && item.children.length > 0;

  const handleClick = () => {
    if (hasChildren) {
      setIsExpanded(!isExpanded);
    }
  };

  const itemContent = (
    <div className={`flex items-center justify-between w-full p-3 rounded-lg transition-all duration-200 group ${
      depth > 0 ? 'ml-4' : ''
    }`}>
      <div className="flex items-center space-x-3 min-w-0 flex-1">
        <item.icon className="flex-shrink-0 h-5 w-5" />
        {!isCollapsed && (
          <>
            <span className="font-medium truncate text-base">{item.label}</span>
            {item.badge && (
              <span className="px-2 py-1 text-sm bg-error text-white rounded-full ml-auto">
                {item.badge}
              </span>
            )}
          </>
        )}
      </div>
      {hasChildren && !isCollapsed && (
        <div className="flex-shrink-0">
          {isExpanded ? (
            <ChevronDown className="h-4 w-4 transition-transform duration-200" />
          ) : (
            <ChevronRight className="h-4 w-4 transition-transform duration-200" />
          )}
        </div>
      )}
    </div>
  );

  return (
    <div>
      {hasChildren ? (
        <button
          onClick={handleClick}
          className="w-full text-left text-black hover:text-blue-600 hover:bg-gray-100 transition-all duration-200 rounded-lg"
          title={isCollapsed ? item.label : undefined}
        >
          {itemContent}
        </button>
      ) : (
        <NavLink
          to={item.path}
          className={({ isActive }) =>
            `block transition-all duration-200 rounded-lg ${
              isActive
                ? 'bg-primary-100 text-primary-700 border-r-2 border-primary-600'
                : 'text-black hover:text-blue-600 hover:bg-gray-100'
            }`
          }
          title={isCollapsed ? item.label : undefined}
        >
          {itemContent}
        </NavLink>
      )}
      {hasChildren && isExpanded && !isCollapsed && (
        <div className="mt-1 space-y-1 ml-2">
          {item.children?.map((child) => (
            <SidebarItemComponent key={child.id} item={child} depth={depth + 1} isCollapsed={isCollapsed} />
          ))}
        </div>
      )}
    </div>
  );
}

export function Sidebar() {
  const { isSidebarOpen, sidebarCollapsed } = useTheme();
  const [isCollapsed, setIsCollapsed] = useState(false);

  useEffect(() => {
    setIsCollapsed(sidebarCollapsed);
  }, [sidebarCollapsed]);

  return (
    <>
      {/* Mobile overlay */}
      {isSidebarOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-30 lg:hidden" />
      )}
      
      {/* Sidebar */}
      <aside
        className={`bg-white border-r border-gray-200 transition-all duration-300 ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        } ${isCollapsed ? 'w-16' : 'w-64'} h-screen`}
      >
        <div className="flex flex-col h-full">
          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
            {sidebarItems.map((item) => (
              <SidebarItemComponent key={item.id} item={item} isCollapsed={isCollapsed} />
            ))}
          </nav>

          {/* System Status */}
          {!isCollapsed && (
            <div className="p-4 border-t border-gray-200">
              <div className="flex items-center space-x-3 text-base text-gray-600">
                <Activity className="h-4 w-4 text-success" />
                <span>System Online</span>
              </div>
              <div className="text-sm text-gray-500 mt-2">
                CTP v1.0.0 • {new Date().getFullYear()}
              </div>
            </div>
          )}

          {/* Collapsed status indicator */}
          {isCollapsed && (
            <div className="p-4 border-t border-gray-700 flex justify-center">
              <Activity className="h-5 w-5 text-success animate-pulse" />
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
