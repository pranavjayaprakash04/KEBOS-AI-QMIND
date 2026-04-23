import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Upload, Play, CheckCircle, XCircle, AlertTriangle, Trash2, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';

interface ModelInfo {
  id: string;
  name: string;
  version: string;
  model_type: string;
  description?: string;
  uploaded_at: string;
  file_size: number;
  status: 'uploaded' | 'active' | 'inactive' | 'error';
  performance_metrics?: {
    precision?: number;
    recall?: number;
    f1_score?: number;
    auc_roc?: number;
  };
  configuration?: any;
}

interface TestResult {
  is_threat: boolean;
  confidence: number;
  reconstruction_error?: number;
  threshold?: number;
  timestamp: string;
}

export default function ModelManagementPage() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [activeModel, setActiveModel] = useState<ModelInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [testing, setTesting] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState<ModelInfo | null>(null);
  const [testResult, setTestResult] = useState<TestResult | null>(null);

  // Upload form state
  const [uploadForm, setUploadForm] = useState({
    name: '',
    version: '1.0.0',
    model_type: 'autoencoder',
    description: '',
    model_file: null as File | null,
    config_file: null as File | null,
    scaler_file: null as File | null
  });

  // Test form state
  const [testData, setTestData] = useState({
    packet_size: '1024',
    flow_duration: '5.5',
    protocol_type: '6',
    src_port: '80',
    dst_port: '443',
    packet_count: '10',
    byte_count: '10240',
    tcp_flags: '24'
  });

  useEffect(() => {
    fetchModels();
    fetchActiveModel();
  }, []);

  const fetchModels = async () => {
    try {
      const response = await fetch('/api/model-management/models', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setModels(data);
      } else {
        toast.error('Failed to fetch models');
      }
    } catch (error) {
      toast.error('Error fetching models');
    } finally {
      setLoading(false);
    }
  };

  const fetchActiveModel = async () => {
    try {
      const response = await fetch('/api/model-management/models/active/info', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setActiveModel(data.active_model);
      }
    } catch (error) {
      console.error('Error fetching active model:', error);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!uploadForm.model_file) {
      toast.error('Please select a model file');
      return;
    }

    setUploading(true);
    
    try {
      const formData = new FormData();
      formData.append('name', uploadForm.name);
      formData.append('version', uploadForm.version);
      formData.append('model_type', uploadForm.model_type);
      formData.append('description', uploadForm.description);
      formData.append('model_file', uploadForm.model_file);
      
      if (uploadForm.config_file) {
        formData.append('config_file', uploadForm.config_file);
      }
      
      if (uploadForm.scaler_file) {
        formData.append('scaler_file', uploadForm.scaler_file);
      }

      const response = await fetch('/api/model-management/models/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });

      if (response.ok) {
        await response.json();
        toast.success('Model uploaded successfully!');
        
        // Reset form
        setUploadForm({
          name: '',
          version: '1.0.0',
          model_type: 'autoencoder',
          description: '',
          model_file: null,
          config_file: null,
          scaler_file: null
        });
        
        // Refresh models list
        fetchModels();
      } else {
        const error = await response.json();
        toast.error(`Upload failed: ${error.detail}`);
      }
    } catch (error) {
      toast.error('Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleTestModel = async (modelId: string) => {
    setTesting(modelId);
    setTestResult(null);
    
    try {
      const response = await fetch(`/api/model-management/models/${modelId}/test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          model_id: modelId,
          test_data: Object.fromEntries(
            Object.entries(testData).map(([key, value]) => [key, parseFloat(value) || 0])
          )
        })
      });

      if (response.ok) {
        const result = await response.json();
        setTestResult(result.test_result);
        toast.success('Model test completed!');
      } else {
        const error = await response.json();
        toast.error(`Test failed: ${error.detail || error.message}`);
      }
    } catch (error) {
      toast.error('Test failed');
    } finally {
      setTesting(null);
    }
  };

  const handleActivateModel = async (modelId: string) => {
    try {
      const response = await fetch(`/api/model-management/models/${modelId}/activate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        toast.success('Model activated successfully!');
        fetchModels();
        fetchActiveModel();
      } else {
        const error = await response.json();
        toast.error(`Activation failed: ${error.detail}`);
      }
    } catch (error) {
      toast.error('Activation failed');
    }
  };

  const handleDeleteModel = async (modelId: string) => {
    if (!confirm('Are you sure you want to delete this model?')) {
      return;
    }

    try {
      const response = await fetch(`/api/model-management/models/${modelId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        toast.success('Model deleted successfully!');
        fetchModels();
      } else {
        const error = await response.json();
        toast.error(`Deletion failed: ${error.detail}`);
      }
    } catch (error) {
      toast.error('Deletion failed');
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'error':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-black">Model Management</h1>
          <p className="text-gray-600 mt-2">Upload, test, and manage your threat detection models</p>
        </div>
        <div className="flex items-center space-x-4">
          <button
            onClick={() => fetchModels()}
            className="px-4 py-2 bg-gray-100 text-black rounded-lg hover:bg-gray-200 transition-colors flex items-center space-x-2"
          >
            <RefreshCw className="h-4 w-4" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Active Model Status */}
      {activeModel && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-green-50 border border-green-200 rounded-lg p-6"
        >
          <div className="flex items-center space-x-3">
            <CheckCircle className="h-6 w-6 text-green-500" />
            <div>
              <h3 className="text-lg font-semibold text-black">Active Model</h3>
              <p className="text-gray-600">
                {activeModel.name} v{activeModel.version} ({activeModel.model_type})
              </p>
            </div>
          </div>
        </motion.div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Upload New Model */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow"
        >
          <h2 className="text-xl font-semibold text-black mb-6 flex items-center space-x-2">
            <Upload className="h-5 w-5" />
            <span>Upload New Model</span>
          </h2>

          <form onSubmit={handleUpload} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-black mb-2">Model Name</label>
                <input
                  type="text"
                  value={uploadForm.name}
                  onChange={(e) => setUploadForm({ ...uploadForm, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-black"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-black mb-2">Version</label>
                <input
                  type="text"
                  value={uploadForm.version}
                  onChange={(e) => setUploadForm({ ...uploadForm, version: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-black"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-black mb-2">Model Type</label>
              <select
                value={uploadForm.model_type}
                onChange={(e) => setUploadForm({ ...uploadForm, model_type: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-black"
              >
                <option value="autoencoder">Autoencoder</option>
                <option value="classifier">Classifier</option>
                <option value="anomaly_detector">Anomaly Detector</option>
                <option value="custom">Custom</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-black mb-2">Description</label>
              <textarea
                value={uploadForm.description}
                onChange={(e) => setUploadForm({ ...uploadForm, description: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-black"
                rows={3}
              />
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-black mb-2">Model File *</label>
                <input
                  type="file"
                  accept=".pkl,.joblib,.h5,.pt,.pth,.onnx"
                  onChange={(e) => setUploadForm({ ...uploadForm, model_file: e.target.files?.[0] || null })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-black"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-black mb-2">Configuration File</label>
                <input
                  type="file"
                  accept=".json"
                  onChange={(e) => setUploadForm({ ...uploadForm, config_file: e.target.files?.[0] || null })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-black"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-black mb-2">Scaler File</label>
                <input
                  type="file"
                  accept=".pkl,.joblib"
                  onChange={(e) => setUploadForm({ ...uploadForm, scaler_file: e.target.files?.[0] || null })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-black"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={uploading}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2"
            >
              {uploading ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  <span>Uploading...</span>
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4" />
                  <span>Upload Model</span>
                </>
              )}
            </button>
          </form>
        </motion.div>

        {/* Test Model */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow"
        >
          <h2 className="text-xl font-semibold text-black mb-6 flex items-center space-x-2">
            <Play className="h-5 w-5" />
            <span>Test Model</span>
          </h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-black mb-2">Select Model to Test</label>
              <select
                value={selectedModel?.id || ''}
                onChange={(e) => setSelectedModel(models.find(m => m.id === e.target.value) || null)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-black"
              >
                <option value="">Select a model...</option>
                {models.map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.name} v{model.version}
                  </option>
                ))}
              </select>
            </div>

            {selectedModel && (
              <>
                <div className="grid grid-cols-2 gap-3">
                  {Object.entries(testData).map(([key, value]) => (
                    <div key={key}>
                      <label className="block text-sm font-medium text-black mb-1 capitalize">
                        {key.replace('_', ' ')}
                      </label>
                      <input
                        type="number"
                        step="any"
                        value={value}
                        onChange={(e) => setTestData({ ...testData, [key]: e.target.value })}
                        className="w-full px-2 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 text-black text-sm"
                      />
                    </div>
                  ))}
                </div>

                <button
                  onClick={() => handleTestModel(selectedModel.id)}
                  disabled={testing === selectedModel.id}
                  className="w-full bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2"
                >
                  {testing === selectedModel.id ? (
                    <>
                      <RefreshCw className="h-4 w-4 animate-spin" />
                      <span>Testing...</span>
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4" />
                      <span>Test Model</span>
                    </>
                  )}
                </button>

                {testResult && (
                  <div className={`p-4 rounded-lg border ${testResult.is_threat ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'}`}>
                    <h4 className="font-semibold text-black mb-2">Test Result</h4>
                    <div className="space-y-1 text-sm">
                      <p className="text-black">
                        <span className="font-medium">Threat Detected:</span> {testResult.is_threat ? 'Yes' : 'No'}
                      </p>
                      <p className="text-black">
                        <span className="font-medium">Confidence:</span> {(testResult.confidence * 100).toFixed(2)}%
                      </p>
                      {testResult.reconstruction_error && (
                        <p className="text-black">
                          <span className="font-medium">Reconstruction Error:</span> {testResult.reconstruction_error.toFixed(4)}
                        </p>
                      )}
                      {testResult.threshold && (
                        <p className="text-black">
                          <span className="font-medium">Threshold:</span> {testResult.threshold}
                        </p>
                      )}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </motion.div>
      </div>

      {/* Models List */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow"
      >
        <h2 className="text-xl font-semibold text-black mb-6">Uploaded Models</h2>

        {models.length === 0 ? (
          <div className="text-center py-8">
            <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">No models uploaded yet. Upload your first model above!</p>
          </div>
        ) : (
          <div className="space-y-4">
            {models.map((model) => (
              <div
                key={model.id}
                className="border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(model.status)}
                    <div>
                      <h3 className="font-semibold text-black">{model.name}</h3>
                      <p className="text-sm text-gray-600">
                        v{model.version} • {model.model_type} • {formatFileSize(model.file_size)}
                      </p>
                      {model.description && (
                        <p className="text-sm text-gray-500 mt-1">{model.description}</p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {model.status !== 'active' && (
                      <button
                        onClick={() => handleActivateModel(model.id)}
                        className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors text-sm"
                      >
                        Activate
                      </button>
                    )}
                    <button
                      onClick={() => handleDeleteModel(model.id)}
                      className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 transition-colors text-sm"
                      disabled={model.status === 'active'}
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
                
                {model.performance_metrics && (
                  <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    {Object.entries(model.performance_metrics).map(([metric, value]) => (
                      <div key={metric}>
                        <span className="text-gray-600 capitalize">{metric.replace('_', ' ')}:</span>
                        <span className="text-black font-medium ml-1">{(value * 100).toFixed(1)}%</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </motion.div>
    </div>
  );
}
