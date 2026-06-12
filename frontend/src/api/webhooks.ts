/* Webhook管理API */

import apiClient from './client';

export interface Webhook {
  id: string;
  url: string;
  events: string[];
  is_active: boolean;
  failure_count: number;
  last_triggered_at: string | null;
  created_at: string;
}

export interface WebhookCreate {
  url: string;
  events: string[];
  secret?: string;
}

export interface WebhookEventType {
  type: string;
  name: string;
  description: string;
}

export const webhooksApi = {
  // 获取Webhook列表
  list: async (): Promise<Webhook[]> => {
    const response = await apiClient.get('/webhooks/');
    return response.data;
  },

  // 创建Webhook
  create: async (data: WebhookCreate): Promise<Webhook> => {
    const response = await apiClient.post('/webhooks/', data);
    return response.data;
  },

  // 删除Webhook
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/webhooks/${id}`);
  },

  // 测试Webhook
  test: async (id: string): Promise<{ success: boolean; message: string }> => {
    const response = await apiClient.post(`/webhooks/${id}/test`);
    return response.data;
  },

  // 获取支持的事件类型
  getEvents: async (): Promise<{ events: WebhookEventType[]; total: number }> => {
    const response = await apiClient.get('/webhooks/events');
    return response.data;
  },
};
