/* 定时任务管理API */

import apiClient from './client';

export interface ScheduledTask {
  id: string;
  crew_id: string;
  cron_expression: string;
  timezone: string;
  inputs: Record<string, unknown>;
  is_active: boolean;
  last_run_at: string | null;
  next_run_at: string | null;
  run_count: number;
  failure_count: number;
}

export interface ScheduleCreate {
  crew_id: string;
  cron_expression: string;
  timezone?: string;
  inputs?: Record<string, unknown>;
}

export const schedulesApi = {
  // 获取定时任务列表
  list: async (): Promise<ScheduledTask[]> => {
    const response = await apiClient.get('/schedules/');
    return response.data;
  },

  // 创建定时任务
  create: async (data: ScheduleCreate): Promise<{ success: boolean; task: ScheduledTask }> => {
    const response = await apiClient.post('/schedules/', data);
    return response.data;
  },

  // 删除定时任务
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/schedules/${id}`);
  },

  // 启用/禁用定时任务
  toggle: async (id: string): Promise<{ success: boolean; is_active: boolean }> => {
    const response = await apiClient.patch(`/schedules/${id}/toggle`);
    return response.data;
  },

  // 验证Cron表达式
  validateCron: async (expression: string): Promise<{ valid: boolean; expression: string; next_runs: string[] }> => {
    const response = await apiClient.get('/schedules/cron/validate', { params: { expression } });
    return response.data;
  },

  // 获取定时任务详情
  get: async (id: string): Promise<ScheduledTask> => {
    const response = await apiClient.get(`/schedules/${id}`);
    return response.data;
  },
};
