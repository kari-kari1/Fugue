/**
 * 模型能力注册表
 * 定义各 LLM 提供商/模型对 function calling (tool use) 的支持情况
 * 支持逐工具级别的能力检测
 */

import type { ToolMeta, ToolCapability } from './tools';

export type ToolDisabledReason = 'model_no_tools' | 'not_implemented' | 'missing_capability';

export interface ToolSupportStatus {
  toolId: string;
  available: boolean;
  reason?: ToolDisabledReason;
  reasonText?: string;
}

export interface ToolSupportInfo {
  toolId: string;
  supported: boolean;
  reason?: string;
}

interface ModelPattern {
  pattern: RegExp;
  supportsTools: boolean;
}

interface ProviderCapabilities {
  supportsTools: boolean;
  modelPatterns?: ModelPattern[];
}

// 已知提供商的能力配置
const PROVIDER_CAPABILITIES: Record<string, ProviderCapabilities> = {
  // OpenAI — 所有主力模型均支持 function calling
  openai: {
    supportsTools: true,
    modelPatterns: [
      { pattern: /gpt-4o|gpt-4-turbo|gpt-4|gpt-3\.5-turbo|o1|o3|o4/i, supportsTools: true },
    ],
  },
  // Anthropic — Claude 3+ 均支持 tool use
  anthropic: {
    supportsTools: true,
    modelPatterns: [
      { pattern: /claude/i, supportsTools: true },
    ],
  },
  // DeepSeek — V2+ 支持 function calling (OpenAI 兼容)
  deepseek: {
    supportsTools: true,
    modelPatterns: [
      { pattern: /deepseek-chat|deepseek-coder|deepseek-v/i, supportsTools: true },
      { pattern: /deepseek-r1/i, supportsTools: false },  // 推理模型，不支持原生 function calling
    ],
  },
  // 通义千问 — qwen-turbo/qwen-plus/qwen-max 支持
  qwen: {
    supportsTools: true,
    modelPatterns: [
      { pattern: /qwen-turbo|qwen-plus|qwen-max|qwen-long|qwen2\.?5/i, supportsTools: true },
      { pattern: /qwen-vl|qwen-audio/i, supportsTools: false },  // 多模态专用模型
    ],
  },
  // 智谱AI — GLM-4 系列支持
  zhipu: {
    supportsTools: true,
    modelPatterns: [
      { pattern: /glm-4|glm-3/i, supportsTools: true },
      { pattern: /cogview|cogvideo/i, supportsTools: false },  // 生成专用模型
    ],
  },
  // Moonshot — Kimi 支持 function calling
  moonshot: {
    supportsTools: true,
    modelPatterns: [
      { pattern: /moonshot|kimi/i, supportsTools: true },
    ],
  },
};

// 模型级别的细粒度能力注册表
// key 格式: "provider/model" (小写)，value 为该模型具备的能力集合
// 不在表中的模型 → 仅具备 function_calling（最基本能力）
const MODEL_CAPABILITIES: Record<string, ToolCapability[]> = {
  // OpenAI — 纯文本模型（支持 function calling，不支持图像生成）
  'openai/gpt-4o':          ['function_calling', 'image_generation'],
  'openai/gpt-4o-mini':     ['function_calling', 'image_generation'],
  'openai/gpt-4-turbo':     ['function_calling', 'image_generation'],
  'openai/gpt-3.5-turbo':   ['function_calling'],
  'openai/o1':              ['function_calling'],
  'openai/o3':              ['function_calling'],
  'openai/o4-mini':         ['function_calling'],
  // Anthropic — 纯文本模型
  'anthropic/claude-sonnet-4-20250514':   ['function_calling'],
  'anthropic/claude-3-5-sonnet-20241022': ['function_calling'],
  'anthropic/claude-3-5-haiku-20241022':  ['function_calling'],
  'anthropic/claude-3-opus-20240229':     ['function_calling'],
  // DeepSeek — 纯文本
  'deepseek/deepseek-chat':   ['function_calling'],
  'deepseek/deepseek-coder':  ['function_calling'],
  // Moonshot — 纯文本
  'moonshot/moonshot-v1-8k':  ['function_calling'],
  'moonshot/moonshot-v1-32k': ['function_calling'],
  'moonshot/moonshot-v1-128k':['function_calling'],
  // 通义千问 — 纯文本
  'qwen/qwen-turbo':  ['function_calling'],
  'qwen/qwen-plus':   ['function_calling'],
  'qwen/qwen-max':    ['function_calling'],
  // 智谱AI — 纯文本
  'zhipu/glm-4-flash':  ['function_calling'],
  'zhipu/glm-4':        ['function_calling'],
  // 演示模式
  'mock/mock-model':    ['function_calling'],
};

