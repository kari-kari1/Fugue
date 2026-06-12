/**
 * 工具定义注册表
 * 为8个内置工具提供元数据、图标、描述和 OpenAI function calling schema
 */

export type ToolCapability = 'function_calling' | 'image_generation';

export interface ToolMeta {
  id: string;
  name: string;
  icon: string;
  shortDesc: string;
  description: string;
  category: 'search' | 'file' | 'code' | 'data' | 'media' | 'analysis';
  implemented: boolean;
  requiredCapabilities: ToolCapability[];
  openaiSchema: {
    type: 'function';
    function: {
      name: string;
      description: string;
      parameters: Record<string, any>;
    };
  };
}

const TOOL_DEFINITIONS: ToolMeta[] = [
  {
    id: 'web_search',
    name: '网络搜索',
    icon: 'search',
    shortDesc: '搜索互联网获取实时信息',
    description: '在互联网上搜索信息，获取最新的网页内容和数据',
    category: 'search',
    implemented: true,
    requiredCapabilities: ['function_calling'],
    openaiSchema: {
      type: 'function',
      function: {
        name: 'web_search',
        description: 'Search the internet for real-time information',
        parameters: {
          type: 'object',
          properties: {
            query: { type: 'string', description: 'Search query' },
            max_results: { type: 'integer', description: 'Maximum results to return', default: 5 },
          },
          required: ['query'],
        },
      },
    },
  },
  {
    id: 'file_read',
    name: '读取文件',
    icon: 'file_read',
    shortDesc: '读取本地或远程文件内容',
    description: '读取指定路径的文件内容，支持文本和常见格式',
    category: 'file',
    implemented: true,
    requiredCapabilities: ['function_calling'],
    openaiSchema: {
      type: 'function',
      function: {
        name: 'file_read',
        description: 'Read the contents of a file',
        parameters: {
          type: 'object',
          properties: {
            file_path: { type: 'string', description: 'Path to the file' },
            encoding: { type: 'string', description: 'File encoding', default: 'utf-8' },
          },
          required: ['file_path'],
        },
      },
    },
  },
  {
    id: 'file_write',
    name: '写入文件',
    icon: 'file_write',
    shortDesc: '创建或覆写文件',
    description: '将内容写入指定路径的文件',
    category: 'file',
    implemented: true,
    requiredCapabilities: ['function_calling'],
    openaiSchema: {
      type: 'function',
      function: {
        name: 'file_write',
        description: 'Write content to a file',
        parameters: {
          type: 'object',
          properties: {
            file_path: { type: 'string', description: 'Path to write the file' },
            content: { type: 'string', description: 'Content to write' },
            mode: { type: 'string', enum: ['overwrite', 'append'], default: 'overwrite' },
          },
          required: ['file_path', 'content'],
        },
      },
    },
  },
  {
    id: 'code_execute',
    name: '执行代码',
    icon: 'code',
    shortDesc: '运行 Python/JS 代码片段',
    description: '在沙箱环境中执行代码，返回运行结果',
    category: 'code',
    implemented: true,
    requiredCapabilities: ['function_calling'],
    openaiSchema: {
      type: 'function',
      function: {
        name: 'code_execute',
        description: 'Execute code in a sandboxed environment',
        parameters: {
          type: 'object',
          properties: {
            language: { type: 'string', enum: ['python', 'javascript', 'bash'], description: 'Programming language' },
            code: { type: 'string', description: 'Code to execute' },
          },
          required: ['language', 'code'],
        },
      },
    },
  },
  {
    id: 'api_call',
    name: 'API调用',
    icon: 'api',
    shortDesc: '发送 HTTP 请求到外部 API',
    description: '向指定 URL 发送 HTTP 请求，支持 GET/POST 等方法',
    category: 'data',
    implemented: true,
    requiredCapabilities: ['function_calling'],
    openaiSchema: {
      type: 'function',
      function: {
        name: 'api_call',
        description: 'Make an HTTP request to an external API',
        parameters: {
          type: 'object',
          properties: {
            url: { type: 'string', description: 'API endpoint URL' },
            method: { type: 'string', enum: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'], default: 'GET' },
            headers: { type: 'object', description: 'Request headers', additionalProperties: { type: 'string' } },
            body: { type: 'object', description: 'Request body (for POST/PUT/PATCH)' },
          },
          required: ['url'],
        },
      },
    },
  },
  {
    id: 'database_query',
    name: '数据库查询',
    icon: 'database',
    shortDesc: '执行 SQL 查询',
    description: '连接数据库并执行 SQL 查询，返回查询结果',
    category: 'data',
    implemented: true,
    requiredCapabilities: ['function_calling'],
    openaiSchema: {
      type: 'function',
      function: {
        name: 'database_query',
        description: 'Execute a SQL query against a database',
        parameters: {
          type: 'object',
          properties: {
            query: { type: 'string', description: 'SQL query to execute' },
            database: { type: 'string', description: 'Database connection name or URL' },
            params: { type: 'object', description: 'Query parameters for prepared statements' },
          },
          required: ['query'],
        },
      },
    },
  },
  {
    id: 'image_generation',
    name: '图像生成',
    icon: 'image',
    shortDesc: '根据文字描述生成图片',
    description: '调用 AI 图像生成模型，根据文本描述创建图片',
    category: 'media',
    implemented: true,
    requiredCapabilities: ['function_calling', 'image_generation'],
    openaiSchema: {
      type: 'function',
      function: {
        name: 'image_generation',
        description: 'Generate an image from a text description',
        parameters: {
          type: 'object',
          properties: {
            prompt: { type: 'string', description: 'Text description of the image to generate' },
            size: { type: 'string', enum: ['256x256', '512x512', '1024x1024', '1792x1024', '1024x1792'], default: '1024x1024' },
            style: { type: 'string', enum: ['vivid', 'natural'], default: 'vivid' },
          },
          required: ['prompt'],
        },
      },
    },
  },
  {
    id: 'text_analysis',
    name: '文本分析',
    icon: 'analysis',
    shortDesc: '对文本进行结构化分析',
    description: '对输入文本进行摘要、情感分析、关键词提取等处理',
    category: 'analysis',
    implemented: true,
    requiredCapabilities: ['function_calling'],
    openaiSchema: {
      type: 'function',
      function: {
        name: 'text_analysis',
        description: 'Perform structured analysis on text content',
        parameters: {
          type: 'object',
          properties: {
            text: { type: 'string', description: 'Text content to analyze' },
            analysis_type: {
              type: 'string',
              enum: ['summarize', 'sentiment', 'keywords', 'classify', 'translate'],
              description: 'Type of analysis to perform',
            },
            target_language: { type: 'string', description: 'Target language (for translation)' },
          },
          required: ['text', 'analysis_type'],
        },
      },
    },
  },
];

// 快速查找表
const TOOL_MAP = new Map(TOOL_DEFINITIONS.map((t) => [t.id, t]));

/** 获取单个工具的元数据 */
export function getToolMeta(toolId: string): ToolMeta | undefined {
  return TOOL_MAP.get(toolId);
}

/** 获取所有工具的元数据列表 */
export function getAllToolMeta(): ToolMeta[] {
  return TOOL_DEFINITIONS;
}

/** 获取所有工具 ID */
export function getAllToolIds(): string[] {
  return TOOL_DEFINITIONS.map((t) => t.id);
}

/** 获取所有已实现的工具 */
export function getImplementedTools(): ToolMeta[] {
  return TOOL_DEFINITIONS.filter((t) => t.implemented);
}

/** 获取所有未实现的工具 */
export function getStubTools(): ToolMeta[] {
  return TOOL_DEFINITIONS.filter((t) => !t.implemented);
}

/** 将工具列表转为 OpenAI function calling tools 数组 */
export function toOpenAITools(toolIds: string[]): ToolMeta['openaiSchema'][] {
  return toolIds
    .map((id) => TOOL_MAP.get(id))
    .filter((t): t is ToolMeta => !!t)
    .map((t) => t.openaiSchema);
}

/** 将工具列表转为 Anthropic tool_use 格式 */
export function toAnthropicTools(toolIds: string[]): Array<{
  name: string;
  description: string;
  input_schema: Record<string, any>;
}> {
  return toolIds
    .map((id) => TOOL_MAP.get(id))
    .filter((t): t is ToolMeta => !!t)
    .map((t) => ({
      name: t.openaiSchema.function.name,
      description: t.openaiSchema.function.description,
      input_schema: t.openaiSchema.function.parameters,
    }));
}
