import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  withCredentials: true, // credentials:'include' for HttpOnly cookies
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - NO manual Authorization header injection
// Token is sent automatically via HttpOnly cookie
apiClient.interceptors.request.use(
  (config) => {
    // Do NOT add Authorization header - cookie handles auth
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login on 401
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;
