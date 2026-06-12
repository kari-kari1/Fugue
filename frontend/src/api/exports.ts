/* 导出API客户端 */

import apiClient from './client';

export const exportsApi = {
  exportCrewJson: async (crewId: string): Promise<Blob> => {
    const response = await apiClient.get(`/exports/crews/${crewId}/export/json`, {
      responseType: 'blob',
    });
    return response.data;
  },

  exportExecutionMarkdown: async (executionId: string): Promise<Blob> => {
    const response = await apiClient.get(`/exports/executions/${executionId}/export/markdown`, {
      responseType: 'blob',
    });
    return response.data;
  },

  exportExecutionJson: async (executionId: string): Promise<Blob> => {
    const response = await apiClient.get(`/exports/executions/${executionId}/export/json`, {
      responseType: 'blob',
    });
    return response.data;
  },
};

export function downloadBlob(blob: Blob, filename: string) {
  if (typeof window === 'undefined' || !window.URL) {
    throw new Error('当前环境不支持文件下载');
  }
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}
