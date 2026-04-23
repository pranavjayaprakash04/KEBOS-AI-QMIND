/**
 * Model Management Service
 * Handles all API calls related to model management
 */

export interface ModelInfo {
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

export interface ActiveModelInfo {
  is_loaded: boolean;
  metadata: any;
  configuration: any;
  has_scaler: boolean;
  active_model?: ModelInfo;
}

export interface ModelTestResult {
  is_threat: boolean;
  confidence: number;
  reconstruction_error?: number;
  threshold?: number;
  timestamp: string;
  model_id: string;
  model_name: string;
  model_type: string;
}

class ModelManagementService {
  private baseUrl = '/api/model-management';

  private getAuthHeaders() {
    const token = localStorage.getItem('token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  /**
   * Fetch all available models
   */
  async fetchModels(): Promise<ModelInfo[]> {
    const response = await fetch(`${this.baseUrl}/models`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('Failed to fetch models');
    }

    return response.json();
  }

  /**
   * Fetch active model information
   */
  async fetchActiveModel(): Promise<ActiveModelInfo> {
    const response = await fetch(`${this.baseUrl}/models/active/info`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('Failed to fetch active model');
    }

    return response.json();
  }

  /**
   * Activate a specific model
   */
  async activateModel(modelId: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/models/${modelId}/activate`, {
      method: 'POST',
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('Failed to activate model');
    }
  }

  /**
   * Delete a model
   */
  async deleteModel(modelId: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/models/${modelId}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('Failed to delete model');
    }
  }

  /**
   * Test a model with sample data
   */
  async testModel(modelId: string, testData: Record<string, any>): Promise<ModelTestResult> {
    const response = await fetch(`${this.baseUrl}/models/${modelId}/test`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(testData)
    });

    if (!response.ok) {
      throw new Error('Failed to test model');
    }

    return response.json();
  }

  /**
   * Upload a new model
   */
  async uploadModel(formData: FormData): Promise<ModelInfo> {
    const token = localStorage.getItem('token');
    const response = await fetch(`${this.baseUrl}/models/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
        // Don't set Content-Type for FormData, let browser set it with boundary
      },
      body: formData
    });

    if (!response.ok) {
      throw new Error('Failed to upload model');
    }

    return response.json();
  }

  /**
   * Get model validation results
   */
  async validateModel(modelId: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/models/${modelId}/validate`, {
      method: 'POST',
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('Failed to validate model');
    }

    return response.json();
  }

  /**
   * Get model performance metrics
   */
  async getModelMetrics(modelId: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/models/${modelId}/metrics`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('Failed to fetch model metrics');
    }

    return response.json();
  }

  /**
   * Create model backup
   */
  async createBackup(modelId: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/models/${modelId}/backup`, {
      method: 'POST',
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('Failed to create backup');
    }
  }

  /**
   * Restore model from backup
   */
  async restoreFromBackup(modelId: string, backupId: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/models/${modelId}/restore`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ backup_id: backupId })
    });

    if (!response.ok) {
      throw new Error('Failed to restore from backup');
    }
  }

  /**
   * Get model health status
   */
  async getModelHealth(modelId: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/models/${modelId}/health`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('Failed to fetch model health');
    }

    return response.json();
  }
}

// Utility functions for formatting
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
};

export const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

export const formatPercentage = (value: number): string => {
  return (value * 100).toFixed(1) + '%';
};

// Export singleton instance
export const modelManagementService = new ModelManagementService();