/**
 * 获取指定模型具备的能力集合
 * 优先从 MODEL_CAPABILITIES 精确匹配，否则返回默认 ['function_calling']
 */
export function getModelCapabilities(provider: string, model: string): ToolCapability[] {
  if (!provider || !model) return [];
  const key = `${provider.toLowerCase().trim()}/${model.toLowerCase().trim()}`;
  return MODEL_CAPABILITIES[key] ?? ['function_calling'];
}

// 通用启发式规则：未知提供商的模型名模式
const HEURISTIC_PATTERNS: ModelPattern[] = [
  // 已知支持 function calling 的模型名关键词
  { pattern: /gpt-4|gpt-3\.5|claude-3|claude-sonnet|qwen-|glm-4|gemini-pro|gemini-1\.5|gemini-2/i, supportsTools: true },
  // 推理模型通常不支持 function calling
  { pattern: /r1|o1-mini|o3-mini|reasoning/i, supportsTools: false },
  // 旧版模型
  { pattern: /gpt-3(?!-)|text-davinci|text-babbage|text-ada/i, supportsTools: false },
];

/**
 * 检查指定提供商+模型是否支持工具调用
 */
export function modelSupportsTools(provider: string, model: string): boolean {
  if (!provider || !model) return false;

  const providerKey = provider.toLowerCase().trim();
  const caps = PROVIDER_CAPABILITIES[providerKey];

  if (caps) {
    // 已知提供商：按模型模式匹配
    if (caps.modelPatterns) {
      for (const mp of caps.modelPatterns) {
        if (mp.pattern.test(model)) {
          return mp.supportsTools;
        }
      }
    }
    // 已知提供商但模型未匹配到具体模式 → 使用提供商默认值
    return caps.supportsTools;
  }

  // 未知提供商：使用启发式规则
  for (const hp of HEURISTIC_PATTERNS) {
    if (hp.pattern.test(model)) {
      return hp.supportsTools;
    }
  }

  // 未知提供商 + 未知模型 → 乐观假设支持（OpenAI 兼容接口通常支持）
  return true;
}

/**
 * 获取模型对8个内置工具的支持信息列表
 * 当前所有内置工具都依赖 function calling，
 * 所以如果模型不支持 function calling，所有工具都不可用
 */
export function getModelToolSupport(
  provider: string,
  model: string,
  allToolIds: string[],
): ToolSupportInfo[] {
  const supports = modelSupportsTools(provider, model);
  const reason = supports ? undefined : `${provider}/${model} 不支持 Function Calling`;

  return allToolIds.map((toolId) => ({
    toolId,
    supported: supports,
    reason,
  }));
}

/**
 * 获取模型的简要能力描述（用于 UI 展示）
 */
export function getModelCapabilitySummary(provider: string, model: string): string {
  if (!provider || !model) return '未知模型';
  if (provider === 'mock' || provider === 'demo') return '演示模式';
  if (modelSupportsTools(provider, model)) return '支持工具调用';
  return '不支持工具调用';
}

/**
 * 逐工具检测可用性
 * 检查顺序：工具已实现 → 模型支持 function calling → 模型具备工具所需的具体能力
 */
export function getToolSupportStatuses(
  provider: string,
  model: string,
  tools: ToolMeta[],
): ToolSupportStatus[] {
  const modelOk = modelSupportsTools(provider, model);
  const modelCaps = getModelCapabilities(provider, model);

  return tools.map((tool) => {
    // 1) 检查工具是否已实现
    if (!tool.implemented) {
      return {
        toolId: tool.id,
        available: false,
        reason: 'not_implemented',
        reasonText: '该工具尚未接入真实 API，暂时不可用',
      };
    }

    // 2) 检查模型是否支持 function calling
    if (!modelOk) {
      return {
        toolId: tool.id,
        available: false,
        reason: 'model_no_tools',
        reasonText: '当前模型不支持 Function Calling',
      };
    }

    // 3) 检查模型是否具备该工具所需的具体能力
    const missing = tool.requiredCapabilities.filter((c) => !modelCaps.includes(c));
    if (missing.length > 0) {
      return {
        toolId: tool.id,
        available: false,
        reason: 'missing_capability',
        reasonText: `当前模型缺少所需能力: ${missing.join(', ')}`,
      };
    }

    return { toolId: tool.id, available: true };
  });
}
