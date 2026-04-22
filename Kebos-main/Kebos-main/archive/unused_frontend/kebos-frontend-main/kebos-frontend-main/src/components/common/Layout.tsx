import { ReactNode } from 'react';
import { Header } from './Header';
import {Sidebar} from './Sidebar';
import { Footer } from './Footer';
import { useTheme } from '@/contexts/ThemeContext';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const { isSidebarOpen } = useTheme();

  return (
    <div className="min-h-screen bg-background-primary flex flex-col">
      {/* Header */}
      <Header />

      {/* Main section with Sidebar and Content */}
      <div className="flex flex-1">
        {/* Sidebar */}
        <Sidebar />

        {/* Content + Footer */}
        <div
          className="flex-1 flex flex-col transition-all duration-300"
          style={{ marginLeft: isSidebarOpen ? '16rem' : '0' }}
        >
          {/* Main content */}
          <main className="flex-1 pt-16">
            <div className="p-6">
              {children}
            </div>
          </main>

          {/* Footer */}
          <Footer />
        </div>
      </div>
    </div>
  );
}
