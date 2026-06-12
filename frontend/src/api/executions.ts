/* 执行相关API */

import apiClient from './client';
import type { Execution, TaskExecution } from '../types';

export interface ExecutionStats {
  total_executions: number;
  completed_executions: number;
  success_rate: number;
  total_tokens: number;
  total_cost: number;
}

export const executionsApi = {
  // 获取执行记录列表
  list: async (params?: {
    crew_id?: string;
    skip?: number;
    limit?: number;
  }): Promise<Execution[]> => {
    const response = await apiClient.get('/executions/', { params });
    return response.data;
  },

  // 创建执行（启动工作流）
  create: async (data: {
    crew_id: string;
    inputs?: Record<string, any>;
    trigger_type?: string;
    llm_api_keys?: Record<string, string>;
    llm_base_urls?: Record<string, string>;
  }): Promise<Execution> => {
    const response = await apiClient.post('/executions/', data, { timeout: 120000 });
    return response.data;
  },

  // 获取执行详情
  get: async (executionId: string): Promise<Execution> => {
    const response = await apiClient.get(`/executions/${executionId}`);
    return response.data;
  },

  // 获取执行中各任务的执行记录
  getTaskExecutions: async (executionId: string): Promise<TaskExecution[]> => {
    const response = await apiClient.get(`/executions/${executionId}/task-executions`);
    return response.data;
  },

  // 取消执行
  cancel: async (executionId: string): Promise<void> => {
    await apiClient.post(`/executions/${executionId}/cancel`);
  },

  // 获取执行统计摘要
  getStats: async (): Promise<ExecutionStats> => {
    const response = await apiClient.get('/executions/stats/summary');
    return response.data;
  },

  // 获取检查点列表
  getCheckpoints: async (executionId: string): Promise<any[]> => {
    const response = await apiClient.get(`/executions/${executionId}/checkpoints`);
    return response.data;
  },

  // 暂停执行
  pause: async (executionId: string): Promise<void> => {
    await apiClient.post(`/executions/${executionId}/pause`);
  },

  // 恢复执行
  resume: async (executionId: string): Promise<void> => {
    await apiClient.post(`/executions/${executionId}/resume`);
  },

  // 无头模式执行
  runHeadless: async (data: {
    crew_id: string;
    inputs?: Record<string, any>;
    llm_api_keys?: Record<string, string>;
    llm_base_urls?: Record<string, string>;
    max_turns?: number;
    output_format?: string;
    webhook_url?: string;
  }): Promise<any> => {
    const response = await apiClient.post('/executions/run', data, { timeout: 600000 });
    return response.data;
  },
};
