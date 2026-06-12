/* Iteration 相关类型定义 */

export interface Iteration {
  id: string;
  execution_id: string;
  iteration_number: number;
  feedback: string;
  mode: 'reexecute' | 'incremental';
  status: 'pending' | 'running' | 'completed' | 'failed';
  refined_output?: string;
  tokens_used: number;
  cost_usd: number;
  error_message?: string;
  context_snapshot?: Record<string, any>;
  created_at: string;
  updated_at?: string;
  completed_at?: string;
}

export interface IterationCreate {
  feedback: string;
  mode: 'reexecute' | 'incremental';
}

export interface IterationListResponse {
  iterations: Iteration[];
  total: number;
}
