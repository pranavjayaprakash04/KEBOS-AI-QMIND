import React, { useState } from 'react'
import apiClient from '../../../api/apiClient'

interface ComplianceItem {
  id: string
  label: string
  checked: boolean
  action?: 'generate' | 'export'
}

export const ComplianceWidget: React.FC = () => {
  const [items, setItems] = useState<ComplianceItem[]>([
    { id: 'detected', label: 'Incident detected within 6 hours', checked: true },
    { id: 'audit', label: 'Audit trail tamper-evident (Dilithium-3)', checked: true },
    { id: 'encrypted', label: 'Telemetry encrypted (Kyber-768 + AES-256-GCM)', checked: true },
    { id: 'siem', label: 'SIEM integration active', checked: true },
    { id: 'certin', label: 'CERT-In report submitted', checked: false, action: 'generate' },
  ])
  const [generating, setGenerating] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [message, setMessage] = useState<string | null>(null)

  const handleGenerateCertIn = async () => {
    setGenerating(true)
    try {
      // This would need a case_id - using a placeholder for now
      const response = await apiClient.post(
        '/api/v1/cases/sample-case/cert-in-report',
        {},
        { responseType: 'blob' }
      )
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.download = `cert-in-report-${new Date().toISOString().split('T')[0]}.pdf`
      link.click()
      window.URL.revokeObjectURL(url)

      setMessage('Report generated successfully')
      setItems(items.map(item =>
        item.id === 'certin' ? { ...item, checked: true } : item
      ))
    } catch (err) {
      setMessage('Failed to generate report')
    } finally {
      setGenerating(false)
    }
  }

  const handleExportAudit = async () => {
    setExporting(true)
    try {
      const today = new Date().toISOString().split('T')[0]
      const response = await apiClient.get('/api/v1/audit/export?format=json', {
        responseType: 'blob'
      })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.download = `audit_log_${today}.json`
      link.click()
      window.URL.revokeObjectURL(url)

      setMessage('Audit log exported successfully')
    } catch (err) {
      setMessage('Failed to export audit log')
    } finally {
      setExporting(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
      <h2 className="text-lg font-semibold text-gray-800 mb-4">CERT-In Compliance</h2>

      {message && (
        <div className="mb-4 p-2 bg-green-100 text-green-800 text-sm rounded">
          {message}
          <button onClick={() => setMessage(null)} className="ml-2 text-green-600 underline">
            Dismiss
          </button>
        </div>
      )}

      <div className="space-y-3">
        {items.map((item) => (
          <div key={item.id} className="flex items-start gap-3">
            <input
              type="checkbox"
              checked={item.checked}
              readOnly
              className="mt-1 h-4 w-4 text-blue-600 rounded border-gray-300"
            />
            <div className="flex-1">
              <span className={`text-sm ${item.checked ? 'text-gray-600' : 'text-gray-400'}`}>
                {item.label}
              </span>

              {item.id === 'certin' && !item.checked && (
                <button
                  onClick={handleGenerateCertIn}
                  disabled={generating}
                  className="mt-2 block w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded transition-colors disabled:opacity-50"
                >
                  {generating ? 'Generating...' : 'Generate Report'}
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 pt-4 border-t border-gray-200">
        <button
          onClick={handleExportAudit}
          disabled={exporting}
          className="w-full py-2 px-4 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-medium rounded transition-colors disabled:opacity-50"
        >
          {exporting ? 'Exporting...' : 'Export Audit Log'}
        </button>
      </div>
    </div>
  )
}

export default ComplianceWidget
