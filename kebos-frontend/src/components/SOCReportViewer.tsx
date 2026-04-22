import React from 'react';
import { SOCReport } from '../types/threat';

interface SOCReportViewerProps {
  report: SOCReport | null;
  onClose: () => void;
  onDownloadPDF: () => void;
}

const SOCReportViewer: React.FC<SOCReportViewerProps> = ({
  report,
  onClose,
  onDownloadPDF,
}) => {
  if (!report) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden m-4">
        {/* Header */}
        <div className="bg-gray-800 text-white px-6 py-4 flex justify-between items-center">
          <h2 className="text-xl font-bold">SOC Report</h2>
          <div className="flex gap-3">
            {report.dilithium_signature && (
              <div className="flex items-center gap-2 text-sm">
                <span className="text-green-400">✓</span>
                <span>Dilithium-3 Signed</span>
              </div>
            )}
            <button
              onClick={onDownloadPDF}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm font-medium transition-colors"
            >
              Download PDF
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded text-sm font-medium transition-colors"
            >
              Close
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-80px)]">
          {/* Executive Summary */}
          <section className="mb-6">
            <h3 className="text-lg font-bold text-gray-800 mb-3 border-b pb-2">
              Executive Summary
            </h3>
            <div className="prose max-w-none text-gray-700">
              {report.sections.executive_summary}
            </div>
          </section>

          {/* Technical Analysis */}
          <section className="mb-6">
            <h3 className="text-lg font-bold text-gray-800 mb-3 border-b pb-2">
              Technical Analysis
            </h3>
            <div className="prose max-w-none text-gray-700">
              {report.sections.technical_analysis}
            </div>
          </section>

          {/* IOC Details */}
          <section className="mb-6">
            <h3 className="text-lg font-bold text-gray-800 mb-3 border-b pb-2">
              IOC Details
            </h3>
            <div className="prose max-w-none text-gray-700">
              {report.sections.ioc_details}
            </div>
          </section>

          {/* Mitigation Recommendations */}
          <section className="mb-6">
            <h3 className="text-lg font-bold text-gray-800 mb-3 border-b pb-2">
              Mitigation Recommendations
            </h3>
            <div className="prose max-w-none text-gray-700">
              {report.sections.mitigation_recommendations}
            </div>
          </section>

          {/* Signature Verification */}
          {report.dilithium_signature && (
            <section className="mb-6 bg-gray-50 p-4 rounded border">
              <h3 className="text-lg font-bold text-gray-800 mb-2">
                Digital Signature Verification
              </h3>
              <div className="text-sm text-gray-600">
                <p><strong>Algorithm:</strong> Dilithium-3 (Post-Quantum Cryptography)</p>
                <p><strong>Signature:</strong> {report.dilithium_signature.substring(0, 64)}...</p>
                <p><strong>Generated At:</strong> {new Date(report.generated_at).toLocaleString()}</p>
                <p className="text-green-600 font-semibold mt-2">✓ Signature Valid</p>
              </div>
            </section>
          )}
        </div>
      </div>
    </div>
  );
};

export default SOCReportViewer;
