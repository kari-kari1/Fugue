/* 模板相关API */

import apiClient from './client';

export interface AgentConfig {
  name: string;
  role: string;
  goal: string;
  backstory: string;
  llm_provider: string;
  llm_model: string;
  tools: string[];
}

export interface TaskConfig {
  name: string;
  description: string;
  expected_output: string;
  output_type: string;
  agent_index: number;
  depends_on: number[];
}

export interface ConnectionConfig {
  source: number;
  target: number;
  type?: string;
}

export interface Template {
  id: string;
  name: string;
  description: string | null;
  category: string;
  icon: string;
  difficulty: string;
  agents_config: AgentConfig[];
  tasks_config: TaskConfig[];
  connections_config: ConnectionConfig[];
  process_type: string;
  tags: string[];
  use_count: number;
  rating: number;
  is_builtin: boolean;
  user_id: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface TemplateListResponse {
  items: Template[];
  total: number;
  page: number;
  limit: number;
}

export const templatesApi = {
  // 获取模板列表
  list: async (params?: {
    category?: string;
    search?: string;
    sort_by?: string;
    page?: number;
    limit?: number;
  }): Promise<TemplateListResponse> => {
    const response = await apiClient.get('/templates', { params });
    return response.data;
  },

  // 获取模板详情
  get: async (id: string): Promise<Template> => {
    const response = await apiClient.get(`/templates/${id}`);
    return response.data;
  },

  // 使用模板创建工作流
  use: async (id: string): Promise<{ message: string; crew_id: string; agents_count: number; tasks_count: number }> => {
    const response = await apiClient.post(`/templates/${id}/use`);
    return response.data;
  },
};
