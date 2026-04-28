import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

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

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      return Promise.reject(new ApiError(408, 'Connection timed out. Check your network.'));
    }

    if (!error.response) {
      return Promise.reject(new ApiError(0, 'Network error. Check your connection.'));
    }

    const status = error.response.status;

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
