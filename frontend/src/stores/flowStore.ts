/* ReactFlow画布状态管理 */

import { create, type StateCreator } from 'zustand';
import { temporal } from 'zundo';
import {
  type Node,
  type Edge,
  type OnNodesChange,
  type OnEdgesChange,
  type OnConnect,
  type Connection,
  type NodeChange,
  type EdgeChange,
  applyNodeChanges,
  applyEdgeChanges,
  addEdge,
} from '@xyflow/react';
import type { AgentNodeData, TaskNodeData, ConditionNodeData } from '../types';
import { generateId } from '../lib/utils';

interface FlowState {
  nodes: Node[];
  edges: Edge[];
  selectedNode: Node | null;
  clipboard: { nodes: Node[]; edges: Edge[] } | null;

  // Actions
  onNodesChange: OnNodesChange;
  onEdgesChange: OnEdgesChange;
  onConnect: OnConnect;
  addNode: (node: Node) => void;
  removeNode: (nodeId: string) => void;
  updateNodeData: (nodeId: string, data: Partial<AgentNodeData | TaskNodeData | ConditionNodeData>) => void;
  setSelectedNode: (node: Node | null) => void;
  setNodes: (nodes: Node[]) => void;
  setEdges: (edges: Edge[]) => void;
  clearFlow: () => void;
  loadFlow: (nodes: Node[], edges: Edge[]) => void;

  // 剪贴板
  copySelected: () => void;
  paste: () => void;
}

// 节点类型分类集合
const EVENT_FLOW_TYPES = new Set(['start', 'listen', 'router_event']);
const WORKFLOW_PATTERN_TYPES = new Set(['router', 'parallel_flow', 'orchestrator', 'evaluator', 'prompt_chain']);
const ALL_FLOW_TYPES = new Set([...EVENT_FLOW_TYPES, ...WORKFLOW_PATTERN_TYPES]);

// 验证连线是否合法
function isValidConnection(connection: Connection, edges: Edge[], nodes: Node[]): boolean {
  if (!connection.source || !connection.target) return false;
  // 禁止自连接
  if (connection.source === connection.target) return false;

  // 禁止重复连线
  const exists = edges.some(
    (e) => e.source === connection.source && e.target === connection.target
  );
  if (exists) return false;

  // 获取源和目标节点类型
  const sourceNode = nodes.find((n) => n.id === connection.source);
  const targetNode = nodes.find((n) => n.id === connection.target);
  if (!sourceNode || !targetNode) return false;

  const sourceType = sourceNode.type;
  const targetType = targetNode.type;

  // agent 不能作为目标
  if (targetType === 'agent') return false;
  if (sourceType === 'task' && targetType === 'agent') return false;

  // agent 不能直接连接到事件流或工作流模式节点
  if (sourceType === 'agent' && ALL_FLOW_TYPES.has(targetType || '')) return false;

  // Event Flow 节点：只能连接到 task 或其他事件流节点
  const isSourceEventFlow = EVENT_FLOW_TYPES.has(sourceType || '');
  const isTargetEventFlow = EVENT_FLOW_TYPES.has(targetType || '');
  if (isSourceEventFlow || isTargetEventFlow) {
    if (targetType === 'start') return false; // start 不能作为目标
    // 只允许事件流↔事件流 或 事件流→task
    const validTarget = isTargetEventFlow || targetType === 'task';
    const validSource = isSourceEventFlow || sourceType === 'task';
    if (isSourceEventFlow && !validTarget) return false;
    if (isTargetEventFlow && !validSource) return false;
    return true;
  }

  // 工作流模式节点：禁止双向环
  const isSourceWP = WORKFLOW_PATTERN_TYPES.has(sourceType || '');
  const isTargetWP = WORKFLOW_PATTERN_TYPES.has(targetType || '');
  if (isSourceWP || isTargetWP) {
    const reverseExists = edges.some(
      (e) => e.source === connection.target && e.target === connection.source
    );
    if (reverseExists) return false;
    return true;
  }

  // 禁止 task→task 形成环（简化检测：A→B 时禁止 B→A）
  if (sourceType === 'task' && targetType === 'task') {
    const reverseExists = edges.some(
      (e) => e.source === connection.target && e.target === connection.source
    );
    if (reverseExists) return false;
  }

  return true;
}

