/* API客户端配置 */

import axios, { AxiosError } from 'axios';
import toast from 'react-hot-toast';
import { useAuthStore } from '../stores/authStore';

// 扩展 AxiosRequestConfig 类型
declare module 'axios' {
  interface InternalAxiosRequestConfig {
    _redirectCount?: number;
  }
  interface AxiosRequestConfig {
    _redirectCount?: number;
  }
}

// D1: API base URL 环境变量化（Tauri 生产构建使用绝对 URL）
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: false,
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    if (config.url?.startsWith('http')) {
      const url = new URL(config.url);
      config.url = url.pathname + url.search;
    }
    const token = useAuthStore.getState().token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string; message?: string }>) => {
    // 307重定向处理（带循环检测）
    if (error.response?.status === 307) {
      const location = error.response.headers['location'];
      const redirectCount = (error.config?._redirectCount || 0) + 1;
      if (location && redirectCount <= 3) {
        let redirectUrl = location;
        if (redirectUrl.startsWith('http')) {
          try { redirectUrl = new URL(redirectUrl).pathname + new URL(redirectUrl).search; } catch { /* ignore */ }
        }
        return apiClient.request({ ...error.config, url: redirectUrl, baseURL: '', _redirectCount: redirectCount });
      }
    }

    const status = error.response?.status;

    // 无响应 = 网络错误
    if (!error.response) {
      toast.error('网络连接失败，请检查网络');
      return Promise.reject(error);
    }

    switch (status) {
      case 401:
        // 让 authStore 处理，不显示 toast
        useAuthStore.getState().logout();
        break;

      case 403:
        toast.error('没有权限执行此操作');
        break;

      case 404:
        toast.error('请求的资源不存在');
        break;

      case 422: {
        const data = error.response.data;
        // 尝试提取验证错误信息
        const detail = data?.detail;
        if (Array.isArray(detail)) {
          // FastAPI validation error format: [{ loc, msg, type }]
          const messages = detail.map((e: { loc?: string[]; msg: string }) =>
            e.loc ? `${e.loc.join('.')}: ${e.msg}` : e.msg
          );
          toast.error(messages.join('\n'));
        } else if (typeof detail === 'string') {
          toast.error(detail);
        } else if (data?.message) {
          toast.error(data.message);
        } else {
          toast.error('请求数据验证失败');
        }
        break;
      }

      case 429:
        toast.error('请求过于频繁，请稍后重试');
        break;

      case 500:
      case 502:
      case 503:
      case 504:
        toast.error('服务器错误，请稍后重试');
        break;

      default:
        // 其他错误不自动 toast，由调用方自行处理
        break;
    }

    return Promise.reject(error);
  }
);

export { apiClient };
export default apiClient;
