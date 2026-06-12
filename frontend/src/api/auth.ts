/* 认证相关API */

import apiClient from './client';
import type { User, TokenResponse } from '../types';

export const authApi = {
  // 用户注册
  register: async (data: {
    email: string;
    username: string;
    password: string;
    full_name?: string;
  }): Promise<User> => {
    const response = await apiClient.post('/auth/register', data);
    return response.data;
  },

  // 用户登录
  login: async (data: {
    email: string;
    password: string;
  }): Promise<TokenResponse> => {
    const response = await apiClient.post('/auth/login', data);
    return response.data;
  },

  // 获取当前用户信息
  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },

  // 刷新Token
  refreshToken: async (): Promise<TokenResponse> => {
    const response = await apiClient.post('/auth/refresh');
    return response.data;
  },
};