export interface DAGValidationError {
  type: 'cycle' | 'missing_agent' | 'disconnected' | 'invalid_connection' | 'missing_output';
  severity: 'error' | 'warning';
  message: string;
  nodeIds?: string[];
  edgeIds?: string[];
}

export function validateDAG(nodes: Node[], edges: Edge[]): {
  valid: boolean;
  errors: DAGValidationError[];
  warnings: DAGValidationError[];
} {
  const errors: DAGValidationError[] = [];
  const warnings: DAGValidationError[] = [];
  const taskNodes = nodes.filter((n) => n.type === 'task');
  const agentNodes = nodes.filter((n) => n.type === 'agent');

  // 检查是否有任务节点
  if (taskNodes.length === 0) {
    errors.push({
      type: 'missing_output',
      severity: 'error',
      message: '没有任务节点',
    });
  }

  // 检查是否有Agent节点
  if (agentNodes.length === 0) {
    errors.push({
      type: 'missing_agent',
      severity: 'error',
      message: '没有Agent节点',
    });
  }

  // 检查每个task是否连接了agent
  for (const task of taskNodes) {
    const hasAgent = edges.some((e) => {
      if (e.target !== task.id) return false;
      const sourceNode = nodes.find((n) => n.id === e.source);
      return sourceNode?.type === 'agent';
    });
    if (!hasAgent) {
      errors.push({
        type: 'missing_agent',
        severity: 'error',
        message: `任务"${(task.data as unknown as TaskNodeData).name || task.id}"未连接Agent`,
        nodeIds: [task.id],
      });
    }
  }

  // 检查孤立节点
  const connectedNodeIds = new Set<string>();
  edges.forEach((e) => {
    connectedNodeIds.add(e.source);
    connectedNodeIds.add(e.target);
  });

  const disconnectedNodes = nodes.filter((n) => !connectedNodeIds.has(n.id));
  if (disconnectedNodes.length > 0) {
    warnings.push({
      type: 'disconnected',
      severity: 'warning',
      message: `${disconnectedNodes.length} 个节点未连接`,
      nodeIds: disconnectedNodes.map((n) => n.id),
    });
  }

  // 环检测（Kahn算法）
  const taskIds = new Set(taskNodes.map((n) => n.id));
  const taskEdges = edges.filter(
    (e) => taskIds.has(e.source) && taskIds.has(e.target)
  );

  const inDegree: Record<string, number> = {};
  const dependents: Record<string, string[]> = {};

  for (const id of taskIds) {
    inDegree[id] = 0;
    dependents[id] = [];
  }

  for (const e of taskEdges) {
    inDegree[e.target] = (inDegree[e.target] || 0) + 1;
    dependents[e.source].push(e.target);
  }

  const queue = Object.keys(inDegree).filter((id) => inDegree[id] === 0);
  let visited = 0;

  while (queue.length) {
    const node = queue.shift()!;
    visited++;
    for (const dep of dependents[node]) {
      inDegree[dep]--;
      if (inDegree[dep] === 0) queue.push(dep);
    }
  }

  if (visited < taskNodes.length) {
    // 找出环中的节点
    const inCycle = Object.keys(inDegree).filter((id) => inDegree[id] > 0);
    errors.push({
      type: 'cycle',
      severity: 'error',
      message: `检测到循环依赖，涉及 ${inCycle.length} 个任务`,
      nodeIds: inCycle,
      edgeIds: taskEdges
        .filter((e) => inCycle.includes(e.source) && inCycle.includes(e.target))
        .map((e) => e.id),
    });
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings,
  };
}

