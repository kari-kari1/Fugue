/* 节点组件导出 */

import type { NodeTypes } from '@xyflow/react';
import AgentNode from './AgentNode';
import TaskNode from './TaskNode';
import ConditionNode from './ConditionNode';
import LoopNode from './LoopNode';
import HumanReviewNode from './HumanReviewNode';
import { WorkflowPatternNode } from './WorkflowPatternNode';
import EventFlowNode from './EventFlowNode';

// 注册自定义节点类型
export const nodeTypes: NodeTypes = {
  agent: AgentNode,
  task: TaskNode,
  condition: ConditionNode,
  loop: LoopNode,
  humanReview: HumanReviewNode,
  // Anthropic 五种工作流模式节点
  router: WorkflowPatternNode,
  parallel_flow: WorkflowPatternNode,
  orchestrator: WorkflowPatternNode,
  evaluator: WorkflowPatternNode,
  prompt_chain: WorkflowPatternNode,
  // Event Flow 事件驱动节点
  start: EventFlowNode,
  listen: EventFlowNode,
  router_event: EventFlowNode,
};

export { default as AgentNode } from './AgentNode';
export { default as TaskNode } from './TaskNode';
export { default as ConditionNode } from './ConditionNode';
export { default as LoopNode } from './LoopNode';
export { default as HumanReviewNode } from './HumanReviewNode';
export { WorkflowPatternNode } from './WorkflowPatternNode';
export { default as EventFlowNode } from './EventFlowNode';
