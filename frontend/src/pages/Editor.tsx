/* 工作流编辑器页面 - iOS Liquid Glass (Light) */

import React, { useCallback, useRef, useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  BackgroundVariant,
  type Node,
  type Edge,
  useReactFlow,
  ReactFlowProvider,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Save, Play, ChevronDown, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';

import { nodeTypes } from '../components/nodes';
import { particleEdgeTypes } from '../components/edges';
import { cyberNodeTypes } from '../components/nodes/cyberNodeTypes';
import { cyberEdgeTypes } from '../components/edges/cyberEdgeTypes';
import NodeToolbar from '../components/editor/NodeToolbar';
import PropertyPanel from '../components/editor/PropertyPanel';
import { ShortcutsHelp } from '../components/editor/ShortcutsHelp';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';
import { useFlowStore, validateDAG, type DAGValidationError } from '../stores/flowStore';
import { DAGValidationPanel } from '../components/editor/DAGValidationPanel';
import { useThemeStore } from '../stores/themeStore';
import { TunnelTransition } from '../components/motion/TunnelTransition';
import { crewsApi } from '../api/crews';
import { agentsApi } from '../api/agents';
import { tasksApi } from '../api/tasks';
import { executionsApi } from '../api/executions';
import { generateId } from '../lib/utils';
import { getLLMKeys, getLLMBaseUrls } from '../lib/llmKeys';
import type { AgentNodeData, TaskNodeData } from '../types';

// ============ FlowCanvas ============

const FlowCanvas: React.FC<{ crewId: string }> = ({ crewId }) => {
  const { screenToFlowPosition, zoomIn, zoomOut, fitView } = useReactFlow();
  const queryClient = useQueryClient();
  const loadedCrewId = useRef<string | null>(null);

  const {
    nodes, edges,
    onNodesChange, onEdgesChange, onConnect,
    addNode, removeNode, setSelectedNode, loadFlow, clearFlow,
    copySelected, paste,
  } = useFlowStore();

  // 动态类型切换: 静态态→标准类型, 动态态→赛博类型
  const themeMode = useThemeStore((s) => s.mode);
  const activeNodeTypes = themeMode === 'static' ? nodeTypes : cyberNodeTypes;
  const activeEdgeTypes = themeMode === 'static' ? particleEdgeTypes : cyberEdgeTypes;

  const [isDirty, setIsDirty] = useState(false);
  const [validationErrors, setValidationErrors] = useState<DAGValidationError[]>([]);
  const [validationWarnings, setValidationWarnings] = useState<DAGValidationError[]>([]);
  const [showValidationPanel, setShowValidationPanel] = useState(true);

  useEffect(() => {
    loadedCrewId.current = null;
    clearFlow();
    setIsDirty(false);
  }, [crewId, clearFlow]);

  const { data: crew, isLoading: crewLoading } = useQuery({
    queryKey: ['crew', crewId],
    queryFn: () => crewsApi.get(crewId),
  });

  const { data: agents } = useQuery({
    queryKey: ['agents', crewId],
    queryFn: () => crewsApi.getAgents(crewId),
    enabled: !!crewId,
  });

  const { data: tasks } = useQuery({
    queryKey: ['tasks', crewId],
    queryFn: () => crewsApi.getTasks(crewId),
    enabled: !!crewId,
  });

  useEffect(() => {
    if (!agents || !tasks) return;
    if (loadedCrewId.current === crewId) return;

    const flowNodes: Node[] = [
      ...agents.map((agent) => ({
        id: `agent-${agent.id}`,
        type: 'agent' as const,
        position: { x: agent.position_x || 0, y: agent.position_y || 0 },
        data: {
          name: agent.name, role: agent.role,
          llm_provider: agent.llm_provider, llm_model: agent.llm_model,
          tools: agent.tools_config || [], agent,
        } as unknown as Record<string, unknown>,
      })),
      ...tasks.map((task) => ({
        id: `task-${task.id}`,
        type: 'task' as const,
        position: { x: task.position_x || 0, y: task.position_y || 0 },
        data: {
          name: task.name, description: task.description,
          output_type: task.output_type, agent_id: task.agent_id,
          agent_name: task.agent_id ? agents.find((a) => a.id === task.agent_id)?.name : undefined,
          attachments: (task as any).config?.attachments || [],
          task,
        } as unknown as Record<string, unknown>,
      })),
    ];

    const flowEdges: Edge[] = [];
    tasks.forEach((task) => {
      if (task.context_task_ids?.length > 0) {
        task.context_task_ids.forEach((ctxTaskId) => {
          flowEdges.push({
            id: `edge-${ctxTaskId}-${task.id}`,
            source: `task-${ctxTaskId}`, target: `task-${task.id}`,
            type: 'particle', animated: true, data: { color: 'green' },
          });
        });
      }
      if (task.agent_id) {
        flowEdges.push({
          id: `edge-agent-${task.agent_id}-task-${task.id}`,
          source: `agent-${task.agent_id}`, target: `task-${task.id}`,
          type: 'particle', animated: true, data: { color: 'cyan' },
        });
      }
    });

    clearFlow();
    loadFlow(flowNodes, flowEdges);
    loadedCrewId.current = crewId;
  }, [crewId, agents, tasks, loadFlow, clearFlow]);

  useEffect(() => {
    const timer = setInterval(() => {
      const { nodes: n, edges: e } = useFlowStore.getState();
      if (Array.isArray(n) && n.length > 0) {
        localStorage.setItem(`flow-draft-${crewId}`, JSON.stringify({ nodes: n, edges: e, savedAt: Date.now() }));
      }
    }, 30000);
    return () => clearInterval(timer);
  }, [crewId]);

  const saveMutation = useMutation({
    mutationFn: async () => {
      const taskAgentMap: Record<string, string> = {};
      const taskDepsMap: Record<string, string[]> = {};
      edges.forEach((edge) => {
        const sourceNode = nodes.find(n => n.id === edge.source);
        const targetNode = nodes.find(n => n.id === edge.target);

        if (sourceNode?.type === 'agent' && targetNode?.type === 'task') {
          taskAgentMap[edge.target] = edge.source;
        }
        if (sourceNode?.type === 'task' && targetNode?.type === 'task') {
          if (!taskDepsMap[edge.target]) taskDepsMap[edge.target] = [];
          taskDepsMap[edge.target].push(edge.source);
        }
      });

      const agentNodes = nodes.filter((n) => n.type === 'agent');
      const taskNodes = nodes.filter((n) => n.type === 'task');
      const failures: string[] = [];
      const agentIdMap: Record<string, string> = {};
      const createdAgents: Array<{ nodeId: string; agent: any }> = [];

      for (const node of agentNodes) {
        const d = node.data as unknown as AgentNodeData;
        try {
          if (d.agent) {
            const updated = await agentsApi.update(d.agent.id, {
              name: d.name, role: d.role, llm_provider: d.llm_provider, llm_model: d.llm_model,
              tools_config: d.tools, position_x: node.position.x, position_y: node.position.y,
            });
            agentIdMap[node.id] = updated.id;
            createdAgents.push({ nodeId: node.id, agent: updated });
          } else {
            const created = await agentsApi.create({
              crew_id: crewId, name: d.name || 'Agent', role: d.role || '助手',
              goal: d.role ? `作为${d.role}完成指定任务` : '完成指定任务',
              llm_provider: d.llm_provider || 'openai', llm_model: d.llm_model || 'gpt-4o',
              tools_config: d.tools || [], position_x: node.position.x, position_y: node.position.y,
            });
            agentIdMap[node.id] = created.id;
            createdAgents.push({ nodeId: node.id, agent: created });
          }
        } catch (err: any) {
          failures.push(`Agent "${d.name}": ${err.response?.data?.detail || err.message}`);
        }
      }

      const taskIdMap: Record<string, string> = {};
      for (const node of taskNodes) {
        const d = node.data as unknown as TaskNodeData;
        const t = d.task;
        const agentNodeId = taskAgentMap[node.id];
        const agentId = (agentNodeId ? agentIdMap[agentNodeId] : null) || d.agent_id || undefined;
        const depNodeIds = taskDepsMap[node.id] || [];
        const rawDeps = depNodeIds.length > 0 ? depNodeIds : (t?.context_task_ids || []);
        const deps = rawDeps.map((depId: string) => taskIdMap[depId] || depId).filter(Boolean);

        try {
          const taskConfig = d.attachments?.length ? { attachments: d.attachments } : undefined;
          if (t) {
            await tasksApi.update(t.id, {
              name: d.name, description: d.description, output_type: d.output_type as any,
              agent_id: agentId, context_task_ids: deps,
              position_x: node.position.x, position_y: node.position.y,
              config: taskConfig,
            });
            taskIdMap[node.id] = t.id;
          } else {
            const created = await tasksApi.create({
              crew_id: crewId, name: d.name || 'Task', description: d.description || '待填写任务描述',
              output_type: d.output_type || 'text', agent_id: agentId, context_task_ids: deps,
              position_x: node.position.x, position_y: node.position.y,
              config: taskConfig,
            });
            taskIdMap[node.id] = created.id;
          }
        } catch (err: any) {
          failures.push(`Task "${d.name}": ${err.response?.data?.detail || err.message}`);
        }
      }

      const keptAgentIds = new Set(Object.values(agentIdMap));
      const keptTaskIds = new Set(Object.values(taskIdMap));
      try {
        const [backendAgents, backendTasks] = await Promise.all([
          crewsApi.getAgents(crewId), crewsApi.getTasks(crewId),
        ]);
        for (const a of backendAgents) { if (!keptAgentIds.has(a.id)) await agentsApi.delete(a.id).catch(() => {}); }
        for (const t of backendTasks) { if (!keptTaskIds.has(t.id)) await tasksApi.delete(t.id).catch(() => {}); }
      } catch { /* ignore cleanup failures */ }

      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['agents', crewId] }),
        queryClient.invalidateQueries({ queryKey: ['tasks', crewId] }),
        queryClient.invalidateQueries({ queryKey: ['crews'] }),
        queryClient.invalidateQueries({ queryKey: ['crew', crewId] }),
      ]);
      loadedCrewId.current = null;

      // 更新节点中的 agent 引用，使知识库关联在保存后即可用
      if (createdAgents.length > 0) {
        const { nodes: currentNodes, setNodes } = useFlowStore.getState();
        setNodes(currentNodes.map(n => {
          const hit = createdAgents.find(ca => ca.nodeId === n.id);
          return hit ? { ...n, data: { ...n.data, agent: hit.agent } } : n;
        }));
      }

      if (failures.length > 0) throw new Error(`保存失败:\n${failures.join('\n')}`);
      localStorage.removeItem(`flow-draft-${crewId}`);
    },
    onSuccess: () => { setIsDirty(false); toast.success('保存成功'); },
    onError: (error: any) => { toast.error('保存失败: ' + (error.message || '未知错误')); },
  });

  useEffect(() => {
    if (loadedCrewId.current !== crewId) return;
    if (saveMutation.isPending) return;
    if (nodes.length > 0 || edges.length > 0) setIsDirty(true);
  }, [nodes, edges, crewId, saveMutation.isPending]);

  // 实时校验
  useEffect(() => {
    const { errors, warnings } = validateDAG(nodes, edges);
    setValidationErrors(errors);
    setValidationWarnings(warnings);
  }, [nodes, edges]);

  const [editingName, setEditingName] = useState(false);
  const [crewName, setCrewName] = useState('');
  const [crewProcess, setCrewProcess] = useState('sequential');
  const [approvalMode, setApprovalMode] = useState('semi_auto');
  const [showApprovalDropdown, setShowApprovalDropdown] = useState(false);
  const [showApprovalConfirm, setShowApprovalConfirm] = useState(false);
  const [workspaceDir, setWorkspaceDir] = useState<string | null>(null);

  useEffect(() => {
    if (crew) { setCrewName(crew.name); setCrewProcess(crew.process || 'sequential'); setApprovalMode((crew as any).approval_mode || 'semi_auto'); setWorkspaceDir((crew as any).workspace_dir || null); }
  }, [crew]);

  const updateCrewMutation = useMutation({
    mutationFn: (data: { name?: string; process?: 'sequential' | 'parallel' | 'hierarchical' | 'prompt_chain' | 'router' | 'orchestrator' | 'evaluator_optimizer' | 'event_flow' | 'plan_execute'; approval_mode?: 'safe' | 'semi_auto' | 'full_auto'; workspace_dir?: string | null }) => crewsApi.update(crewId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crew', crewId] });
      queryClient.invalidateQueries({ queryKey: ['crews'] });
    },
  });

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      const type = event.dataTransfer.getData('application/reactflow-type');
      if (!type) return;
      const position = screenToFlowPosition({ x: event.clientX, y: event.clientY });
      const id = `${type}-${generateId()}`;
      if (type === 'agent') {
        addNode({ id, type: 'agent', position, data: { name: '新Agent', role: '助手', llm_provider: 'openai', llm_model: 'gpt-4o', tools: [] } as unknown as Record<string, unknown> });
      } else if (type === 'task') {
        addNode({ id, type: 'task', position, data: { name: '新任务', description: '', output_type: 'text' } as unknown as Record<string, unknown> });
      } else if (type === 'condition') {
        addNode({ id, type: 'condition', position, data: { name: '条件判断', expression: '', true_branch: '', false_branch: '', true_branch_task_ids: [], false_branch_task_ids: [] } as unknown as Record<string, unknown> });
      } else if (type === 'loop') {
        addNode({ id, type: 'loop', position, data: { name: '循环节点', maxIterations: 10, condition: '', exitOnFailure: true, loopBodyTaskIds: [] } as unknown as Record<string, unknown> });
      } else if (type === 'humanReview') {
        addNode({ id, type: 'humanReview', position, data: { name: '人工审核', reviewType: 'approval', prompt: '', options: [], timeoutSeconds: undefined, timeoutAction: 'reject' } as unknown as Record<string, unknown> });
      } else if (type === 'router') {
        addNode({ id, type: 'router', position, data: { name: 'Router', patternType: 'router', routes: [], description: '' } as unknown as Record<string, unknown> });
      } else if (type === 'parallel_flow') {
        addNode({ id, type: 'parallel_flow', position, data: { name: 'Parallel', patternType: 'parallel', mode: 'sectioning', branches: [], description: '' } as unknown as Record<string, unknown> });
      } else if (type === 'orchestrator') {
        addNode({ id, type: 'orchestrator', position, data: { name: 'Orchestrator', patternType: 'orchestrator', worker_agent_ids: [], description: '' } as unknown as Record<string, unknown> });
      } else if (type === 'evaluator') {
        addNode({ id, type: 'evaluator', position, data: { name: 'Evaluator', patternType: 'evaluator', max_iterations: 5, evaluation_criteria: '', description: '' } as unknown as Record<string, unknown> });
      } else if (type === 'prompt_chain') {
        addNode({ id, type: 'prompt_chain', position, data: { name: 'Prompt Chain', patternType: 'prompt_chain', chain_tasks: [], pass_output: true, description: '' } as unknown as Record<string, unknown> });
      } else if (type === 'start') {
        addNode({ id, type: 'start', position, data: { name: '@start', flowType: 'start', event_name: 'on_start', description: '' } as unknown as Record<string, unknown> });
      } else if (type === 'listen') {
        addNode({ id, type: 'listen', position, data: { name: '@listen', flowType: 'listen', event_name: '', description: '' } as unknown as Record<string, unknown> });
      } else if (type === 'router_event') {
        addNode({ id, type: 'router_event', position, data: { name: '@router', flowType: 'router_event', event_name: '', condition: '', description: '' } as unknown as Record<string, unknown> });
      }
    },
    [screenToFlowPosition, addNode]
  );

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => setSelectedNode(node), [setSelectedNode]);
  const onPaneClick = useCallback(() => setSelectedNode(null), [setSelectedNode]);

  const handleValidationErrorClick = useCallback((nodeId: string) => {
    const node = nodes.find((n) => n.id === nodeId);
    if (node) {
      setSelectedNode(node);
      fitView({ nodes: [node], duration: 500, padding: 0.5 });
    }
  }, [nodes, setSelectedNode, fitView]);

  // 快捷键系统
  const temporalStore = useFlowStore.temporal;

  useKeyboardShortcuts({
    onSave: () => saveMutation.mutate(),
    onUndo: () => temporalStore.getState().undo(),
    onRedo: () => temporalStore.getState().redo(),
    onCopy: () => copySelected(),
    onPaste: () => paste(),
    onDelete: () => {
      const { selectedNode: sel } = useFlowStore.getState();
      if (sel) removeNode(sel.id);
    },
    onSelectAll: () => {
      // 全选：通过设置所有节点的 selected 属性实现多选视觉效果
      const { nodes: allNodes, setNodes } = useFlowStore.getState();
      if (allNodes.length > 0) {
        setNodes(allNodes.map(node => ({ ...node, selected: true })));
        setSelectedNode(allNodes[0]);
      }
    },
    onZoomIn: () => zoomIn(),
    onZoomOut: () => zoomOut(),
    onZoomFit: () => fitView(),
  });

  useEffect(() => { setEditorDirty(isDirty); }, [isDirty]);

  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => { if (isDirty) e.preventDefault(); };
    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, [isDirty]);

  const nodeColor = (node: Node) => {
    if (themeMode === 'static') {
      switch (node.type) {
        case 'agent': return '#0071E3';
        case 'task': return '#34C759';
        case 'condition': return '#AF52DE';
        case 'loop': return '#FF9500';
        case 'humanReview': return '#FF453A';
        case 'router': case 'parallel_flow': return '#5856D6';
        case 'orchestrator': return '#8944AB';
        case 'evaluator': return '#30B45E';
        case 'prompt_chain': return '#FF375F';
        case 'start': return '#06B6D4';
        case 'listen': return '#8B5CF6';
        case 'router_event': return '#F59E0B';
        default: return '#86868B';
      }
    }
    // Cyber mode neon colors
    switch (node.type) {
      case 'agent': return '#00D4FF';
      case 'task': return '#AF52DE';
      case 'condition': return '#FFD60A';
      case 'loop': return '#FF9500';
      case 'humanReview': return '#FF453A';
      case 'router': return '#F59E0B';
      case 'parallel_flow': return '#3B82F6';
      case 'orchestrator': return '#8B5CF6';
      case 'evaluator': return '#10B981';
      case 'prompt_chain': return '#EC4899';
      case 'start': return '#06B6D4';
      case 'listen': return '#8B5CF6';
      case 'router_event': return '#F59E0B';
      default: return '#636366';
    }
  };

  // 拖拽放置：监听 NodeToolbar 发出的自定义事件（WebView2 不支持 HTML5 拖拽）
  useEffect(() => {
    const handler = (e: Event) => {
      const { type, clientX, clientY } = (e as CustomEvent).detail;
      const position = screenToFlowPosition({ x: clientX, y: clientY });
      const id = `${type}-${generateId()}`;
      if (type === 'agent') {
        addNode({ id, type: 'agent', position, data: { name: '新Agent', role: '助手', llm_provider: 'openai', llm_model: 'gpt-4o', tools: [] } as unknown as Record<string, unknown> });
      } else if (type === 'task') {
        addNode({ id, type: 'task', position, data: { name: '新任务', description: '', output_type: 'text' } as unknown as Record<string, unknown> });
      } else if (type === 'condition') {
        addNode({ id, type: 'condition', position, data: { name: '条件判断', expression: '', true_branch: '', false_branch: '', true_branch_task_ids: [], false_branch_task_ids: [] } as unknown as Record<string, unknown> });
      } else if (type === 'loop') {
        addNode({ id, type: 'loop', position, data: { name: '循环节点', maxIterations: 10, condition: '', exitOnFailure: true, loopBodyTaskIds: [] } as unknown as Record<string, unknown> });
      } else if (type === 'humanReview') {
        addNode({ id, type: 'humanReview', position, data: { name: '人工审核', reviewType: 'approval', prompt: '', options: [], timeoutSeconds: undefined, timeoutAction: 'reject' } as unknown as Record<string, unknown> });
      } else if (type === 'router') {
        addNode({ id, type: 'router', position, data: { name: 'Router', patternType: 'router', routes: [], description: '' } as unknown as Record<string, unknown> });
      } else if (type === 'parallel_flow') {
        addNode({ id, type: 'parallel_flow', position, data: { name: 'Parallel', patternType: 'parallel', mode: 'sectioning', branches: [], description: '' } as unknown as Record<string, unknown> });
      } else if (type === 'orchestrator') {
        addNode({ id, type: 'orchestrator', position, data: { name: 'Orchestrator', patternType: 'orchestrator', worker_agent_ids: [], description: '' } as unknown as Record<string, unknown> });
      } else if (type === 'evaluator') {
        addNode({ id, type: 'evaluator', position, data: { name: 'Evaluator', patternType: 'evaluator', max_iterations: 5, evaluation_criteria: '', description: '' } as unknown as Record<string, unknown> });
      } else if (type === 'prompt_chain') {
        addNode({ id, type: 'prompt_chain', position, data: { name: 'Prompt Chain', patternType: 'prompt_chain', chain_tasks: [], pass_output: true, description: '' } as unknown as Record<string, unknown> });
      } else if (type === 'start') {
        addNode({ id, type: 'start', position, data: { name: '@start', flowType: 'start', event_name: 'on_start', description: '' } as unknown as Record<string, unknown> });
      } else if (type === 'listen') {
        addNode({ id, type: 'listen', position, data: { name: '@listen', flowType: 'listen', event_name: '', description: '' } as unknown as Record<string, unknown> });
      } else if (type === 'router_event') {
        addNode({ id, type: 'router_event', position, data: { name: '@router', flowType: 'router_event', event_name: '', condition: '', description: '' } as unknown as Record<string, unknown> });
      }
    };
    window.addEventListener('toolbar-drop', handler);
    return () => window.removeEventListener('toolbar-drop', handler);
  }, [screenToFlowPosition, addNode]);

  if (crewLoading) {
    return (
      <div className="flex items-center justify-center h-full bg-secondary">
        <div
          className="animate-spin rounded-full"
          style={{
            width: 32,
            height: 32,
            borderWidth: 2,
            borderColor: 'rgba(0,0,0,0.08)',
            borderTopColor: 'var(--accent)',
            borderStyle: 'solid',
          }}
        />
      </div>
    );
  }

  return (
    <div className="flex-1 relative" style={{ background: themeMode === 'static' ? 'var(--bg-secondary, #F5F5F7)' : '#000000' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        nodeTypes={activeNodeTypes}
        edgeTypes={activeEdgeTypes}
        fitView
        snapToGrid
        snapGrid={[16, 16]}
        connectionLineStyle={themeMode === 'static'
          ? { strokeWidth: 1, stroke: 'rgba(0,0,0,0.08)', strokeOpacity: 1 }
          : { strokeWidth: 2, stroke: '#00D4FF', filter: 'drop-shadow(0 0 6px rgba(0,212,255,0.5))' }
        }
        defaultEdgeOptions={themeMode === 'static'
          ? { type: 'particle', animated: true, data: { color: 'cyan' } }
          : { type: 'cyber', animated: true, data: { color: 'cyan', active: true } }
        }
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={32}
          size={0.5}
          color={themeMode === 'static' ? 'rgba(0, 0, 0, 0.04)' : 'rgba(0, 212, 255, 0.06)'}
        />
        <Controls
          style={themeMode === 'static' ? {
            background: 'rgba(255,255,255,0.80)',
            backdropFilter: 'blur(16px)',
            WebkitBackdropFilter: 'blur(16px)',
            border: '1px solid rgba(0,0,0,0.08)',
            borderRadius: 'var(--radius-lg)',
            boxShadow: 'var(--shadow-sm)',
            overflow: 'hidden',
          } : {
            background: 'rgba(10, 10, 15, 0.8)',
            backdropFilter: 'blur(40px) saturate(1.8)',
            WebkitBackdropFilter: 'blur(40px) saturate(1.8)',
            border: '0.5px solid rgba(0, 212, 255, 0.15)',
            borderRadius: '12px',
            boxShadow: '0 0 20px rgba(0, 212, 255, 0.08)',
            overflow: 'hidden',
          }}
        />
        <MiniMap
          nodeColor={nodeColor}
          maskColor={themeMode === 'static' ? 'rgba(245, 245, 247, 0.85)' : 'rgba(0, 0, 0, 0.85)'}
          style={themeMode === 'static' ? {
            background: 'rgba(255,255,255,0.80)',
            backdropFilter: 'blur(16px)',
            WebkitBackdropFilter: 'blur(16px)',
            border: '1px solid rgba(0,0,0,0.08)',
            borderRadius: 'var(--radius-lg)',
            boxShadow: 'var(--shadow-sm)',
            overflow: 'hidden',
          } : {
            background: 'rgba(10, 10, 15, 0.8)',
            backdropFilter: 'blur(40px) saturate(1.8)',
            WebkitBackdropFilter: 'blur(40px) saturate(1.8)',
            border: '0.5px solid rgba(0, 212, 255, 0.15)',
            borderRadius: '12px',
            boxShadow: '0 0 20px rgba(0, 212, 255, 0.08)',
            overflow: 'hidden',
          }}
        />
      </ReactFlow>

      {/* 顶部悬浮工具栏 — 双态适配 */}
      <div
        className="absolute left-1/2 flex items-center gap-3 flex-nowrap whitespace-nowrap"
        style={{
          top: 'var(--space-4)',
          transform: 'translateX(-50%)',
          background: themeMode === 'static' ? 'rgba(255,255,255,0.80)' : 'rgba(10, 10, 15, 0.8)',
          backdropFilter: themeMode === 'static' ? 'blur(20px)' : 'blur(40px) saturate(1.8)',
          WebkitBackdropFilter: themeMode === 'static' ? 'blur(20px)' : 'blur(40px) saturate(1.8)',
          border: themeMode === 'static' ? '1px solid rgba(0,0,0,0.08)' : '0.5px solid rgba(0, 212, 255, 0.12)',
          borderRadius: 'var(--radius-pill)',
          padding: 'var(--space-2) var(--space-6)',
          boxShadow: themeMode === 'static'
            ? 'var(--shadow-sm)'
            : '0 0 20px rgba(0, 212, 255, 0.06)',
        }}
      >
        {editingName ? (
          <input
            type="text"
            value={crewName}
            onChange={(e) => setCrewName(e.target.value)}
            onBlur={() => {
              setEditingName(false);
              if (crewName.trim() && crewName !== crew?.name) updateCrewMutation.mutate({ name: crewName.trim() });
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter') (e.target as HTMLInputElement).blur();
              if (e.key === 'Escape') { setCrewName(crew?.name || ''); setEditingName(false); }
            }}
            className="font-medium radius-sm outline-none"
            style={{
              fontSize: 'var(--text-footnote)',
              color: themeMode === 'static' ? 'var(--text-primary)' : '#E0E0E0',
              background: themeMode === 'static' ? 'rgba(0, 0, 0, 0.03)' : 'rgba(0, 212, 255, 0.05)',
              border: `1px solid ${themeMode === 'static' ? 'var(--accent)' : 'rgba(0, 212, 255, 0.3)'}`,
              padding: '5px 10px',
              width: '176px',
            }}
            autoFocus
          />
        ) : (
          <span
            className="font-semibold cursor-pointer"
            style={{ fontSize: 'var(--text-callout)', color: themeMode === 'static' ? 'var(--text-primary)' : '#E0E0E0' }}
            onClick={() => setEditingName(true)}
            title="点击编辑名称"
            onMouseEnter={(e) => (e.currentTarget.style.color = themeMode === 'static' ? 'var(--accent)' : '#00D4FF')}
            onMouseLeave={(e) => (e.currentTarget.style.color = themeMode === 'static' ? 'var(--text-primary)' : '#E0E0E0')}
          >
            {crewName || '工作流'}
          </span>
        )}

        <div style={{ width: '0.5px', height: '16px', background: themeMode === 'static' ? 'var(--separator)' : 'rgba(0,212,255,0.1)' }} />

        <div className="relative">
          <select
            value={crewProcess}
            onChange={(e) => {
              const value = e.target.value as 'sequential' | 'parallel' | 'hierarchical' | 'prompt_chain' | 'router' | 'orchestrator' | 'evaluator_optimizer' | 'event_flow' | 'plan_execute';
              setCrewProcess(value);
              updateCrewMutation.mutate({ process: value });
            }}
            className="outline-none cursor-pointer appearance-none whitespace-nowrap"
            style={{
              fontSize: 'var(--text-footnote)',
              borderRadius: 'var(--radius-sm)',
              color: themeMode === 'static' ? 'var(--text-secondary)' : '#A1A1A6',
              background: themeMode === 'static' ? 'rgba(0, 0, 0, 0.03)' : 'rgba(0, 212, 255, 0.04)',
              border: themeMode === 'static' ? '0.5px solid var(--separator)' : '0.5px solid rgba(0, 212, 255, 0.1)',
              padding: '5px 24px 5px 10px',
            }}
          >
            <option value="sequential">顺序执行</option>
            <option value="parallel">并行执行</option>
            <option value="hierarchical">层级管理</option>
            <option value="prompt_chain">提示链</option>
            <option value="router">路由分发</option>
            <option value="orchestrator">编排器-工作者</option>
            <option value="evaluator_optimizer">评估优化</option>
            <option value="event_flow">事件驱动</option>
            <option value="plan_execute">规划执行</option>
          </select>
          <ChevronDown
            className="w-3.5 h-3.5 absolute right-1.5 top-1/2 -translate-y-1/2 pointer-events-none"
            style={{ color: themeMode === 'static' ? 'var(--text-secondary)' : '#A1A1A6' }}
          />
        </div>

        <div style={{ width: '0.5px', height: '16px', background: themeMode === 'static' ? 'var(--separator)' : 'rgba(0,212,255,0.1)' }} />

        <div className="relative">
          <button
            onClick={() => setShowApprovalDropdown(!showApprovalDropdown)}
            className="outline-none cursor-pointer flex items-center gap-1 whitespace-nowrap"
            style={{
              fontSize: 'var(--text-footnote)',
              borderRadius: 'var(--radius-sm)',
              color: approvalMode === 'full_auto'
                ? '#FF3B30'
                : (themeMode === 'static' ? 'var(--text-secondary)' : '#A1A1A6'),
              background: approvalMode === 'full_auto'
                ? 'rgba(255, 59, 48, 0.06)'
                : (themeMode === 'static' ? 'rgba(0, 0, 0, 0.03)' : 'rgba(0, 212, 255, 0.04)'),
              border: approvalMode === 'full_auto'
                ? '0.5px solid rgba(255, 59, 48, 0.3)'
                : (themeMode === 'static' ? '0.5px solid var(--separator)' : '0.5px solid rgba(0, 212, 255, 0.1)'),
              padding: '5px 24px 5px 10px',
            }}
          >
            {approvalMode === 'full_auto' && <span style={{ color: '#FF3B30' }}>⚠</span>}
            {approvalMode === 'safe' ? '限制权限' : approvalMode === 'semi_auto' ? '默认权限' : '完全权限'}
            <ChevronDown className="w-3 h-3 ml-0.5" />
          </button>
          {showApprovalDropdown && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setShowApprovalDropdown(false)} />
              <div
                className="absolute z-50 mt-1 overflow-hidden"
                style={{
                  top: '100%',
                  left: 0,
                  minWidth: '120px',
                  borderRadius: 'var(--radius-md)',
                  background: themeMode === 'static' ? 'rgba(255,255,255,0.95)' : 'rgba(30,30,35,0.95)',
                  backdropFilter: 'blur(20px)',
                  border: themeMode === 'static' ? '1px solid rgba(0,0,0,0.1)' : '0.5px solid rgba(0,212,255,0.15)',
                  boxShadow: '0 8px 32px rgba(0,0,0,0.15)',
                }}
              >
                {[
                  { value: 'safe', label: '限制权限', desc: '所有操作需确认' },
                  { value: 'semi_auto', label: '默认权限', desc: '高风险操作需确认' },
                  { value: 'full_auto', label: '完全权限', desc: '全部自动执行', danger: true },
                ].map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => {
                      setShowApprovalDropdown(false);
                      if (opt.value === 'full_auto') {
                        setShowApprovalConfirm(true);
                        return;
                      }
                      setApprovalMode(opt.value);
                      updateCrewMutation.mutate({ approval_mode: opt.value as 'safe' | 'semi_auto' | 'full_auto' });
                    }}
                    className="w-full text-left px-3 py-2 flex items-center gap-2 transition-colors"
                    style={{
                      fontSize: 'var(--text-footnote)',
                      color: opt.danger ? '#FF3B30' : (themeMode === 'static' ? 'var(--text-primary)' : '#F5F5F7'),
                      background: approvalMode === opt.value
                        ? (opt.danger ? 'rgba(255,59,48,0.08)' : (themeMode === 'static' ? 'rgba(0,122,255,0.08)' : 'rgba(0,212,255,0.08)'))
                        : 'transparent',
                    }}
                    onMouseEnter={(e) => {
                      if (approvalMode !== opt.value) {
                        e.currentTarget.style.background = opt.danger ? 'rgba(255,59,48,0.06)' : (themeMode === 'static' ? 'rgba(0,0,0,0.04)' : 'rgba(255,255,255,0.05)');
                      }
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = approvalMode === opt.value
                        ? (opt.danger ? 'rgba(255,59,48,0.08)' : (themeMode === 'static' ? 'rgba(0,122,255,0.08)' : 'rgba(0,212,255,0.08)'))
                        : 'transparent';
                    }}
                  >
                    {opt.danger && <span style={{ color: '#FF3B30', fontSize: '12px' }}>⚠</span>}
                    <div>
                      <div style={{ fontWeight: approvalMode === opt.value ? 600 : 400 }}>{opt.label}</div>
                      <div style={{ fontSize: '11px', opacity: 0.5 }}>{opt.desc}</div>
                    </div>
                  </button>
                ))}
              </div>
            </>
          )}
        </div>

        <div style={{ width: '0.5px', height: '16px', background: themeMode === 'static' ? 'var(--separator)' : 'rgba(0,212,255,0.1)' }} />

        {/* 工作空间选择器 */}
        <motion.button
          className="flex items-center gap-1.5 radius-sm font-medium"
          style={{
            fontSize: 'var(--text-footnote)',
            color: workspaceDir
              ? (themeMode === 'static' ? '#007AFF' : '#00D4FF')
              : (themeMode === 'static' ? 'var(--text-tertiary)' : '#636366'),
            padding: '5px 12px',
            background: workspaceDir
              ? (themeMode === 'static' ? 'rgba(0,122,255,0.06)' : 'rgba(0,212,255,0.06)')
              : 'transparent',
            border: workspaceDir
              ? (themeMode === 'static' ? '0.5px solid rgba(0,122,255,0.2)' : '0.5px solid rgba(0,212,255,0.15)')
              : '0.5px solid transparent',
            borderRadius: 'var(--radius-sm)',
            cursor: 'pointer',
            maxWidth: '200px',
          }}
          onClick={async () => {
            try {
              const { invoke } = await import('@tauri-apps/api/core');
              const result = await invoke<string | null>('pick_folder');
              if (result) {
                setWorkspaceDir(result);
                updateCrewMutation.mutate({ workspace_dir: result });
              }
            } catch (e) {
              // Fallback: prompt 输入
              const dir = prompt('请输入工作空间路径：', workspaceDir || '');
              if (dir !== null) {
                setWorkspaceDir(dir || null);
                updateCrewMutation.mutate({ workspace_dir: dir || null });
              }
            }
          }}
          whileHover={themeMode === 'static'
            ? { scale: 1.02, backgroundColor: 'rgba(0,0,0,0.03)' }
            : { backgroundColor: 'rgba(0,212,255,0.06)' }
          }
          whileTap={{ scale: 0.97 }}
          title={workspaceDir || '点击选择工作空间'}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
          </svg>
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {workspaceDir ? workspaceDir.split(/[/\\]/).pop() || workspaceDir : '工作空间'}
          </span>
        </motion.button>

        <div style={{ width: '0.5px', height: '16px', background: themeMode === 'static' ? 'var(--separator)' : 'rgba(0,212,255,0.1)' }} />

        <motion.button
          className="flex items-center gap-1.5 radius-sm font-medium disabled:opacity-40"
          style={{
            fontSize: 'var(--text-footnote)',
            color: themeMode === 'static' ? 'var(--text-secondary)' : '#A1A1A6',
            padding: '5px 12px',
            background: 'transparent',
            border: 'none',
          }}
          onClick={() => saveMutation.mutate()}
          disabled={saveMutation.isPending}
          whileHover={themeMode === 'static'
            ? { scale: 1.02, backgroundColor: 'rgba(0,0,0,0.03)', color: 'var(--text-primary)' }
            : { backgroundColor: 'rgba(0,212,255,0.06)', color: '#00D4FF' }
          }
          whileTap={{ scale: 0.97 }}
          transition={{ duration: 0.15 }}
        >
          <Save className="w-4 h-4" />
          {saveMutation.isPending ? '保存中...' : '保存'}
        </motion.button>

        <ShortcutsHelp />

        <div style={{ width: '0.5px', height: '16px', background: themeMode === 'static' ? 'var(--separator)' : 'rgba(0,212,255,0.1)' }} />

        <span className="font-mono" style={{ fontSize: 'var(--text-micro)', color: themeMode === 'static' ? 'var(--text-tertiary)' : '#636366' }}>
          {nodes.length} nodes &middot; {edges.length} edges{isDirty && <span style={{ color: '#FF9F0A' }}> &middot; unsaved</span>}
        </span>
      </div>

      {/* 完全权限确认弹窗 — createPortal 到 body 避免被 ReactFlow transform 影响 */}
      {showApprovalConfirm && createPortal(
        <div
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 9999,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'rgba(0,0,0,0.45)',
            backdropFilter: 'blur(8px)',
            WebkitBackdropFilter: 'blur(8px)',
          }}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.92 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ type: 'spring', damping: 28, stiffness: 380 }}
            style={{
              width: '400px',
              maxWidth: '90vw',
              borderRadius: '16px',
              background: themeMode === 'static' ? '#FFFFFF' : '#1C1C1E',
              border: '1px solid rgba(255,59,48,0.25)',
              boxShadow: '0 24px 80px rgba(0,0,0,0.35), 0 0 0 1px rgba(0,0,0,0.05)',
              padding: '28px',
              overflow: 'hidden',
            }}
          >
            {/* 标题区 */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '18px' }}>
              <div style={{
                width: '36px', height: '36px', borderRadius: '10px',
                background: 'rgba(255,59,48,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '18px', flexShrink: 0,
              }}>
                ⚠
              </div>
              <div>
                <div style={{ fontSize: '16px', fontWeight: 600, color: '#FF3B30', letterSpacing: '-0.01em' }}>
                  开启完全权限
                </div>
                <div style={{ fontSize: '12px', color: themeMode === 'static' ? '#86868B' : '#636366', marginTop: '2px' }}>
                  此操作将降低安全限制
                </div>
              </div>
            </div>

            {/* 说明区 */}
            <div style={{
              fontSize: '13px', lineHeight: '1.65',
              color: themeMode === 'static' ? '#1D1D1F' : '#F5F5F7',
              marginBottom: '14px',
              wordBreak: 'break-word',
            }}>
              开启后，Agent 将<strong>自动执行所有操作</strong>，包括：
            </div>

            <div style={{
              display: 'flex', flexDirection: 'column', gap: '6px',
              marginBottom: '16px', padding: '12px 14px',
              borderRadius: '10px',
              background: themeMode === 'static' ? 'rgba(0,0,0,0.03)' : 'rgba(255,255,255,0.04)',
            }}>
              {['文件读写操作', '代码执行', 'Shell 命令执行', '外部 API 调用'].map((item) => (
                <div key={item} style={{
                  fontSize: '12px', color: themeMode === 'static' ? '#636366' : '#A1A1A6',
                  display: 'flex', alignItems: 'center', gap: '8px',
                }}>
                  <span style={{ color: '#FF3B30', fontSize: '10px' }}>●</span>
                  {item}
                  <span style={{ color: '#FF3B30', fontWeight: 600, marginLeft: 'auto', fontSize: '11px' }}>无需确认</span>
                </div>
              ))}
            </div>

            {/* 警告区 */}
            <div style={{
              fontSize: '12px', lineHeight: '1.55',
              color: '#FF3B30',
              marginBottom: '22px',
              padding: '10px 14px',
              borderRadius: '10px',
              background: 'rgba(255,59,48,0.07)',
              border: '0.5px solid rgba(255,59,48,0.15)',
              wordBreak: 'break-word',
            }}>
              此模式适用于可信环境下的自动化任务。请确保您了解潜在风险。
            </div>

            {/* 按钮区 */}
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowApprovalConfirm(false)}
                style={{
                  fontSize: '14px', fontWeight: 500,
                  padding: '9px 22px', borderRadius: '10px',
                  background: themeMode === 'static' ? 'rgba(0,0,0,0.05)' : 'rgba(255,255,255,0.08)',
                  color: themeMode === 'static' ? '#1D1D1F' : '#F5F5F7',
                  border: 'none', cursor: 'pointer',
                  transition: 'background 0.15s',
                }}
              >
                取消
              </button>
              <button
                onClick={() => {
                  setShowApprovalConfirm(false);
                  setApprovalMode('full_auto');
                  updateCrewMutation.mutate({ approval_mode: 'full_auto' });
                }}
                style={{
                  fontSize: '14px', fontWeight: 600,
                  padding: '9px 22px', borderRadius: '10px',
                  background: '#FF3B30', color: '#fff',
                  border: 'none', cursor: 'pointer',
                  transition: 'opacity 0.15s',
                }}
              >
                确认开启
              </button>
            </div>
          </motion.div>
        </div>,
        document.body,
      )}

      {/* DAG 校验面板 */}
      {showValidationPanel && (
        <div className="absolute bottom-4 left-4 z-10">
          <DAGValidationPanel
            errors={validationErrors}
            warnings={validationWarnings}
            onNodeClick={handleValidationErrorClick}
            onClose={() => setShowValidationPanel(false)}
          />
        </div>
      )}

      {/* 当面板关闭且有错误时，显示简化的提示 */}
      {!showValidationPanel && validationErrors.length > 0 && (
        <motion.button
          onClick={() => setShowValidationPanel(true)}
          className="absolute bottom-4 left-4 z-10 flex items-center gap-2 px-3 py-2"
          style={{
            background: themeMode === 'static' ? 'rgba(255,255,255,0.80)' : 'rgba(10, 10, 15, 0.8)',
            backdropFilter: themeMode === 'static' ? 'blur(16px)' : 'blur(40px) saturate(1.8)',
            WebkitBackdropFilter: themeMode === 'static' ? 'blur(16px)' : 'blur(40px) saturate(1.8)',
            color: 'var(--destructive)',
            borderRadius: 'var(--radius-lg)',
            boxShadow: themeMode === 'static' ? 'var(--shadow-raised)' : undefined,
            border: themeMode === 'static' ? '0.5px solid var(--separator)' : '0.5px solid rgba(255,59,48,0.2)',
          }}
          whileHover={{ boxShadow: '0 2px 20px rgba(0,0,0,0.06)' }}
          whileTap={{ scale: 0.97 }}
          transition={{ duration: 0.15 }}
        >
          <AlertCircle className="w-4 h-4" />
          <span className="text-13 font-medium">{validationErrors.length} 个错误</span>
        </motion.button>
      )}
    </div>
  );
};

