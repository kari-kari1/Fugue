/* Fugue TypeScript类型定义 */

// ============ 核心实体类型 ============

export interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  is_active: boolean;
  is_superuser: boolean;
  avatar_url?: string;
  created_at: string;
  updated_at: string;
}

export interface Agent {
  id: string;
  crew_id: string;
  name: string;
  role: string;
  goal: string;
  backstory?: string;
  llm_provider: string;
  llm_model: string;
  temperature: number;
  max_tokens: number;
  allow_delegation: boolean;
  max_iterations: number;
  system_prompt_template?: string;
  tools_config: string[];
  position_x: number;
  position_y: number;
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: string;
  crew_id: string;
  agent_id?: string;
  name: string;
  description: string;
  expected_output?: string;
  output_type: 'text' | 'json' | 'file' | 'code';
  output_file?: string;
  context_task_ids: string[];
  max_retries: number;
  timeout_seconds: number;
  human_review_required: boolean;
  validation_rules: ValidationRule[];
  position_x: number;
  position_y: number;
  config?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface Crew {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  process: 'sequential' | 'parallel' | 'hierarchical' | 'prompt_chain' | 'router' | 'orchestrator' | 'evaluator_optimizer' | 'event_flow' | 'plan_execute';
  approval_mode: 'safe' | 'semi_auto' | 'full_auto';
  max_execution_time: number;
  cost_budget?: number;
  workspace_dir?: string | null;
  project_memory?: string | null;
  metadata: Record<string, unknown>;
  is_template: string;
  template_category?: string;
  agents?: Agent[];
  tasks?: Task[];
  created_at: string;
  updated_at: string;
}

export interface Execution {
  id: string;
  crew_id: string;
  user_id: string;
  status: ExecutionStatus;
  trigger_type: 'manual' | 'scheduled' | 'api' | 'webhook';
  started_at?: string;
  completed_at?: string;
  total_tokens_used: number;
  total_cost_usd: number;
  results: Record<string, unknown>;
  error_log?: string;
  trace: ExecutionTrace[];
  created_at: string;
  updated_at: string;
}

export interface TaskExecution {
  id: string;
  execution_id: string;
  task_id: string;
  agent_id?: string;
  task_name?: string;
  agent_name?: string;
  status: TaskExecutionStatus;
  started_at?: string;
  completed_at?: string;
  input_context: Record<string, unknown>;
  output?: string;
  output_json?: Record<string, unknown>;
  tokens_used: number;
  cost_usd: number;
  retry_count: number;
  error_message?: string;
  thoughts: AgentThought[];
  tool_calls: ToolCall[];
  created_at: string;
  updated_at: string;
}

// ============ 枚举类型 ============

export type ExecutionStatus = 'pending' | 'running' | 'paused' | 'waiting_review' | 'completed' | 'failed' | 'cancelled';
export type TaskExecutionStatus = 'pending' | 'running' | 'completed' | 'failed' | 'skipped' | 'retrying';

// ============ 配置类型 ============

export interface LLMConfig {
  provider: 'openai' | 'anthropic' | 'google' | 'local' | 'custom';
  model: string;
  api_key_id?: string;
  base_url?: string;
  temperature: number;
  max_tokens: number;
  top_p: number;
  streaming: boolean;
  timeout_seconds: number;
}

export interface Tool {
  id: string;
  name: string;
  description: string;
  type: 'builtin' | 'mcp' | 'custom';
  permissions: 'safe' | 'caution' | 'dangerous';
  input_schema: JSONSchema;
  output_schema: JSONSchema;
  config: Record<string, unknown>;
}

export interface MemoryConfig {
  short_term: boolean;
  long_term: boolean;
  knowledge_base_ids: string[];
  vector_store: 'chromadb' | 'pinecone' | 'local';
  retrieval_strategy: 'semantic' | 'keyword' | 'hybrid';
  top_k: number;
}

export interface ValidationRule {
  type: string;
  value: unknown;
  message?: string;
}

export interface JSONSchema {
  type: string;
  properties?: Record<string, JSONSchema>;
  required?: string[];
  [key: string]: unknown;
}

// ============ 执行相关类型 ============

export interface ExecutionTrace {
  timestamp: string;
  event_type: string;
  agent_name?: string;
  task_name?: string;
  data: Record<string, unknown>;
}

export const TRACE_EVENT_LABELS: Record<string, string> = {
  'crew.started': '工作流启动',
  'crew.completed': '工作流完成',
  'task.started': '任务开始',
  'task.completed': '任务完成',
  'task.skipped': '任务跳过',
  'task.failed': '任务失败',
  'agent.thinking': 'Agent思考',
  'agent.tool_call': '工具调用',
  'agent.command': 'Agent命令',
  'agent.handoff': 'Agent交接',
  'agent.warning': 'Agent警告',
  'orchestrator.started': '编排器启动',
  'orchestrator.completed': '编排器完成',
};

export interface AgentThought {
  timestamp: string;
  content: string;
  type: 'thinking' | 'reasoning' | 'planning';
}

export interface ToolCall {
  timestamp: string;
  tool_name: string;
  input: Record<string, unknown>;
  output?: unknown;
  duration_ms?: number;
  error?: string;
}

// ============ WebSocket消息类型 ============

export interface WSMessage {
  type: WSMessageType;
  timestamp: string;
  data: Record<string, unknown>;
}

export type WSMessageType =
  | 'agent.thinking'
  | 'agent.tool_call'
  | 'agent.output'
  | 'agent.error'
  | 'task.started'
  | 'task.completed'
  | 'task.failed'
  | 'task.retrying'
  | 'crew.started'
  | 'crew.completed'
  | 'crew.failed'
  | 'crew.paused'
  | 'crew.resumed'
  | 'system.cost_update'
  | 'system.progress'
  | 'system.heartbeat'
  | 'system.warning'
  | 'system.review';

// ============ API响应类型 ============

export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

// ============ ReactFlow节点类型 ============

export interface AgentNodeData {
  name: string;
  role: string;
  llm_provider: string;
  llm_model: string;
  tools: string[];
  status?: ExecutionStatus;
  agent?: Agent;
}

/** 任务附件 — 预绑定的本地文件 */
export interface TaskAttachment {
  name: string;
  path: string;
  size: number;
  mime_type: string;
  added_at: string;
}

export interface TaskNodeData {
  name: string;
  description: string;
  output_type: string;
  agent_id?: string;
  agent_name?: string;
  sub_crew_id?: string;
  status?: TaskExecutionStatus;
  task?: Task;
  attachments?: TaskAttachment[];
}

export interface ConditionNodeData {
  name: string;
  expression: string;
  description?: string;
  true_branch_task_ids: string[];
  false_branch_task_ids: string[];
  true_branch?: string;  // 描述性文本（仅前端显示）
  false_branch?: string;  // 描述性文本（仅前端显示）
}

export interface LoopNodeData {
  name: string;
  maxIterations: number;
  condition?: string;
  exitOnFailure?: boolean;
  loopBodyTaskIds?: string[];
}

export interface HumanReviewNodeData {
  name: string;
  reviewType: 'approval' | 'input' | 'selection';
  prompt: string;
  options?: string[];
  timeoutSeconds?: number;
  timeoutAction?: 'approve' | 'reject' | 'skip';
  notificationChannels?: string[];
}

export interface StartNodeData {
  label: string;
}

export interface EndNodeData {
  label: string;
}

// ── Anthropic 五种工作流模式节点 ──────────────────────────

export interface RouterNodeData {
  name: string;
  description?: string;
  routes: Array<{
    condition: string;        // 条件表达式
    target_agent_id?: string; // 目标Agent
    label: string;            // 分支标签
  }>;
}

export interface ParallelNodeData {
  name: string;
  description?: string;
  max_concurrency?: number;   // 最大并发数
  mode: 'sectioning' | 'voting';  // 分段或投票
  branches: string[];         // 子分支任务ID列表
}

export interface OrchestratorNodeData {
  name: string;
  description?: string;
  worker_agent_ids: string[];  // 可用的Worker Agent
  task_ledger?: string;        // 任务账本（任务分配记录）
}

export interface EvaluatorNodeData {
  name: string;
  description?: string;
  max_iterations: number;      // 最大优化轮次
  evaluation_criteria: string; // 评估标准
  optimizer_agent_id?: string; // 优化Agent
}

export interface PromptChainNodeData {
  name: string;
  description?: string;
  chain_tasks: string[];       // 链式任务ID序列
  pass_output: boolean;        // 是否将前一个输出传递给下一个输入
}

// ============ 知识库类型 ============

export interface KnowledgeBase {
  id: string;
  name: string;
  description?: string;
  document_count: number;
  chunk_count: number;
}

export interface AgentKnowledgeMapping {
  id: string;
  agent_id: string;
  knowledge_base_id: string;
}

// ============ Event Flow 类型 ============

export interface FlowNodeData {
  name: string;
  event_name?: string;    // @start/@listen 事件名
  flowType: 'start' | 'listen' | 'router_event';
  condition?: string;     // @router 条件表达式
  description?: string;
}

export interface FlowEvent {
  name: string;
  data?: unknown;
  source?: string;
}

// ============ RAG / Memory 增强类型 ============

export interface MemoryConfigFull {
  short_term_enabled: boolean;
  short_term_window: number;
  long_term_enabled: boolean;
  vector_store_type: string;
  retrieval_strategy: 'semantic' | 'keyword' | 'hybrid';
  top_k: number;
  chunk_size: number;
  chunk_overlap: number;
  auto_index_on_complete: boolean;
}
