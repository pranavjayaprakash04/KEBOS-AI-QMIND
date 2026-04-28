import React from 'react';
import { ThreatEvent, ThreatCategory, ThreatStatus } from '../types/threat';

interface ThreatCardProps {
  threat: ThreatEvent;
  onViewReport: (threat: ThreatEvent) => void;
  onApprove: (threat: ThreatEvent) => void;
  onMarkBenign: (threat: ThreatEvent) => void;
}

const ThreatCard: React.FC<ThreatCardProps> = ({
  threat,
  onViewReport,
  onApprove,
  onMarkBenign,
}) => {
  const getCategoryColor = (category: ThreatCategory): string => {
    const colors: Record<ThreatCategory, string> = {
      C2_Infrastructure: 'bg-red-100 text-red-800 border-red-500',
      Botnet_IP: 'bg-red-100 text-red-800 border-red-500',
      Phishing: 'bg-orange-100 text-orange-800 border-orange-500',
      Malware: 'bg-orange-100 text-orange-800 border-orange-500',
      Credential_Leak: 'bg-yellow-100 text-yellow-800 border-yellow-500',
      DDoS: 'bg-yellow-100 text-yellow-800 border-yellow-500',
      Insider_Threat: 'bg-purple-100 text-purple-800 border-purple-500',
      Supply_Chain: 'bg-purple-100 text-purple-800 border-purple-500',
      CVE_Exploitation: 'bg-red-100 text-red-800 border-red-500',
      Benign: 'bg-green-100 text-green-800 border-green-500',
    };
    return colors[category] || 'bg-gray-100 text-gray-800 border-gray-500';
  };

  const getStatusColor = (status: ThreatStatus): string => {
    const colors: Record<ThreatStatus, string> = {
      PENDING: 'bg-gray-100 text-gray-800',
      ELEVATED: 'bg-yellow-100 text-yellow-800',
      CONFIRMED_THREAT: 'bg-red-100 text-red-800',
      FALSE_POSITIVE: 'bg-green-100 text-green-800',
      BENIGN: 'bg-green-100 text-green-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const isProactiveSource = (): boolean => {
    const proactiveSources = ['ct_log', 'paste_monitor', 'domain_monitor', 'apk_monitor'];
    return proactiveSources.includes(threat.source);
  };

  const isGovDomain = (): boolean => {
    if (threat.ioc_type === 'domain' || threat.ioc_type === 'url') {
      const govTlds = ['.gov', '.gov.in', '.gov.uk', '.gov.au', '.gov.ca', '.gov.sg', '.gov.my', '.gov.ph', '.gov.bd', '.gov.lk', '.gov.np'];
      return govTlds.some(tld => threat.ioc_value.toLowerCase().endsWith(tld));
    }
    return false;
  };

  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-4 border border-gray-200 hover:shadow-lg transition-shadow">
      {/* Header with indicator and category */}
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1">
          <div className="font-mono text-sm text-gray-600 break-all mb-2">
            {threat.ioc_value}
          </div>
          <div className="flex gap-2 mb-2">
            <span className="text-xs text-gray-500 uppercase">{threat.ioc_type}</span>
            <span
              className={`inline-block px-2 py-1 text-xs font-bold rounded border ${getCategoryColor(
                threat.lead_category
              )}`}
            >
              {threat.lead_category.replace('_', ' ')}
            </span>
          </div>
        </div>
        <span
          className={`ml-2 px-2 py-1 text-xs font-semibold rounded ${getStatusColor(
            threat.status
          )}`}
        >
          {threat.status.replace('_', ' ')}
        </span>
      </div>

      {/* Proactive Detection Badge */}
      {isProactiveSource() && (
        <div className="mb-3">
          <div className="bg-blue-100 border border-blue-500 rounded px-2 py-1 text-xs font-bold text-blue-800 inline-flex items-center">
            🔍 PROACTIVELY DETECTED — identified before any network impact
          </div>
        </div>
      )}

      {/* Government Domain Flag */}
      {isGovDomain() && (
        <div className="mb-3">
          <div className="bg-amber-100 border border-amber-500 rounded px-2 py-1 text-xs font-bold text-amber-800 inline-flex items-center">
            🏛️ GOVERNMENT DOMAIN — high-priority target
          </div>
        </div>
      )}

      {/* Confidence Bar */}
      <div className="mb-3">
        <div className="flex justify-between text-xs text-gray-600 mb-1">
          <span>Confidence</span>
          <span>{(threat.confidence * 100).toFixed(1)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all"
            style={{ width: `${threat.confidence * 100}%` }}
          />
        </div>
      </div>

      {/* Reversibility Tag */}
      <div className="mb-3">
        <span
          className={`inline-block px-2 py-1 text-xs font-semibold rounded ${
            threat.reversibility === 'REVERSIBLE'
              ? 'bg-green-100 text-green-800'
              : 'bg-red-100 text-red-800'
          }`}
        >
          {threat.reversibility}
        </span>
      </div>

      {/* Timestamp */}
      <div className="text-xs text-gray-500 mb-4">
        {formatTimestamp(threat.created_at)}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2">
        <button
          onClick={() => onViewReport(threat)}
          className="flex-1 px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-medium rounded transition-colors"
        >
          View Report
        </button>
        {threat.reversibility === 'IRREVERSIBLE' && (
          <button
            onClick={() => onApprove(threat)}
            className="flex-1 px-3 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded transition-colors"
          >
            Approve
          </button>
        )}
        <button
          onClick={() => onMarkBenign(threat)}
          className="flex-1 px-3 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded transition-colors"
        >
          Mark Benign
        </button>
      </div>
    </div>
  );
};

export default ThreatCard;
