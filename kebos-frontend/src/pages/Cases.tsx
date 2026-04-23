import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Case } from '../types/threat';
import apiClient from '../api/apiClient';

const Cases: React.FC = () => {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<'all' | 'open' | 'resolved' | 'breached'>('all');
  const [selectedTimeline, setSelectedTimeline] = useState<Case | null>(null);
  const [downloadingPDF, setDownloadingPDF] = useState<string | null>(null);

  // Fetch cases
  const { data: cases, isLoading } = useQuery({
    queryKey: ['cases', filter],
    queryFn: async () => {
      const response = await apiClient.get<Case[]>('/api/v1/cases/', {
        params: filter === 'open' ? { status: 'open' } : undefined,
      });
      return response.data;
    },
    refetchInterval: 60000,
  });

  // Approve action mutation
  const approveActionMutation = useMutation({
    mutationFn: async (caseId: string) => {
      await apiClient.post(`/api/v1/cases/${caseId}/approve-action`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cases'] });
    },
  });

  // Filter cases
  const filteredCases = cases?.filter((c) => {
    if (filter === 'all') return true;
    if (filter === 'open') return c.status === 'OPEN';
    if (filter === 'resolved') return c.status === 'CLOSED';
    if (filter === 'breached') {
      const hoursLeft = (new Date(c.cert_in_deadline).getTime() - Date.now()) / 3600000;
      return hoursLeft <= 0;
    }
    return true;
  }) || [];

  // CERT-In countdown logic
  const getDeadlineDisplay = (deadline: string) => {
    const hoursLeft = (new Date(deadline).getTime() - Date.now()) / 3600000;
    
    if (hoursLeft <= 0) {
      return {
        text: 'DEADLINE BREACHED',
        className: 'bg-red-600 text-white px-2 py-1 text-xs font-bold rounded',
      };
    }
    
    if (hoursLeft < 1) {
      return {
        text: `${Math.floor(hoursLeft * 60)}m remaining`,
        className: 'text-red-600 font-bold border border-red-600 px-2 py-1 text-xs rounded',
      };
    }
    
    if (hoursLeft < 3) {
      return {
        text: `${Math.floor(hoursLeft)}h ${Math.floor((hoursLeft % 1) * 60)}m`,
        className: 'text-amber-600 font-semibold flex items-center gap-1',
        showPulsingDot: true,
      };
    }
    
    return {
      text: `${Math.floor(hoursLeft)}h ${Math.floor((hoursLeft % 1) * 60)}m`,
      className: 'text-green-600',
    };
  };

  // View timeline
  const handleViewTimeline = async (caseId: string) => {
    try {
      const response = await apiClient.get(`/api/v1/cases/${caseId}/timeline`);
      setSelectedTimeline(response.data);
    } catch (error) {
      console.error('Failed to fetch timeline:', error);
    }
  };

  // Generate CERT-In report
  const handleGenerateCertIn = async (caseId: string) => {
    setDownloadingPDF(caseId);
    try {
      const response = await apiClient.post(
        `/api/v1/cases/${caseId}/cert-in-report`,
        {},
        { responseType: 'blob' }
      );
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.download = `cert-in-${caseId}.pdf`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to generate CERT-In report:', error);
    } finally {
      setDownloadingPDF(null);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-100 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-gray-300 rounded w-1/4"></div>
            <div className="h-12 bg-gray-300 rounded"></div>
            <div className="space-y-2">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="h-16 bg-gray-300 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-800 mb-6">Case Management</h1>

        {/* Filter Bar */}
        <div className="bg-white rounded-lg shadow-md p-4 mb-6">
          <div className="flex gap-2">
            {(['all', 'open', 'resolved', 'breached'] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-4 py-2 rounded font-medium transition-colors ${
                  filter === f
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Cases Table */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Case ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Indicator
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Category
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Severity
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  CERT-In Deadline
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredCases.map((case_) => {
                const deadlineDisplay = getDeadlineDisplay(case_.cert_in_deadline);
                return (
                  <tr key={case_.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                      {case_.case_number}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {case_.title}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {case_.threat_event_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 text-xs font-semibold rounded ${
                          case_.severity === 'CRITICAL'
                            ? 'bg-red-100 text-red-800'
                            : case_.severity === 'HIGH'
                            ? 'bg-orange-100 text-orange-800'
                            : case_.severity === 'MEDIUM'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-green-100 text-green-800'
                        }`}
                      >
                        {case_.severity}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {deadlineDisplay.showPulsingDot && (
                        <span className="inline-block w-2 h-2 bg-amber-500 rounded-full animate-pulse mr-2"></span>
                      )}
                      <span className={deadlineDisplay.className}>{deadlineDisplay.text}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 text-xs font-semibold rounded ${
                          case_.status === 'OPEN'
                            ? 'bg-blue-100 text-blue-800'
                            : case_.status === 'IN_PROGRESS'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-green-100 text-green-800'
                        }`}
                      >
                        {case_.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleViewTimeline(case_.id)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          View Timeline
                        </button>
                        <button
                          onClick={() => handleGenerateCertIn(case_.id)}
                          disabled={downloadingPDF === case_.id}
                          className="text-blue-600 hover:text-blue-900 disabled:opacity-50"
                        >
                          {downloadingPDF === case_.id ? 'Generating...' : 'Generate CERT-In'}
                        </button>
                        {case_.status === 'OPEN' && (
                          <button
                            onClick={() => approveActionMutation.mutate(case_.id)}
                            className="text-red-600 hover:text-red-900"
                          >
                            Approve Action
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {filteredCases.length === 0 && (
            <div className="text-center py-8 text-gray-500">No cases found</div>
          )}
        </div>

        {/* Timeline Modal */}
        {selectedTimeline && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden m-4">
              <div className="bg-gray-800 text-white px-6 py-4 flex justify-between items-center">
                <h2 className="text-xl font-bold">Case Timeline</h2>
                <button
                  onClick={() => setSelectedTimeline(null)}
                  className="px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded text-sm font-medium"
                >
                  Close
                </button>
              </div>
              <div className="p-6 overflow-y-auto max-h-[calc(90vh-80px)]">
                <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                  {JSON.stringify(selectedTimeline, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Cases;
