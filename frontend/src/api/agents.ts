/* 智能体（Agent）相关API */

import apiClient from './client';
import type { Agent } from '../types';

export const agentsApi = {
  // 创建智能体
  create: async (data: {
    crew_id: string;
    name: string;
    role: string;
    goal: string;
    backstory?: string;
    llm_provider?: string;
    llm_model?: string;
    temperature?: number;
    max_tokens?: number;
    allow_delegation?: boolean;
    max_iterations?: number;
    system_prompt_template?: string;
    tools_config?: string[];
    position_x?: number;
    position_y?: number;
  }): Promise<Agent> => {
    const response = await apiClient.post('/agents/', data);
    return response.data;
  },

  // 获取智能体详情
  get: async (agentId: string): Promise<Agent> => {
    const response = await apiClient.get(`/agents/${agentId}`);
    return response.data;
  },

  // 更新智能体
  update: async (agentId: string, data: Partial<Agent>): Promise<Agent> => {
    const response = await apiClient.put(`/agents/${agentId}`, data);
    return response.data;
  },

  // 删除智能体
  delete: async (agentId: string): Promise<void> => {
    await apiClient.delete(`/agents/${agentId}`);
  },
};
