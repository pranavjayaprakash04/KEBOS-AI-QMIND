import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { ApiResponse } from '@/types';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token');
        if (token && !config.headers.Authorization) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor to handle common errors
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        return response;
      },
      async (error) => {
        const originalRequest = error.config;

        // Handle 401 Unauthorized
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          // Try to refresh token
          const token = localStorage.getItem('auth_token');
          if (token) {
            try {
              const refreshResponse = await this.post<ApiResponse<{ token: string; user: any }>>('/api/auth/refresh', {}, {
                headers: { Authorization: `Bearer ${token}` },
              });

              if (refreshResponse.data.success && refreshResponse.data.data) {
                const newToken = refreshResponse.data.data.token;
                localStorage.setItem('auth_token', newToken);
                localStorage.setItem('auth_user', JSON.stringify(refreshResponse.data.data.user));
                
                // Retry original request with new token
                originalRequest.headers.Authorization = `Bearer ${newToken}`;
                return this.client(originalRequest);
              }
            } catch (refreshError) {
              // Refresh failed, redirect to login
              localStorage.removeItem('auth_token');
              localStorage.removeItem('auth_user');
              window.location.href = '/login';
              return Promise.reject(refreshError);
            }
          } else {
            // No token, redirect to login
            window.location.href = '/login';
          }
        }

        // Handle 403 Forbidden
        if (error.response?.status === 403) {
          // Show permission denied message
          console.error('Permission denied');
        }

        // Handle 500 Internal Server Error
        if (error.response?.status === 500) {
          console.error('Internal server error');
        }

        return Promise.reject(error);
      }
    );
  }

  // GET request
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.get<T>(url, config);
  }

  // POST request
  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.post<T>(url, data, config);
  }

  // PUT request
  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.put<T>(url, data, config);
  }

  // PATCH request
  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.patch<T>(url, data, config);
  }

  // DELETE request
  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.delete<T>(url, config);
  }

  // Upload file
  async upload<T = any>(url: string, file: File, onProgress?: (progress: number) => void): Promise<AxiosResponse<T>> {
    const formData = new FormData();
    formData.append('file', file);

    return this.client.post<T>(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });
  }

  // Download file
  async download(url: string, filename?: string): Promise<void> {
    try {
      const response = await this.client.get(url, {
        responseType: 'blob',
      });

      const blob = new Blob([response.data]);
      const downloadUrl = window.URL.createObjectURL(blob);
      
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename || 'download';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      console.error('Download failed:', error);
      throw error;
    }
  }

  // Get client instance for custom requests
  getInstance(): AxiosInstance {
    return this.client;
  }

  // Update base URL
  setBaseURL(baseURL: string): void {
    this.client.defaults.baseURL = baseURL;
  }

  // Set default headers
  setDefaultHeaders(headers: Record<string, string>): void {
    Object.assign(this.client.defaults.headers, headers);
  }

  // Clear auth token
  clearAuthToken(): void {
    delete this.client.defaults.headers.Authorization;
  }
}

export const apiClient = new ApiClient();
