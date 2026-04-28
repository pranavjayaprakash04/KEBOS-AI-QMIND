import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ErrorMessage } from '../components/ErrorMessage';
import apiClient, { ApiError } from '../api/apiClient';

interface Report {
  id: string;
  case_id: string;
  case_number: string;
  indicator: string;
  generated_at: string;
  dilithium_signed: boolean;
}

const Reports: React.FC = () => {
  const [downloadingPDF, setDownloadingPDF] = useState<string | null>(null);
  const [downloadingJSON, setDownloadingJSON] = useState<string | null>(null);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [selectedCaseId, setSelectedCaseId] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  // Fetch reports
  const { data: reports, isLoading, refetch } = useQuery({
    queryKey: ['reports'],
    queryFn: async () => {
      const response = await apiClient.get<Report[]>('/api/v1/reports/');
      return response.data;
    },
  });

  // Generate CERT-In report
  const handleGenerateReport = async () => {
    if (!selectedCaseId) {
      setError('Please select a case to generate a report');
      return;
    }
    setGeneratingReport(true);
    setError(null);
    try {
      await apiClient.post('/api/v1/reports/cert-in', { case_id: selectedCaseId });
      refetch();
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Failed to generate report. Please try again.';
      setError(message);
    } finally {
      setGeneratingReport(false);
    }
  };

  // Download PDF
  const handleDownloadPDF = async (caseId: string) => {
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
      const message = error instanceof ApiError ? error.message : 'Failed to download PDF. Please try again.';
      setError(message);
    } finally {
      setDownloadingPDF(null);
    }
  };

  // Download JSON
  const handleDownloadJSON = async (reportId: string) => {
    setDownloadingJSON(reportId);
    try {
      const response = await apiClient.get(`/api/v1/reports/${reportId}`);
      const data = JSON.stringify(response.data, null, 2);
      const blob = new Blob([data], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `cert-in-${reportId}.json`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      const message = error instanceof ApiError ? error.message : 'Failed to download JSON. Please try again.';
      setError(message);
    } finally {
      setDownloadingJSON(null);
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
        {/* Error Banner */}
        {error && (
          <ErrorMessage
            message={error}
            onDismiss={() => setError(null)}
          />
        )}

        <h1 className="text-3xl font-bold text-gray-800 mb-6">SOC Reports & CERT-In Submissions</h1>

        {/* Generate Report Section */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-lg font-bold text-gray-800 mb-4">Generate CERT-In Report</h2>
          <div className="flex gap-4 items-end">
            <div className="flex-1">
              <label htmlFor="caseId" className="block text-sm font-medium text-gray-700 mb-1">
                Case ID
              </label>
              <input
                id="caseId"
                type="text"
                value={selectedCaseId}
                onChange={(e) => setSelectedCaseId(e.target.value)}
                placeholder="Enter case ID"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button
              onClick={handleGenerateReport}
              disabled={generatingReport}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {generatingReport ? (
                <>
                  <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Generating...
                </>
              ) : (
                'Generate Report'
              )}
            </button>
          </div>
        </div>

        {/* Reports Table */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Report ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Case
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Indicator
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Generated At
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Signed
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {reports?.map((report) => (
                <tr key={report.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                    {report.id.substring(0, 8)}...
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {report.case_number}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {report.indicator}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(report.generated_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {report.dilithium_signed ? (
                      <span className="text-green-600 font-semibold">🔐 Dilithium-3</span>
                    ) : (
                      <span className="text-amber-600 font-semibold">⚠️ Unsigned</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleDownloadPDF(report.case_id)}
                        disabled={downloadingPDF === report.case_id}
                        className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded transition-colors disabled:opacity-50"
                      >
                        {downloadingPDF === report.case_id ? 'Downloading...' : 'PDF'}
                      </button>
                      <button
                        onClick={() => handleDownloadJSON(report.id)}
                        disabled={downloadingJSON === report.id}
                        className="px-3 py-1 bg-gray-600 hover:bg-gray-700 text-white text-sm font-medium rounded transition-colors disabled:opacity-50"
                      >
                        {downloadingJSON === report.id ? 'Downloading...' : 'JSON'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {!reports || reports.length === 0 && (
            <div className="text-center py-8 text-gray-500">No reports found</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Reports;
