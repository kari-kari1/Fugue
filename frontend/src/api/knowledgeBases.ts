/* 知识库相关 API */

import apiClient from './client';
import type { KnowledgeBase, AgentKnowledgeMapping } from '../types';

export const knowledgeBasesApi = {
  // 获取所有知识库
  list: async (params?: { page?: number; limit?: number }): Promise<KnowledgeBase[]> => {
    const response = await apiClient.get('/knowledge-bases/', { params });
    return response.data;
  },

  // 获取指定 Agent 关联的知识库
  listByAgent: async (agentId: string): Promise<KnowledgeBase[]> => {
    const response = await apiClient.get(`/knowledge-bases/agent/${agentId}/knowledge-bases`);
    return response.data;
  },

  // 关联 Agent 到知识库
  linkAgent: async (kbId: string, agentId: string): Promise<AgentKnowledgeMapping> => {
    const response = await apiClient.post(`/knowledge-bases/${kbId}/agent-mappings`, { agent_id: agentId });
    return response.data;
  },

  // 取消 Agent 与知识库的关联
  unlinkAgent: async (kbId: string, mappingId: string): Promise<void> => {
    await apiClient.delete(`/knowledge-bases/${kbId}/agent-mappings/${mappingId}`);
  },
};
