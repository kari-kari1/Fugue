/* 任务（Task）相关API */

import apiClient from './client';
import type { Task } from '../types';

export const tasksApi = {
  // 创建任务
  create: async (data: {
    crew_id: string;
    name: string;
    description: string;
    expected_output?: string;
    output_type?: string;
    output_file?: string;
    context_task_ids?: string[];
    agent_id?: string;
    max_retries?: number;
    timeout_seconds?: number;
    human_review_required?: boolean;
    validation_rules?: any[];
    position_x?: number;
    position_y?: number;
    config?: Record<string, any>;
  }): Promise<Task> => {
    const response = await apiClient.post('/tasks/', data);
    return response.data;
  },

  // 获取任务详情
  get: async (taskId: string): Promise<Task> => {
    const response = await apiClient.get(`/tasks/${taskId}`);
    return response.data;
  },

  // 更新任务
  update: async (taskId: string, data: Partial<Task>): Promise<Task> => {
    const response = await apiClient.put(`/tasks/${taskId}`, data);
    return response.data;
  },

  // 删除任务
  delete: async (taskId: string): Promise<void> => {
    await apiClient.delete(`/tasks/${taskId}`);
  },
};
