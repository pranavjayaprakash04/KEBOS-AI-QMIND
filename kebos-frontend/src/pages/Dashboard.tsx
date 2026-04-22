import React, { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { io, Socket } from 'socket.io-client';
import ThreatCard from '../components/ThreatCard';
import AnalystQueue from '../components/AnalystQueue';
import { ThreatEvent, Case } from '../types/threat';
import { useAuthStore } from '../store/authStore';
import apiClient from '../api/apiClient';

const Dashboard: React.FC = () => {
  const { user, isAuthenticated, rehydrate } = useAuthStore();
  const [socket, setSocket] = useState<Socket | null>(null);
  const [certInWarning, setCertInWarning] = useState<string | null>(null);

  // Rehydrate auth on mount
  useEffect(() => {
    rehydrate();
  }, [rehydrate]);

  // Redirect if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      window.location.href = '/login';
    }
  }, [isAuthenticated]);

  // Fetch threats
  const { data: threats, refetch: refetchThreats } = useQuery({
    queryKey: ['threats'],
    queryFn: async () => {
      const response = await apiClient.get<ThreatEvent[]>('/api/v1/threats');
      return response.data;
    },
    enabled: isAuthenticated,
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  // Fetch cases
  const { data: cases, refetch: refetchCases } = useQuery({
    queryKey: ['cases'],
    queryFn: async () => {
      const response = await apiClient.get<Case[]>('/api/v1/cases');
      return response.data;
    },
    enabled: isAuthenticated,
    refetchInterval: 30000,
  });

  // WebSocket connection
  useEffect(() => {
    if (!isAuthenticated || !user) return;

    const wsUrl = `${import.meta.env.VITE_WS_URL || 'ws://localhost:8000'}/ws/threats/${user.tenant_id}`;
    const newSocket = io(wsUrl);

    newSocket.on('connect', () => {
      console.log('WebSocket connected');
    });

    newSocket.on('threat_updated', () => {
      // Invalidate queries to trigger refetch
      refetchThreats();
      refetchCases();
    });

    newSocket.on('cert_in_warning', (message: string) => {
      setCertInWarning(message);
    });

    newSocket.on('disconnect', () => {
      console.log('WebSocket disconnected');
    });

    setSocket(newSocket);

    return () => {
      newSocket.disconnect();
    };
  }, [isAuthenticated, user, refetchThreats, refetchCases]);

  const handleViewReport = (threat: ThreatEvent) => {
    // TODO: Open SOC Report Viewer modal
    console.log('View report for threat:', threat.id);
  };

  const handleApprove = (threat: ThreatEvent) => {
    // TODO: Approve action for IRREVERSIBLE threats
    console.log('Approve threat:', threat.id);
  };

  const handleMarkBenign = async (threat: ThreatEvent) => {
    try {
      await apiClient.patch(`/api/v1/threats/${threat.id}`, {
        status: 'BENIGN',
      });
      refetchThreats();
    } catch (error) {
      console.error('Failed to mark threat as benign:', error);
    }
  };

  const handleApproveAction = async (caseId: string) => {
    try {
      await apiClient.post(`/api/v1/cases/${caseId}/approve-action`);
      refetchCases();
      refetchThreats();
    } catch (error) {
      console.error('Failed to approve action:', error);
    }
  };

  const handleViewCase = (caseId: string) => {
    // TODO: Open case details modal
    console.log('View case:', caseId);
  };

  // Calculate CERT-In SLA countdown for open cases
  const getOpenCasesWithDeadlines = () => {
    if (!cases) return [];
    const now = new Date();
    return cases
      .filter((c) => c.status === 'OPEN')
      .map((c) => ({
        ...c,
        hoursRemaining: Math.max(0, Math.floor((new Date(c.cert_in_deadline).getTime() - now.getTime()) / (1000 * 60 * 60))),
      }))
      .sort((a, b) => a.hoursRemaining - b.hoursRemaining);
  };

  const openCasesWithDeadlines = getOpenCasesWithDeadlines();
  const urgentCase = openCasesWithDeadlines[0];

  if (!isAuthenticated) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* CERT-In Warning Banner */}
      {certInWarning && (
        <div className="bg-red-600 text-white px-4 py-3 text-center font-semibold">
          ⚠️ {certInWarning}
          <button
            onClick={() => setCertInWarning(null)}
            className="ml-4 text-white underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Kebos AI Dashboard</h1>
            <div className="text-sm text-gray-600 mt-1">
              <span className="font-medium">{user?.organisation_name || 'Tenant'}</span>
              {' • '}
              <span className="font-medium">{user?.username || 'Analyst'}</span>
            </div>
          </div>
          
          {/* CERT-In SLA Countdown */}
          {urgentCase && (
            <div className={`px-4 py-2 rounded-lg ${
              urgentCase.hoursRemaining <= 1 ? 'bg-red-100 text-red-800' :
              urgentCase.hoursRemaining <= 3 ? 'bg-orange-100 text-orange-800' :
              'bg-green-100 text-green-800'
            }`}>
              <div className="text-xs font-semibold">CERT-In SLA Deadline</div>
              <div className="text-lg font-bold">{urgentCase.hoursRemaining}h</div>
              <div className="text-xs">{urgentCase.case_number}</div>
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left: Real-time Threat Feed */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-md p-4 border border-gray-200">
              <h2 className="text-lg font-bold text-gray-800 mb-4">Real-time Threat Feed</h2>
              <div className="space-y-3 max-h-[600px] overflow-y-auto">
                {threats && threats.length > 0 ? (
                  threats.slice(0, 10).map((threat) => (
                    <div
                      key={threat.id}
                      className="p-3 border border-gray-200 rounded hover:bg-gray-50 cursor-pointer transition-colors"
                    >
                      <div className="font-mono text-xs text-gray-700 break-all">
                        {threat.ioc_value}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {threat.lead_category.replace('_', ' ')} • {(threat.confidence * 100).toFixed(0)}%
                      </div>
                      <div className="text-xs text-gray-400 mt-1">
                        {new Date(threat.created_at).toLocaleTimeString()}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center text-gray-500 py-4">
                    No threats detected
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Center: ThreatCard Grid */}
          <div className="lg:col-span-2">
            <h2 className="text-lg font-bold text-gray-800 mb-4">Recent Threats</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {threats && threats.length > 0 ? (
                threats.slice(0, 6).map((threat) => (
                  <ThreatCard
                    key={threat.id}
                    threat={threat}
                    onViewReport={handleViewReport}
                    onApprove={handleApprove}
                    onMarkBenign={handleMarkBenign}
                  />
                ))
              ) : (
                <div className="col-span-2 text-center text-gray-500 py-8">
                  No threats to display
                </div>
              )}
            </div>
          </div>

          {/* Right: Analyst Queue */}
          <div className="lg:col-span-1">
            <AnalystQueue
              threats={threats || []}
              cases={cases || []}
              onApproveAction={handleApproveAction}
              onViewCase={handleViewCase}
            />
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
