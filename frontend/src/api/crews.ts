/* 工作流（Crew）相关API */

import apiClient from './client';
import type { Crew, Agent, Task } from '../types';

export const crewsApi = {
  // 获取工作流列表
  list: async (params?: {
    skip?: number;
    limit?: number;
    is_template?: string;
  }): Promise<Crew[]> => {
    const response = await apiClient.get('/crews/', { params });
    return response.data;
  },

  // 创建工作流
  create: async (data: {
    name: string;
    description?: string;
    process?: string;
    max_execution_time?: number;
    cost_budget?: number;
    metadata?: Record<string, any>;
  }): Promise<Crew> => {
    const response = await apiClient.post('/crews/', data);
    return response.data;
  },

  // 获取工作流详情
  get: async (crewId: string): Promise<Crew> => {
    const response = await apiClient.get(`/crews/${crewId}`);
    return response.data;
  },

  // 更新工作流
  update: async (crewId: string, data: Partial<Crew>): Promise<Crew> => {
    const response = await apiClient.put(`/crews/${crewId}`, data);
    return response.data;
  },

  // 删除工作流
  delete: async (crewId: string): Promise<void> => {
    await apiClient.delete(`/crews/${crewId}`);
  },

  // 获取工作流下的智能体
  getAgents: async (crewId: string): Promise<Agent[]> => {
    const response = await apiClient.get(`/agents/crew/${crewId}`);
    return response.data;
  },

  // 获取工作流下的任务
  getTasks: async (crewId: string): Promise<Task[]> => {
    const response = await apiClient.get(`/tasks/crew/${crewId}`);
    return response.data;
  },
};
