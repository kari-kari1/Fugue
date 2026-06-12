/* 演示数据API */

import apiClient from './client';

export const demoApi = {
  // 创建示例工作流
  seedWorkflow: async (): Promise<{ message: string; crew_id: string; workflow: any }> => {
    const response = await apiClient.post('/demo/seed-demo-workflow');
    return response.data;
  },
};
