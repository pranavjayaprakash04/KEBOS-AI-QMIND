import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '../store/authStore';
import apiClient from '../api/apiClient';

interface Tenant {
  id: number;
  name: string;
  tenant_type: 'government' | 'bfsi' | 'enterprise';
  qmind_threshold_confirmed_threat: number;
  qmind_threshold_elevated: number;
  sla_hours: number;
  auth_policy: 'password_only' | 'mfa_required' | 'fido2_required';
  brand_patterns: string;
}

const Settings: React.FC = () => {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const [saving, setSaving] = useState(false);

  // Fetch current tenant
  const { data: tenant, isLoading } = useQuery({
    queryKey: ['tenant', user?.tenant_id],
    queryFn: async () => {
      const response = await apiClient.get<Tenant>(`/api/v1/admin/tenants/${user?.tenant_id}`);
      return response.data;
    },
    enabled: !!user?.tenant_id,
  });

  // Form state
  const [formData, setFormData] = useState<Partial<Tenant>>({});

  // Update form when tenant data loads
  React.useEffect(() => {
    if (tenant) {
      setFormData(tenant);
    }
  }, [tenant]);

  // Save mutation
  const saveMutation = useMutation({
    mutationFn: async (data: Partial<Tenant>) => {
      await apiClient.put(`/api/v1/admin/tenants/${user?.tenant_id}`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tenant'] });
      setSaving(false);
    },
    onError: () => {
      setSaving(false);
    },
  });

  const handleSave = () => {
    setSaving(true);
    saveMutation.mutate(formData);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-100 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-gray-300 rounded w-1/4"></div>
            <div className="h-12 bg-gray-300 rounded"></div>
            <div className="space-y-4">
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
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-800 mb-6">Tenant Settings</h1>

        <div className="bg-white rounded-lg shadow-md p-6 space-y-6">
          {/* Tenant Type (Read-only) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tenant Type
            </label>
            <div className="px-4 py-2 bg-gray-100 rounded text-gray-600">
              {tenant?.tenant_type.toUpperCase()}
            </div>
          </div>

          {/* QMind Threshold: Confirmed Threat */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              QMind Threshold: Confirmed Threat ({formData.qmind_threshold_confirmed_threat?.toFixed(2)})
            </label>
            <input
              type="range"
              min="0.60"
              max="0.80"
              step="0.01"
              value={formData.qmind_threshold_confirmed_threat || 0.70}
              onChange={(e) =>
                setFormData({ ...formData, qmind_threshold_confirmed_threat: parseFloat(e.target.value) })
              }
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>0.60</span>
              <span>0.80</span>
            </div>
          </div>

          {/* QMind Threshold: Elevated */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              QMind Threshold: Elevated ({formData.qmind_threshold_elevated?.toFixed(2)})
            </label>
            <input
              type="range"
              min="0.40"
              max="0.70"
              step="0.01"
              value={formData.qmind_threshold_elevated || 0.55}
              onChange={(e) =>
                setFormData({ ...formData, qmind_threshold_elevated: parseFloat(e.target.value) })
              }
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>0.40</span>
              <span>0.70</span>
            </div>
          </div>

          {/* SLA Hours */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              SLA Hours (default: 6)
            </label>
            <input
              type="range"
              min="2"
              max="24"
              step="1"
              value={formData.sla_hours || 6}
              onChange={(e) =>
                setFormData({ ...formData, sla_hours: parseInt(e.target.value) })
              }
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>2 hours</span>
              <span>24 hours</span>
            </div>
            <div className="text-center text-sm font-medium text-gray-700 mt-2">
              {formData.sla_hours} hours
            </div>
          </div>

          {/* Auth Policy */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Authentication Policy
            </label>
            <div className="space-y-2">
              {(['password_only', 'mfa_required', 'fido2_required'] as const).map((policy) => (
                <label key={policy} className="flex items-center">
                  <input
                    type="radio"
                    name="auth_policy"
                    value={policy}
                    checked={formData.auth_policy === policy}
                    onChange={(e) =>
                      setFormData({ ...formData, auth_policy: e.target.value as any })
                    }
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">
                    {policy.replace('_', ' ').toUpperCase()}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Brand Patterns */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Brand Patterns (one per line)
            </label>
            <textarea
              value={formData.brand_patterns || ''}
              onChange={(e) =>
                setFormData({ ...formData, brand_patterns: e.target.value })
              }
              rows={10}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter brand patterns, one per line..."
            />
            <p className="text-xs text-gray-500 mt-1">
              These patterns will be merged with global INDIAN_BRAND_PATTERNS in CT log monitor
            </p>
          </div>

          {/* Save Button */}
          <div className="flex justify-end">
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded transition-colors disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
