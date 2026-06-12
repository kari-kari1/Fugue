/* 认证状态管理 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import toast from 'react-hot-toast';
import type { User } from '../types';
import { authApi } from '../api/auth';

interface AuthState {
  user: User | null;
  token: string | null;
  tokenExpiresAt: number | null; // token过期时间戳（ms）
  isAuthenticated: boolean;
  isLoading: boolean;
  _hydrated: boolean; // 是否已从localStorage恢复
  login: (email: string, password: string) => Promise<void>;
  register: (data: { email: string; username: string; password: string; full_name?: string }) => Promise<'ok' | 'need_login'>;
  logout: () => void;
  loadUser: () => Promise<void>;
  refreshToken: () => Promise<void>;
  checkTokenExpiry: () => { isExpired: boolean; isExpiringSoon: boolean; remainingSeconds: number };
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      tokenExpiresAt: null,
      isAuthenticated: false,
      isLoading: true, // 默认loading，防止ProtectedRoute在token恢复前重定向
      _hydrated: false,

      login: async (email, password) => {
        set({ isLoading: true });
        try {
          const { access_token, expires_in } = await authApi.login({ email, password });
          const expiresAt = Date.now() + expires_in * 1000;
          set({ token: access_token, tokenExpiresAt: expiresAt });
          const user = await authApi.getCurrentUser();
          set({ user, isAuthenticated: true, isLoading: false });
        } catch (error) {
          set({ user: null, token: null, tokenExpiresAt: null, isAuthenticated: false, isLoading: false });
          throw error;
        }
      },

      register: async (data) => {
        set({ isLoading: true });
        try {
          await authApi.register(data);
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
        try {
          await get().login(data.email, data.password);
          return 'ok';
        } catch {
          set({ isLoading: false });
          return 'need_login';
        }
      },

      logout: () => {
        set({ user: null, token: null, tokenExpiresAt: null, isAuthenticated: false, isLoading: false });
      },

      loadUser: async () => {
        const token = get().token;
        if (!token) {
          set({ isAuthenticated: false, isLoading: false, _hydrated: true });
          return;
        }
        set({ isLoading: true });
        try {
          const user = await authApi.getCurrentUser();
          set({ user, isAuthenticated: true, isLoading: false, _hydrated: true });
        } catch {
          if (get().token) {
            toast.error('会话已过期，请重新登录');
          }
          set({ user: null, token: null, tokenExpiresAt: null, isAuthenticated: false, isLoading: false, _hydrated: true });
        }
      },

      refreshToken: async () => {
        try {
          const { access_token, expires_in } = await authApi.refreshToken();
          const expiresAt = Date.now() + expires_in * 1000;
          set({ token: access_token, tokenExpiresAt: expiresAt });
        } catch {
          // 刷新失败，清除登录状态
          get().logout();
          toast.error('会话已过期，请重新登录');
        }
      },

      checkTokenExpiry: () => {
        const { tokenExpiresAt } = get();
        if (!tokenExpiresAt) {
          return { isExpired: true, isExpiringSoon: true, remainingSeconds: 0 };
        }
        const remainingMs = tokenExpiresAt - Date.now();
        const remainingSeconds = Math.max(0, Math.floor(remainingMs / 1000));
        return {
          isExpired: remainingSeconds <= 0,
          isExpiringSoon: remainingSeconds <= 300, // 5分钟内视为即将过期
          remainingSeconds,
        };
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ token: state.token, tokenExpiresAt: state.tokenExpiresAt }),
      // 恢复后如果有token，自动开始验证
      onRehydrateStorage: () => {
        return (state) => {
          if (!state) return;
          if (state.token) {
            // 有token → 保持isLoading=true，等待loadUser验证
            state.isLoading = true;
            state._hydrated = false;
          } else {
            // 无token → 不需要loading
            state.isLoading = false;
            state._hydrated = true;
          }
        };
      },
    }
  )
);
