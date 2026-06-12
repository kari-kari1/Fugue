/**
 * 插件管理API
 */

import { apiClient } from './client';

export interface Plugin {
  name: string;
  description: string;
  version: string;
  author: string;
  license: string;
  homepage: string | null;
  tags: string[];
  tools_count: number;
  tools: ToolInfo[];
}

export interface ToolInfo {
  name: string;
  description: string;
  permissions: 'safe' | 'caution' | 'dangerous';
  category: string;
  version?: string;
}

export interface ToolExecutionResult {
  success: boolean;
  tool_name: string;
  result: string;
}

export interface HealthCheckResult {
  results: Record<string, { healthy: boolean; message: string }>;
  total: number;
  healthy_count: number;
}

/**
 * 获取所有已加载的插件
 */
export async function getPlugins(): Promise<{ plugins: Plugin[]; total: number }> {
  const response = await apiClient.get('/plugins/');
  return response.data;
}

/**
 * 获取插件详情
 */
export async function getPluginDetail(pluginName: string): Promise<Plugin> {
  const response = await apiClient.get(`/plugins/${pluginName}`);
  return response.data;
}

/**
 * 获取所有可用工具
 */
export async function getTools(params?: {
  category?: string;
  permission?: string;
}): Promise<{ tools: ToolInfo[]; total: number }> {
  const response = await apiClient.get('/plugins/tools', { params });
  return response.data;
}

/**
 * 执行工具
 */
export async function executeTool(
  toolName: string,
  arguments_: Record<string, any>
): Promise<ToolExecutionResult> {
  const response = await apiClient.post(`/plugins/execute/${toolName}`, {
    tool_name: toolName,
    arguments: arguments_,
  });
  return response.data;
}

/**
 * 获取OpenAI格式的工具Schema
 */
export async function getOpenAISchemas(params?: {
  category?: string;
  permission?: string;
}): Promise<{ schemas: any[]; count: number }> {
  const response = await apiClient.get('/plugins/schemas/openai', { params });
  return response.data;
}

/**
 * 获取Anthropic格式的工具Schema
 */
export async function getAnthropicSchemas(params?: {
  category?: string;
  permission?: string;
}): Promise<{ schemas: any[]; count: number }> {
  const response = await apiClient.get('/plugins/schemas/anthropic', { params });
  return response.data;
}

/**
 * 重新加载插件
 */
export async function reloadPlugin(pluginName: string): Promise<{ success: boolean; message: string }> {
  const response = await apiClient.post('/plugins/reload', {
    plugin_name: pluginName,
  });
  return response.data;
}

/**
 * 执行健康检查
 */
export async function healthCheckPlugins(): Promise<HealthCheckResult> {
  const response = await apiClient.post('/plugins/health-check');
  return response.data;
}

/**
 * 获取活跃执行
 */
export async function getActiveExecutions(): Promise<{
  active_count: number;
  executions: string[];
}> {
  const response = await apiClient.get('/plugins/active-executions');
  return response.data;
}

// ── 插件市场 API ──────────────────────────────────

export interface MarketplacePlugin {
  id: string;
  plugin_name: string;
  display_name: string;
  description: string;
  current_version: string;
  author: string;
  category: string;
  tags: string[];
  download_count: number;
  average_rating: number;
  install_command: string | null;
  tools_list: string[];
  status: string;
}

/**
 * 获取市场插件列表
 */
export async function getMarketplacePlugins(params?: {
  category?: string;
  search?: string;
  page?: number;
  page_size?: number;
}): Promise<{ plugins: MarketplacePlugin[]; total: number; page: number }> {
  const response = await apiClient.get('/plugins/marketplace/', { params });
  return response.data;
}

/**
 * 安装市场插件
 */
export async function installMarketplacePlugin(pluginId: string): Promise<{ message: string }> {
  const response = await apiClient.post(`/plugins/marketplace/${pluginId}/install`);
  return response.data;
}

/**
 * 卸载市场插件
 */
export async function uninstallMarketplacePlugin(pluginId: string): Promise<{ message: string }> {
  const response = await apiClient.post(`/plugins/marketplace/${pluginId}/uninstall`);
  return response.data;
}
