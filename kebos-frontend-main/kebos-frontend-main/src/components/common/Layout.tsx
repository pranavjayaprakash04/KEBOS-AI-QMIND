import { ReactNode, useEffect } from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { Footer } from './Footer';
import { useTheme } from '@/contexts/ThemeContext';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const { isSidebarOpen } = useTheme();

  // Close sidebar on mobile when clicking outside
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 1024) {
        // On desktop, always show sidebar
        document.body.style.overflow = 'unset';
      } else if (isSidebarOpen) {
        // On mobile, prevent body scroll when sidebar is open
        document.body.style.overflow = 'hidden';
      } else {
        document.body.style.overflow = 'unset';
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      document.body.style.overflow = 'unset';
    };
  }, [isSidebarOpen]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <Header />

      {/* Main section with Sidebar and Content */}
      <div className="flex">
        {/* Sidebar */}
        <Sidebar />

        {/* Content + Footer */}
        <div className="flex-1 flex flex-col">
          {/* Main content */}
          <main className="flex-1 min-h-screen flex justify-center">
            <div className="w-full max-w-full p-4 lg:p-6">
              <div className="animate-fade-in">
                {children}
              </div>
            </div>
          </main>

          {/* Footer */}
          <Footer />
        </div>
      </div>
    </div>
  );
}
