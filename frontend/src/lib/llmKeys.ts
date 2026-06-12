/* LLM 配置管理工具 */

const STORAGE_KEY = 'fugue_llm_config';

export interface LLMProviderConfig {
  api_key: string;
  base_url: string;
  model: string;
}

export type LLMConfigMap = Record<string, LLMProviderConfig>;

export function getLLMConfig(): LLMConfigMap {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

export function saveLLMConfig(config: LLMConfigMap) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
}

// 兼容旧格式：提取api_key用于后端
export function getLLMKeys(): Record<string, string> {
  const config = getLLMConfig();
  const keys: Record<string, string> = {};
  Object.entries(config).forEach(([provider, cfg]) => {
    if (cfg.api_key) keys[provider] = cfg.api_key;
  });
  return keys;
}

// 提取base_url映射
export function getLLMBaseUrls(): Record<string, string> {
  const config = getLLMConfig();
  const urls: Record<string, string> = {};
  Object.entries(config).forEach(([provider, cfg]) => {
    if (cfg.base_url) urls[provider] = cfg.base_url;
  });
  return urls;
}

export function hasConfiguredKeys(): boolean {
  const config = getLLMConfig();
  return Object.values(config).some((v) => v.api_key && v.api_key.trim());
}
