import { apiClient } from './apiClient.js';
import { ApiResponse, User } from '@/types';

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthResponse {
  user: User;
  token: string;
  refresh_token?: string;
  expires_in: number;
}

export class AuthService {
  private baseUrl = '/api/auth';

  async login(username: string, password: string): Promise<ApiResponse<AuthResponse>> {
    try {
      const response = await apiClient.post<ApiResponse<AuthResponse>>(`${this.baseUrl}/login`, {
        username,
        password,
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Login failed');
    }
  }

  async logout(token: string): Promise<ApiResponse> {
    try {
      const response = await apiClient.post<ApiResponse>(`${this.baseUrl}/logout`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Logout failed');
    }
  }

  async refreshToken(token: string): Promise<ApiResponse<AuthResponse>> {
    try {
      const response = await apiClient.post<ApiResponse<AuthResponse>>(`${this.baseUrl}/refresh`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Token refresh failed');
    }
  }

  async verifyToken(token: string): Promise<ApiResponse<User>> {
    try {
      const response = await apiClient.get<ApiResponse<User>>(`${this.baseUrl}/verify`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Token verification failed');
    }
  }

  async getUserProfile(token: string): Promise<ApiResponse<User>> {
    try {
      const response = await apiClient.get<ApiResponse<User>>(`${this.baseUrl}/profile`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to fetch user profile');
    }
  }

  async updateProfile(token: string, updates: Partial<User>): Promise<ApiResponse<User>> {
    try {
      const response = await apiClient.put<ApiResponse<User>>(`${this.baseUrl}/profile`, updates, {
        headers: { Authorization: `Bearer ${token}` },
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to update profile');
    }
  }

  async changePassword(token: string, currentPassword: string, newPassword: string): Promise<ApiResponse> {
    try {
      const response = await apiClient.post<ApiResponse>(`${this.baseUrl}/change-password`, {
        current_password: currentPassword,
        new_password: newPassword,
      }, {
        headers: { Authorization: `Bearer ${token}` },
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to change password');
    }
  }

  async requestPasswordReset(email: string): Promise<ApiResponse> {
    try {
      const response = await apiClient.post<ApiResponse>(`${this.baseUrl}/reset-password`, {
        email,
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to request password reset');
    }
  }

  async resetPassword(token: string, newPassword: string): Promise<ApiResponse> {
    try {
      const response = await apiClient.post<ApiResponse>(`${this.baseUrl}/reset-password/confirm`, {
        token,
        new_password: newPassword,
      });
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to reset password');
    }
  }
}

export const authService = new AuthService();
