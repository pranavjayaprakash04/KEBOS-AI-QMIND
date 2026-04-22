import React from 'react';
import { ThreatEvent, ThreatStatus, Case } from '../types/threat';

interface AnalystQueueProps {
  threats: ThreatEvent[];
  cases: Case[];
  onApproveAction: (caseId: string) => void;
  onViewCase: (caseId: string) => void;
}

const AnalystQueue: React.FC<AnalystQueueProps> = ({
  threats,
  cases,
  onApproveAction,
  onViewCase,
}) => {
  const pendingThreats = threats.filter(
    (t) => t.status === 'CONFIRMED_THREAT' || t.status === 'ELEVATED'
  );

  const getCaseForThreat = (threatId: string): Case | undefined => {
    return cases.find((c) => c.threat_event_id === threatId);
  };

  const formatDeadline = (deadline: string): string => {
    const now = new Date();
    const deadlineDate = new Date(deadline);
    const diffMs = deadlineDate.getTime() - now.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));

    if (diffHours <= 0) {
      return 'OVERDUE';
    }
    return `${diffHours}h remaining`;
  };

  const getDeadlineColor = (deadline: string): string => {
    const now = new Date();
    const deadlineDate = new Date(deadline);
    const diffMs = deadlineDate.getTime() - now.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));

    if (diffHours <= 0) return 'text-red-600 font-bold';
    if (diffHours <= 2) return 'text-orange-600 font-semibold';
    return 'text-green-600';
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-4 border border-gray-200">
      <h2 className="text-lg font-bold text-gray-800 mb-4">Analyst Queue</h2>
      
      {pendingThreats.length === 0 ? (
        <div className="text-center text-gray-500 py-8">
          No threats awaiting analyst action
        </div>
      ) : (
        <div className="space-y-4">
          {pendingThreats.map((threat) => {
            const associatedCase = getCaseForThreat(threat.id);
            
            return (
              <div
                key={threat.id}
                className="border border-gray-200 rounded-lg p-3 hover:bg-gray-50 transition-colors"
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="flex-1">
                    <div className="font-mono text-sm text-gray-700 break-all">
                      {threat.ioc_value}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {threat.lead_category.replace('_', ' ')} • {(threat.confidence * 100).toFixed(1)}% confidence
                    </div>
                  </div>
                  <span
                    className={`ml-2 px-2 py-1 text-xs font-semibold rounded ${
                      threat.status === 'CONFIRMED_THREAT'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-yellow-100 text-yellow-800'
                    }`}
                  >
                    {threat.status.replace('_', ' ')}
                  </span>
                </div>

                {associatedCase && (
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium text-gray-700">
                        Case: {associatedCase.case_number}
                      </span>
                      <span className={`text-xs ${getDeadlineColor(associatedCase.cert_in_deadline)}`}>
                        CERT-In: {formatDeadline(associatedCase.cert_in_deadline)}
                      </span>
                    </div>
                    
                    {threat.reversibility === 'IRREVERSIBLE' ? (
                      <div className="flex gap-2">
                        <button
                          onClick={() => onViewCase(associatedCase.id)}
                          className="flex-1 px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-medium rounded transition-colors"
                        >
                          View Digital Twin
                        </button>
                        <button
                          onClick={() => onApproveAction(associatedCase.id)}
                          className="flex-1 px-3 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded transition-colors"
                        >
                          Approve Action
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => onViewCase(associatedCase.id)}
                        className="w-full px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded transition-colors"
                      >
                        View Case Details
                      </button>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default AnalystQueue;
