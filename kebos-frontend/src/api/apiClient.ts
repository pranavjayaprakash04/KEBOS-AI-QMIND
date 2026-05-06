import axios from 'axios';
import { useAuthStore } from '../store/authStore';

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

const apiClient = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Request interceptor - NO manual Authorization header injection
// Token is sent automatically via HttpOnly cookie
apiClient.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling with 401 retry
let isRefreshing = false;
let refreshSubscribers: ((token: string) => void)[] = [];

function subscribeTokenRefresh(cb: (token: string) => void) {
  refreshSubscribers.push(cb);
}

function onTokenRefreshed() {
  refreshSubscribers.forEach((cb) => cb('refreshed'));
  refreshSubscribers = [];
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      return Promise.reject(new ApiError(408, 'Connection timed out. Check your network.'));
    }

    if (!error.response) {
      return Promise.reject(new ApiError(0, 'Network error. Check your connection.'));
    }

    const status = error.response.status;

    // Handle 401 with retry for token refresh (except for auth endpoints)
    if (status === 401 && !originalRequest._retry) {
      const isAuthEndpoint = originalRequest.url?.includes('/auth/login') ||
                            originalRequest.url?.includes('/auth/refresh');

      if (isAuthEndpoint) {
        // Don't retry auth endpoint failures
        window.location.href = '/login';
        return Promise.reject(new ApiError(401, 'Session expired. Please log in again.'));
      }

      originalRequest._retry = true;

      if (!isRefreshing) {
        isRefreshing = true;
        try {
          // Try to refresh token
          await apiClient.post('/api/v1/auth/refresh');
          isRefreshing = false;
          onTokenRefreshed();
        } catch (refreshError) {
          isRefreshing = false;
          refreshSubscribers = [];
          // Refresh failed - logout and redirect
          useAuthStore.getState().logout();
          window.location.href = '/login';
          return Promise.reject(new ApiError(401, 'Session expired. Please log in again.'));
        }
      } else {
        // Wait for token refresh
        return new Promise((resolve) => {
          subscribeTokenRefresh(() => {
            resolve(apiClient(originalRequest));
          });
        });
      }

      // Retry original request
      return apiClient(originalRequest);
    }

    if (status === 401) {
      window.location.href = '/login';
      return Promise.reject(new ApiError(401, 'Session expired. Please log in again.'));
    }

    if (status === 403) {
      return Promise.reject(new ApiError(403, "You don't have permission to view this resource."));
    }

    if (status === 404) {
      return Promise.reject(new ApiError(404, 'This resource does not exist or has been removed.'));
    }

    if (status === 503) {
      return Promise.reject(new ApiError(503, 'Service temporarily unavailable. Please try again shortly.'));
    }

    if (status >= 500) {
      return Promise.reject(new ApiError(status, 'An unexpected error occurred. Our team has been notified.'));
    }

    return Promise.reject(error);
  }
);

export default apiClient;
export { ApiError };
