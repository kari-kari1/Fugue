/* 工作流发布API */

import apiClient from './client';

export interface PublishedWorkflow {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  version: string;
  is_public: boolean;
  rate_limit: number;
  created_at: string | null;
}

export interface PublishRequest {
  slug: string;
  name: string;
  description?: string;
  is_public?: boolean;
  version?: string;
  rate_limit?: number;
}

export interface ApiKeyInfo {
  id: string;
  name: string;
  key_prefix: string;
  permissions: string[];
  created_at: string;
  last_used_at: string | null;
}

export const publishedApi = {
  // 获取已发布的工作流列表
  list: async (): Promise<{ workflows: PublishedWorkflow[]; total: number }> => {
    const response = await apiClient.get('/published/');
    return response.data;
  },

  // 发布工作流
  publish: async (crewId: string, data: PublishRequest): Promise<{ success: boolean; workflow: PublishedWorkflow }> => {
    const response = await apiClient.post(`/published/publish/${crewId}`, data);
    return response.data;
  },

  // 取消发布
  unpublish: async (workflowId: string): Promise<void> => {
    await apiClient.delete(`/published/unpublish/${workflowId}`);
  },

  // 获取API状态
  getStatus: async (slug: string): Promise<{ name: string; version: string; description: string; status: string }> => {
    const response = await apiClient.get(`/published/status/${slug}`);
    return response.data;
  },
};

export const apiKeysApi = {
  // 获取API Key列表
  list: async (): Promise<{ keys: ApiKeyInfo[]; total: number }> => {
    const response = await apiClient.get('/api-keys/');
    return response.data;
  },

  // 创建API Key
  create: async (data: { name: string; permissions?: string[] }): Promise<{ key: string; key_info: ApiKeyInfo }> => {
    const response = await apiClient.post('/api-keys/', data);
    return response.data;
  },

  // 删除API Key
  delete: async (keyId: string): Promise<void> => {
    await apiClient.delete(`/api-keys/${keyId}`);
  },
};