// ============ Main Editor ============

let _editorDirty = false;
export const setEditorDirty = (v: boolean) => { _editorDirty = v; };

const Editor: React.FC = () => {
  const { crewId } = useParams<{ crewId: string }>();
  const navigate = useNavigate();
  const { selectedNode } = useFlowStore();
  const themeMode = useThemeStore((s) => s.mode);

  useEffect(() => { _editorDirty = false; return () => { _editorDirty = false; }; }, []);

  const handleBack = () => {
    if (_editorDirty && !window.confirm('有未保存的修改，确定要离开吗？')) return;
    navigate('/');
  };

  const handleRun = async () => {
    if (!crewId) return;
    if (_editorDirty) { toast('请先保存工作流再运行', { icon: '⚠️' }); return; }
    const { nodes, edges } = useFlowStore.getState();
    const dagResult = validateDAG(nodes, edges);
    if (!dagResult.valid) { toast.error(`工作流校验失败：${dagResult.errors[0].message}`); return; }
    try {
      // Phase 3: 隧道过渡 — 启动赛博模式后导航
      const { setTransitioning, enterCyberMode } = useThemeStore.getState();
      setTransitioning('to-cyber');

      const execution = await executionsApi.create({
        crew_id: crewId,
        llm_api_keys: getLLMKeys(),
        llm_base_urls: getLLMBaseUrls(),
      });

      // 等待隧道动画完成 (~3s) 再导航
      setTimeout(() => {
        enterCyberMode();
        navigate(`/execution/${execution.id}`);
      }, 3200);
    } catch (err: unknown) {
      useThemeStore.getState().exitCyberMode();
      const msg = err instanceof Error ? err.message : '启动失败';
      toast.error(msg);
    }
  };

  if (!crewId) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-secondary">
        <p style={{ color: 'var(--text-secondary)' }}>未指定工作流ID</p>
      </div>
    );
  }

  return (
    <ReactFlowProvider>
      <TunnelTransition>
        <div className="h-screen flex flex-col" style={{ background: themeMode === 'static' ? 'var(--bg-secondary, #F5F5F7)' : '#000000' }}>
          <header
            className="flex items-center gap-4 flex-shrink-0 z-20"
            style={{
              background: themeMode === 'static' ? 'rgba(255,255,255,0.80)' : 'rgba(0, 0, 0, 0.85)',
              backdropFilter: themeMode === 'static' ? 'blur(20px)' : 'blur(40px) saturate(1.8)',
              WebkitBackdropFilter: themeMode === 'static' ? 'blur(20px)' : 'blur(40px) saturate(1.8)',
              borderBottom: themeMode === 'static' ? '1px solid rgba(0,0,0,0.05)' : '0.5px solid rgba(0, 212, 255, 0.12)',
              boxShadow: themeMode === 'static' ? 'none' : 'none',
              padding: '0 var(--space-5)',
              height: 'var(--nav-height, 52px)',
            }}
          >
          <motion.button
            className="flex items-center gap-1.5 px-3 py-1.5 radius-sm"
            style={{ fontSize: 'var(--text-callout)', color: themeMode === 'static' ? 'var(--text-secondary)' : '#A1A1A6' }}
            onClick={handleBack}
            whileHover={{ backgroundColor: themeMode === 'static' ? 'rgba(0,0,0,0.03)' : 'rgba(0,212,255,0.08)', color: themeMode === 'static' ? 'var(--text-primary)' : '#00D4FF' }}
            whileTap={{ scale: 0.97 }}
            transition={{ duration: 0.15 }}
          >
            <ArrowLeft className="w-4 h-4" />
            <span>返回</span>
          </motion.button>

          <div className="flex-1" />

          <motion.button
            className="flex items-center gap-2 font-medium"
            style={{
              fontSize: 'var(--text-callout)',
              background: themeMode === 'static' ? 'var(--accent)' : 'transparent',
              color: themeMode === 'static' ? 'var(--text-inverse)' : '#00D4FF',
              borderRadius: 'var(--radius-pill)',
              height: '36px',
              padding: '0 var(--space-5)',
              border: themeMode === 'static' ? 'none' : '1px solid var(--accent)',
              lineHeight: 1.4,
              boxShadow: themeMode === 'static' ? 'none' : '0 0 12px rgba(0, 212, 255, 0.15)',
            }}
            onClick={handleRun}
            whileHover={themeMode === 'static'
              ? { backgroundColor: 'var(--accent-hover)', boxShadow: '0 4px 16px rgba(0,113,227,0.35)' }
              : { boxShadow: '0 0 20px rgba(0, 212, 255, 0.3), 0 0 40px rgba(0, 212, 255, 0.15)' }
            }
            whileTap={{ scale: 0.97 }}
            transition={{ duration: 0.15 }}
          >
            <Play className="w-4 h-4" />
            运行工作流
          </motion.button>
        </header>

        <div className="flex flex-1 overflow-hidden">
          <NodeToolbar />
          <FlowCanvas key={crewId} crewId={crewId} />
          {selectedNode && <PropertyPanel />}
        </div>
      </div>
    </TunnelTransition>
    </ReactFlowProvider>
  );
};

export default Editor;
