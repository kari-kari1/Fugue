/* 迭代相关API */

import apiClient from './client';
import type { Iteration, IterationCreate } from '../types/iteration';

export const iterationsApi = {
  // 获取迭代列表
  list: async (executionId: string): Promise<Iteration[]> => {
    const response = await apiClient.get<Iteration[]>(
      `/executions/${executionId}/iterations`
    );
    return response.data;
  },

  // 创建迭代
  create: async (executionId: string, data: IterationCreate): Promise<Iteration> => {
    const response = await apiClient.post<Iteration>(
      `/executions/${executionId}/refine`,
      data
    );
    return response.data;
  },
};
