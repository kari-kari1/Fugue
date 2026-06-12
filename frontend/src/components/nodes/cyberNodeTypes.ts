import type { NodeTypes } from '@xyflow/react';
import CyberNode from '../cyber/CyberNode';
import { WorkflowPatternNode } from '../nodes/WorkflowPatternNode';
import EventFlowNode from '../nodes/EventFlowNode';

export const cyberNodeTypes: NodeTypes = {
  agent: CyberNode,
  task: CyberNode,
  condition: CyberNode,
  loop: CyberNode,
  humanReview: CyberNode,
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
