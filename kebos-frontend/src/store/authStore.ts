import { create } from 'zustand';
import apiClient from '../api/apiClient';

interface UserProfile {
  id: number;
  username: string;
  email?: string;
  role: string;
  tenant_id: number;
  fido2_verified: boolean;
}

interface AuthState {
  isAuthenticated: boolean;
  user: UserProfile | null;
  setAuth: (user: UserProfile) => void;
  logout: () => void;
  rehydrate: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: false,
  user: null,

  setAuth: (user: UserProfile) => {
    set({ isAuthenticated: true, user });
    // NO localStorage.setItem for token - cookie handles auth
  },

  logout: async () => {
    await apiClient.post('/api/v1/auth/logout');
    set({ isAuthenticated: false, user: null });
    // NO localStorage.removeItem for token - cookie handles auth
  },

  rehydrate: async () => {
    try {
      // Call /api/v1/auth/me to rehydrate from HttpOnly cookie
      const response = await apiClient.get('/api/v1/auth/me');
      set({ isAuthenticated: true, user: response.data.user });
    } catch (error) {
      set({ isAuthenticated: false, user: null });
    }
  },
}));