const flowStoreCreator: StateCreator<FlowState> = (set, get) => ({
  nodes: [],
  edges: [],
  selectedNode: null,
  clipboard: null,

  onNodesChange: (changes: NodeChange[]) => {
    set({
      nodes: applyNodeChanges(changes, get().nodes),
    });
  },

  onEdgesChange: (changes: EdgeChange[]) => {
    set({
      edges: applyEdgeChanges(changes, get().edges),
    });
  },

  onConnect: (connection: Connection) => {
    const { edges, nodes } = get();
    if (!isValidConnection(connection, edges, nodes)) return;

    const sourceNode = nodes.find((n) => n.id === connection.source);
    const isAgentSource = sourceNode?.type === 'agent';

    set({
      edges: addEdge(
        {
          ...connection,
          type: 'particle',
          animated: true,
          data: { color: isAgentSource ? 'cyan' : 'green' },
        },
        edges
      ),
    });
  },

  addNode: (node: Node) => {
    set({
      nodes: [...get().nodes, node],
    });
  },

  removeNode: (nodeId: string) => {
    set({
      nodes: get().nodes.filter((n) => n.id !== nodeId),
      edges: get().edges.filter((e) => e.source !== nodeId && e.target !== nodeId),
      selectedNode: get().selectedNode?.id === nodeId ? null : get().selectedNode,
    });
  },

  updateNodeData: (nodeId: string, data: Partial<AgentNodeData | TaskNodeData | ConditionNodeData>) => {
    const updatedNodes = get().nodes.map((node) =>
      node.id === nodeId
        ? { ...node, data: { ...node.data, ...data } }
        : node
    );
    // 同步更新selectedNode，避免属性面板显示旧数据
    const updatedSelected = get().selectedNode?.id === nodeId
      ? updatedNodes.find((n) => n.id === nodeId) || null
      : get().selectedNode;

    set({
      nodes: updatedNodes,
      selectedNode: updatedSelected,
    });
  },

  setSelectedNode: (node: Node | null) => {
    set({ selectedNode: node });
  },

  setNodes: (nodes: Node[]) => {
    if (!Array.isArray(nodes)) {
      console.error('[flowStore] setNodes called with non-array value:', typeof nodes, nodes);
      return;
    }
    set({ nodes });
  },

  setEdges: (edges: Edge[]) => {
    if (!Array.isArray(edges)) {
      console.error('[flowStore] setEdges called with non-array value:', typeof edges, edges);
      return;
    }
    set({ edges });
  },

  clearFlow: () => {
    set({
      nodes: [],
      edges: [],
      selectedNode: null,
    });
  },

  loadFlow: (nodes: Node[], edges: Edge[]) => {
    set({
      nodes: Array.isArray(nodes) ? nodes : [],
      edges: Array.isArray(edges) ? edges : [],
      selectedNode: null,
    });
  },

  // 复制选中节点及其相关边
  copySelected: () => {
    const { selectedNode, nodes, edges } = get();
    if (!selectedNode) return;

    // 收集所有选中节点（当前仅支持单选）
    const selectedIds = new Set([selectedNode.id]);
    const copiedNodes = nodes.filter((n) => selectedIds.has(n.id));
    const copiedEdges = edges.filter(
      (e) => selectedIds.has(e.source) && selectedIds.has(e.target)
    );

    set({ clipboard: { nodes: copiedNodes, edges: copiedEdges } });
  },

  // 粘贴剪贴板内容，生成新ID并偏移位置
  paste: () => {
    const { clipboard, nodes, edges } = get();
    if (!clipboard || clipboard.nodes.length === 0) return;

    // 为粘贴的节点生成新ID映射
    const idMap: Record<string, string> = {};
    const offset = 40; // 粘贴偏移量

    const newNodes = clipboard.nodes.map((node) => {
      const newId = `${node.type}-${generateId()}`;
      idMap[node.id] = newId;
      return {
        ...node,
        id: newId,
        position: {
          x: node.position.x + offset,
          y: node.position.y + offset,
        },
        selected: false,
      };
    });

    // 为粘贴的边生成新ID并更新引用
    const newEdges = clipboard.edges.map((edge) => {
      const newSource = idMap[edge.source] || edge.source;
      const newTarget = idMap[edge.target] || edge.target;
      return {
        ...edge,
        id: `edge-${generateId()}`,
        source: newSource,
        target: newTarget,
      };
    });

    set({
      nodes: [...nodes, ...newNodes],
      edges: [...edges, ...newEdges],
      selectedNode: newNodes[0] || null,
    });
  },
});

export const useFlowStore = create<FlowState>()(temporal(flowStoreCreator, {
  limit: 50,
  equality: (pastState: FlowState, currentState: FlowState) =>
    JSON.stringify(pastState) === JSON.stringify(currentState),
}));
