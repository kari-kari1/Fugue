import React, { useRef, useEffect, useMemo, useCallback, useState } from 'react';
import { useForm } from 'react-hook-form';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Trash2, Search, FileText, FileEdit, Code, Globe, Database, Image, BarChart3, AlertTriangle, Wrench, GitBranch, BookOpen, Play, Radio, GitFork, Split, Network, RefreshCw, Link2 } from 'lucide-react';
import { MemoryPanel } from './MemoryPanel';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../../api/client';
import { useFlowStore } from '../../stores/flowStore';
import { getLLMConfig } from '../../lib/llmKeys';
import { getAgentIcon, getTaskIcon, getConditionIcon, getLoopIcon, getReviewIcon } from '../../lib/utils';
import { getAllToolMeta } from '../../lib/tools';
import { getToolSupportStatuses, type ToolSupportStatus } from '../../lib/modelCapabilities';
import { crewsApi } from '../../api/crews';
import { knowledgeBasesApi } from '../../api/knowledgeBases';
import FileAttachments from './FileAttachments';
import type { AgentNodeData, TaskNodeData, ConditionNodeData, LoopNodeData, HumanReviewNodeData, Crew, TaskAttachment, KnowledgeBase } from '../../types';

function getProviderOptions(): { value: string; label: string }[] {
  const config = getLLMConfig();
  const configured = Object.entries(config)
    .filter(([_, c]) => c.api_key?.trim())
    .map(([id]) => ({ value: id, label: id }));
  // Mock 仅作为备选，不作为默认项
  return configured.length > 0 ? configured : [{ value: 'openai', label: 'openai' }];
}

function getModelOptions(provider: string): string[] {
  const config = getLLMConfig();
  const providerConfig = config[provider];
  if (providerConfig?.model) return [providerConfig.model];
  return ['default'];
}

// 工具图标映射
const TOOL_ICONS: Record<string, React.FC<{ className?: string }>> = {
  search: Search,
  file_read: FileText,
  file_write: FileEdit,
  code: Code,
  api: Globe,
  database: Database,
  image: Image,
  analysis: BarChart3,
};

const OUTPUT_TYPES = [
  { value: 'text', label: '文本' },
  { value: 'json', label: 'JSON' },
  { value: 'file', label: '文件' },
  { value: 'code', label: '代码' },
];

const inputClass = "w-full px-3.5 py-2.5 radius-sm text-13 outline-none transition-all";
const labelClass = "block text-13 font-medium mb-1.5";

// Inline style objects for light liquid glass inputs
const inputStyle: React.CSSProperties = {
  color: '#1D1D1F',
  background: 'rgba(0, 0, 0, 0.03)',
  border: '0.5px solid rgba(0, 0, 0, 0.08)',
};
const labelStyle: React.CSSProperties = {
  color: '#1D1D1F',
};

const PropertyPanel: React.FC = () => {
  const { selectedNode, setSelectedNode, removeNode } = useFlowStore();
  if (!selectedNode) return null;

  const isAgent = selectedNode.type === 'agent';
  const isCondition = selectedNode.type === 'condition';
  const isLoop = selectedNode.type === 'loop';
  const isHumanReview = selectedNode.type === 'humanReview';
  const isEventFlow = ['start', 'listen', 'router_event'].includes(selectedNode.type || '');
  const isWorkflowPattern = ['router', 'parallel_flow', 'orchestrator', 'evaluator', 'prompt_chain'].includes(selectedNode.type || '');
  const handleClose = () => setSelectedNode(null);
  const handleDelete = () => { removeNode(selectedNode.id); setSelectedNode(null); };

  // 工作流模式节点图标/颜色映射
  const WP_ICONS: Record<string, React.ReactNode> = {
    router: <GitFork size={16} />,
    parallel_flow: <Split size={16} />,
    orchestrator: <Network size={16} />,
    evaluator: <RefreshCw size={16} />,
    prompt_chain: <Link2 size={16} />,
  };
  const WP_COLORS: Record<string, { bg: string; text: string }> = {
    router: { bg: 'bg-amber-50', text: 'text-amber-600' },
    parallel_flow: { bg: 'bg-blue-50', text: 'text-blue-600' },
    orchestrator: { bg: 'bg-purple-50', text: 'text-purple-600' },
    evaluator: { bg: 'bg-emerald-50', text: 'text-emerald-600' },
    prompt_chain: { bg: 'bg-pink-50', text: 'text-pink-600' },
  };
  const WP_LABELS: Record<string, string> = {
    router: 'Router 路由',
    parallel_flow: 'Parallel 并行',
    orchestrator: 'Orchestrator 编排',
    evaluator: 'Evaluator 评估',
    prompt_chain: 'Prompt Chain 链式',
  };

  const panelIcon = isAgent
    ? getAgentIcon((selectedNode.data as unknown as AgentNodeData).role || '')
    : isCondition
      ? getConditionIcon()
      : isLoop
        ? getLoopIcon()
        : isHumanReview
          ? getReviewIcon()
          : isEventFlow
            ? (selectedNode.type === 'start' ? <Play size={16} /> : selectedNode.type === 'listen' ? <Radio size={16} /> : <GitBranch size={16} />)
            : isWorkflowPattern
              ? (WP_ICONS[selectedNode.type || ''] || <GitFork size={16} />)
              : getTaskIcon();

  const wpColor = WP_COLORS[selectedNode.type || ''];
  const panelIconBg = isAgent
    ? 'bg-accent-primary-dim'
    : isCondition
      ? 'bg-[var(--accent-purple)]/10'
      : isLoop
        ? 'bg-[var(--accent-orange)]/10'
        : isHumanReview
          ? 'bg-pink-50'
          : isEventFlow
            ? 'bg-[var(--accent-blue)]/10'
            : isWorkflowPattern
              ? (wpColor?.bg || 'bg-amber-50')
              : 'bg-accent-green-dim';

  const panelIconColor = isAgent
    ? 'text-accent-primary'
    : isCondition
      ? 'text-[var(--accent-purple)]'
      : isLoop
        ? 'text-[var(--accent-orange)]'
        : isHumanReview
          ? 'text-pink-600'
          : isEventFlow
            ? 'text-[var(--accent-blue)]'
            : isWorkflowPattern
              ? (wpColor?.text || 'text-amber-600')
              : 'text-accent-green';

  const flowLabel = selectedNode.type === 'start' ? '@start' : selectedNode.type === 'listen' ? '@listen' : '@router';
  const wpLabel = WP_LABELS[selectedNode.type || ''] || '工作流模式';
  const panelTitle = isAgent ? 'Agent 配置' : isCondition ? '条件分支配置' : isLoop ? '循环节点配置' : isHumanReview ? '人工审核配置' : isEventFlow ? `${flowLabel} 事件节点` : isWorkflowPattern ? `${wpLabel} 配置` : 'Task 配置';
  const panelDesc = isAgent ? '配置智能体参数' : isCondition ? '配置条件表达式和分支' : isLoop ? '配置迭代次数和循环条件' : isHumanReview ? '配置审核类型和超时' : isEventFlow ? '配置事件驱动流程' : isWorkflowPattern ? '配置工作流模式参数' : '配置任务参数';

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, x: 24 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: 24 }}
        transition={{ type: 'spring', stiffness: 120, damping: 15 }}
        style={{
          width: '288px',
          background: 'rgba(255, 255, 255, 0.45)',
          backdropFilter: 'blur(40px) saturate(1.8)',
          WebkitBackdropFilter: 'blur(40px) saturate(1.8)',
          borderRadius: '18px',
          boxShadow: '0 2px 20px rgba(0,0,0,0.04), inset 0 1px 0 rgba(255,255,255,0.8)',
          display: 'flex',
          flexDirection: 'column',
          height: '100%',
          zIndex: 20,
          margin: '12px',
          border: '0.5px solid rgba(255, 255, 255, 0.6)',
        }}
      >
      <div className="flex items-center justify-between px-4 py-4" style={{ borderBottom: '0.5px solid rgba(0,0,0,0.06)' }}>
        <div className="flex items-center gap-3">
          <div className={`w-9 h-9 radius-sm flex items-center justify-center ${panelIconBg}`}>
            <div className={panelIconColor}>{panelIcon}</div>
          </div>
          <div>
            <span className="font-semibold text-sm" style={{ color: '#1D1D1F' }}>{panelTitle}</span>
            <p className="text-xs" style={{ color: '#6E6E73' }}>{panelDesc}</p>
          </div>
        </div>
        <button onClick={handleClose} className="p-1.5 radius-sm transition-colors"
          style={{ background: 'transparent' }}
          onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(0,0,0,0.03)')}
          onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
        >
          <X className="w-4 h-4" style={{ color: '#6E6E73' }} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-5">
        {isAgent ? (
          <AgentPropertyForm key={selectedNode.id} nodeId={selectedNode.id} data={selectedNode.data as unknown as AgentNodeData} />
        ) : isCondition ? (
          <ConditionPropertyForm key={selectedNode.id} nodeId={selectedNode.id} data={selectedNode.data as unknown as ConditionNodeData} />
        ) : isLoop ? (
          <LoopPropertyForm key={selectedNode.id} nodeId={selectedNode.id} data={selectedNode.data as unknown as LoopNodeData} />
        ) : isHumanReview ? (
          <HumanReviewPropertyForm key={selectedNode.id} nodeId={selectedNode.id} data={selectedNode.data as unknown as HumanReviewNodeData} />
        ) : isEventFlow ? (
          <EventFlowPropertyForm key={selectedNode.id} nodeId={selectedNode.id} flowType={selectedNode.type as string} data={selectedNode.data as unknown as Record<string, unknown>} />
        ) : isWorkflowPattern ? (
          <WorkflowPatternPropertyForm key={selectedNode.id} nodeId={selectedNode.id} patternType={selectedNode.type as string} data={selectedNode.data as unknown as Record<string, unknown>} />
        ) : (
          <TaskPropertyForm key={selectedNode.id} nodeId={selectedNode.id} data={selectedNode.data as unknown as TaskNodeData} />
        )}
      </div>

      <div className="px-4 py-3.5" style={{ borderTop: '0.5px solid rgba(0,0,0,0.06)' }}>
        <button
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 radius-sm text-13 font-medium transition-all"
          style={{
            color: '#FF3B30',
            background: 'rgba(255,59,48,0.06)',
            border: '0.5px solid rgba(255,59,48,0.12)',
          }}
          onClick={handleDelete}
        >
          <Trash2 className="w-4 h-4" />
          删除节点
        </button>
      </div>
      </motion.div>
    </AnimatePresence>
  );
};

interface AgentFormProps { nodeId: string; data: AgentNodeData; }

const AgentPropertyForm: React.FC<AgentFormProps> = ({ nodeId, data }) => {
  const updateNodeData = useFlowStore((s) => s.updateNodeData);
  const providers = useMemo(() => getProviderOptions(), []);
  const defaultProvider = providers[0]?.value || 'openai';
  const allTools = useMemo(() => getAllToolMeta(), []);

  const { register, watch, handleSubmit, setValue, getValues } = useForm<AgentNodeData>({
    defaultValues: {
      name: data.name || '', role: data.role || '',
      llm_provider: data.llm_provider || defaultProvider,
      llm_model: data.llm_model || getModelOptions(defaultProvider)[0],
      tools: data.tools || [],
    },
  });

  const watchProvider = watch('llm_provider');
  const watchModel = watch('llm_model');
  const watchTools = watch('tools') || [];
  const availableModels = getModelOptions(watchProvider);

  // 逐工具检测可用性
  const toolStatuses = useMemo(
    () => getToolSupportStatuses(watchProvider, watchModel, allTools),
    [watchProvider, watchModel, allTools],
  );

  // 快速查找 Map
  const statusMap = useMemo(() => {
    const map = new Map<string, ToolSupportStatus>();
    for (const s of toolStatuses) map.set(s.toolId, s);
    return map;
  }, [toolStatuses]);

  // 切换模型后，自动移除不可用的已选工具
  const prevStatusMapRef = useRef(statusMap);
  useEffect(() => {
    const prev = prevStatusMapRef.current;
    if (watchTools.length > 0) {
      const newTools = watchTools.filter((tid) => {
        const wasAvailable = prev.get(tid)?.available ?? true;
        const isAvailable = statusMap.get(tid)?.available ?? false;
        // 仅移除从"可用"变为"不可用"的工具
        return !(wasAvailable && !isAvailable);
      });
      if (newTools.length !== watchTools.length) {
        setValue('tools', newTools, { shouldDirty: true });
        const currentValues = getValues();
        updateNodeData(nodeId, { ...currentValues, tools: newTools });
      }
    }
    prevStatusMapRef.current = statusMap;
  }, [statusMap, watchTools, setValue, getValues, updateNodeData, nodeId]);

  const onSubmit = (formData: AgentNodeData) => updateNodeData(nodeId, formData);
  const submitRef = useRef<() => void>(() => {});
  submitRef.current = () => { handleSubmit(onSubmit)(); };
  useEffect(() => { return () => { submitRef.current(); }; }, []);

  const handleToolToggle = useCallback((toolId: string, available: boolean) => {
    if (!available) return;
    const current = getValues('tools') || [];
    const next = current.includes(toolId)
      ? current.filter((t) => t !== toolId)
      : [...current, toolId];
    setValue('tools', next, { shouldDirty: true });
    // 立即同步到 flowStore
    const currentValues = getValues();
    updateNodeData(nodeId, { ...currentValues, tools: next });
  }, [getValues, setValue, updateNodeData, nodeId]);

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label className={labelClass} style={labelStyle}>名称</label>
        <input {...register('name', { required: true })} className={inputClass} style={inputStyle} placeholder="例如：研究助手" onBlur={handleSubmit(onSubmit)} />
      </div>
      <div>
        <label className={labelClass} style={labelStyle}>角色</label>
        <input {...register('role', { required: true })} className={inputClass} style={inputStyle} placeholder="例如：资深研究员" onBlur={handleSubmit(onSubmit)} />
      </div>
      <div>
        <label className={labelClass} style={labelStyle}>LLM 提供商</label>
        <select {...register('llm_provider')} className={inputClass} style={inputStyle}
          onChange={(e) => {
            const newProvider = e.target.value;
            const models = getModelOptions(newProvider);
            setValue('llm_provider', newProvider);
            setValue('llm_model', models[0] || 'default');
            updateNodeData(nodeId, { llm_provider: newProvider, llm_model: models[0] || 'default' });
          }}>
          {providers.map((p) => <option key={p.value} value={p.value}>{p.value === 'mock' ? p.label : p.value}</option>)}
        </select>
      </div>
      <div>
        <label className={labelClass} style={labelStyle}>模型</label>
        <select {...register('llm_model')} className={inputClass} style={inputStyle}
          onChange={(e) => {
            setValue('llm_model', e.target.value);
            updateNodeData(nodeId, { llm_model: e.target.value });
          }}>
          {availableModels.map((m) => <option key={m} value={m}>{m}</option>)}
        </select>
      </div>
      <div>
        <div className="flex items-center justify-between mb-1.5">
          <label className={labelClass + ' !mb-0'} style={labelStyle}>工具</label>
          {(() => {
            const unavailCount = toolStatuses.filter((s) => !s.available).length;
            if (unavailCount === allTools.length) {
              return (
                <span className="flex items-center gap-1 text-11" style={{ color: '#FF9F0A' }}>
                  <AlertTriangle className="w-3 h-3" />
                  全部不可用
                </span>
              );
            }
            if (unavailCount > 0) {
              return (
                <span className="flex items-center gap-1 text-11" style={{ color: '#6E6E73' }}>
                  <Wrench className="w-3 h-3" />
                  {allTools.length - unavailCount}/{allTools.length} 可用
                </span>
              );
            }
            return (
              <span className="flex items-center gap-1 text-11" style={{ color: '#34C759' }}>
                <Wrench className="w-3 h-3" />
                全部可用
              </span>
            );
          })()}
        </div>

        {/* 模型完全不支持工具时的警告 */}
        {toolStatuses.some((s) => s.reason === 'model_no_tools') &&
          toolStatuses.every((s) => !s.available) && (
          <div className="mb-2 px-3 py-2 radius-sm text-11 leading-relaxed" style={{ background: 'rgba(255,149,0,0.06)', border: '0.5px solid rgba(255,149,0,0.12)', color: '#FF9F0A' }}>
            当前模型 <strong>{watchModel}</strong> 不支持 Function Calling，工具无法使用。请切换到支持工具调用的模型（如 GPT-4o、Claude 等）。
          </div>
        )}

        {/* 部分工具因模型能力不足不可用时的提示 */}
        {toolStatuses.some((s) => s.reason === 'missing_capability') && (
          <div className="mb-2 px-3 py-2 radius-sm text-11 leading-relaxed" style={{ background: 'rgba(0,113,227,0.06)', border: '0.5px solid rgba(0,113,227,0.12)', color: '#0071E3' }}>
            部分工具因当前模型 <strong>{watchModel}</strong> 缺少特定能力而不可用（如图像生成需要多模态模型）。
          </div>
        )}

        <div className="grid grid-cols-2 gap-1.5">
          {allTools.map((tool) => {
            const status = statusMap.get(tool.id);
            const available = status?.available ?? false;
            const isSelected = watchTools.includes(tool.id);
            const Icon = TOOL_ICONS[tool.icon] || Code;

            return (
              <button
                key={tool.id}
                type="button"
                title={available ? tool.description : (status?.reasonText || '不可用')}
                onClick={() => handleToolToggle(tool.id, available)}
                disabled={!available}
                className="flex items-center gap-2 px-2.5 py-2 radius-sm text-left transition-all"
                style={{
                  ...(!available
                    ? { opacity: 0.4, cursor: 'not-allowed', background: 'rgba(0,0,0,0.01)', color: '#6E6E73' }
                    : isSelected
                      ? { background: 'rgba(0,113,227,0.15)', color: '#0071E3', border: '1px solid rgba(0,113,227,0.25)', cursor: 'pointer' }
                      : { background: 'rgba(0,0,0,0.02)', color: '#6E6E73', border: '1px solid transparent', cursor: 'pointer' }),
                }}
              >
                <Icon className="w-3.5 h-3.5 flex-shrink-0" />
                <div className="min-w-0">
                  <div className="text-xs font-medium truncate" style={isSelected && available ? { color: '#0071E3' } : { color: '#1D1D1F' }}>
                    {tool.name}
                  </div>
                  <div className="text-10 truncate leading-tight mt-0.5" style={{ color: '#6E6E73' }}>
                    {!available
                      ? (status?.reason === 'not_implemented' ? '尚未实现'
                        : status?.reason === 'missing_capability' ? '模型能力不足'
                        : '模型不支持')
                      : tool.shortDesc
                    }
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>
      {/* P1-1: 知识库关联 */}
      <KnowledgeBaseSelector agentId={data.agent?.id || nodeId} />
      {/* 分层记忆管理 */}
      <div className="pt-3" style={{ borderTop: '0.5px solid rgba(0,0,0,0.06)' }}>
        <MemoryPanel agentId={data.agent?.id} />
      </div>
      <button type="submit" className="w-full flex items-center justify-center gap-2 py-2.5 text-13 font-medium radius-sm" style={{ background: '#0071E3', color: '#FFFFFF', border: 'none' }}>
        应用更改
      </button>
    </form>
  );
};

interface TaskFormProps { nodeId: string; data: TaskNodeData; }

const TaskPropertyForm: React.FC<TaskFormProps> = ({ nodeId, data }) => {
  const updateNodeData = useFlowStore((s) => s.updateNodeData);
  const [crews, setCrews] = useState<Crew[]>([]);
  const { register, handleSubmit, watch, setValue } = useForm<TaskNodeData>({
    defaultValues: {
      name: data.name || '',
      description: data.description || '',
      output_type: data.output_type || 'text',
      sub_crew_id: data.sub_crew_id || '',
    },
  });

  const subCrewId = watch('sub_crew_id');

  useEffect(() => {
    crewsApi.list({ skip: 0, limit: 50 }).then(setCrews).catch(() => {});
  }, []);

  const onSubmit = (formData: TaskNodeData) => updateNodeData(nodeId, formData);
  const submitRef = useRef<() => void>(() => {});
  submitRef.current = () => { handleSubmit(onSubmit)(); };
  useEffect(() => { return () => { submitRef.current(); }; }, []);

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label className={labelClass} style={labelStyle}>任务名称</label>
        <input {...register('name', { required: true })} className={inputClass} style={inputStyle} placeholder="例如：撰写报告" onBlur={handleSubmit(onSubmit)} />
      </div>
      <div>
        <label className={labelClass} style={labelStyle}>任务描述</label>
        <textarea {...register('description')} rows={4} className={`${inputClass} resize-none`} style={inputStyle} placeholder="详细描述任务的目标和要求..." onBlur={handleSubmit(onSubmit)} />
      </div>
      <div>
        <label className={labelClass} style={labelStyle}>输出类型</label>
        <select {...register('output_type')} className={inputClass} style={inputStyle} onBlur={handleSubmit(onSubmit)}>
          {OUTPUT_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
        </select>
      </div>
      <div className="pt-3" style={{ borderTop: '0.5px solid rgba(0,0,0,0.06)' }}>
        <div className="flex items-center gap-2 mb-1.5">
          <GitBranch className="w-3.5 h-3.5" style={{ color: '#AF52DE' }} />
          <label className={`${labelClass} !mb-0`} style={labelStyle}>子工作流（可选）</label>
        </div>
        <select
          value={subCrewId || ''}
          className={inputClass}
          style={inputStyle}
          onChange={(e) => {
            const val = e.target.value || undefined;
            setValue('sub_crew_id', val, { shouldDirty: true });
            updateNodeData(nodeId, { sub_crew_id: val });
          }}
        >
          <option value="">无（普通任务）</option>
          {crews.map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
        <p className="text-10 mt-1.5" style={{ color: '#6E6E73' }}>
          选择后，此任务将作为子工作流执行（嵌套编排）
        </p>
      </div>
      <div className="pt-3" style={{ borderTop: '0.5px solid rgba(0,0,0,0.06)' }}>
        <FileAttachments
          attachments={data.attachments || []}
          onChange={(attachments: TaskAttachment[]) => {
            updateNodeData(nodeId, { attachments });
          }}
        />
      </div>
      <button type="submit" className="w-full flex items-center justify-center gap-2 py-2.5 text-13 font-medium radius-sm" style={{ background: '#0071E3', color: '#FFFFFF', border: 'none' }}>
        应用更改
      </button>
    </form>
  );
};

interface ConditionFormProps { nodeId: string; data: ConditionNodeData; }

const ConditionPropertyForm: React.FC<ConditionFormProps> = ({ nodeId, data }) => {
  const updateNodeData = useFlowStore((s) => s.updateNodeData);
  const allNodes = useFlowStore((s) => s.nodes);
  const taskNodes = useMemo(() => allNodes.filter((n) => n.type === 'task'), [allNodes]);

  const { register, handleSubmit, watch, setValue } = useForm<ConditionNodeData>({
    defaultValues: {
      name: data.name || '',
      expression: data.expression || '',
      true_branch: data.true_branch || '',
      false_branch: data.false_branch || '',
      true_branch_task_ids: data.true_branch_task_ids || [],
      false_branch_task_ids: data.false_branch_task_ids || [],
    },
  });

  const trueBranchIds = watch('true_branch_task_ids') || [];
  const falseBranchIds = watch('false_branch_task_ids') || [];

  const toggleTaskId = (field: 'true_branch_task_ids' | 'false_branch_task_ids', taskId: string) => {
    const current = field === 'true_branch_task_ids' ? trueBranchIds : falseBranchIds;
    const next = current.includes(taskId) ? current.filter((id) => id !== taskId) : [...current, taskId];
    setValue(field, next, { shouldDirty: true });
  };

  const onSubmit = (formData: ConditionNodeData) => updateNodeData(nodeId, formData);
  const submitRef = useRef<() => void>(() => {});
  submitRef.current = () => { handleSubmit(onSubmit)(); };
  useEffect(() => { return () => { submitRef.current(); }; }, []);

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label className={labelClass} style={labelStyle}>节点名称</label>
        <input {...register('name', { required: true })} className={inputClass} style={inputStyle} placeholder="例如：检查结果" onBlur={handleSubmit(onSubmit)} />
      </div>
      <div>
        <label className={labelClass} style={labelStyle}>条件表达式</label>
        <textarea
          {...register('expression', { required: true })}
          rows={3}
          className={`${inputClass} resize-none font-mono text-xs`}
          style={inputStyle}
          placeholder='例如: context["task_output"]["score"] > 80'
          onBlur={handleSubmit(onSubmit)}
        />
        <p className="text-10 mt-1.5 leading-relaxed" style={{ color: '#6E6E73' }}>
          使用 Python 语法。可用变量：<code className="px-1 py-0.5 rounded" style={{ background: 'rgba(0,0,0,0.03)', color: '#6E6E73' }}>context</code>（包含任务输出等）
        </p>
      </div>
      <div>
        <label className={labelClass} style={labelStyle}>True 分支 - 执行的任务</label>
        {taskNodes.length === 0 ? (
          <p className="text-xs" style={{ color: '#6E6E73' }}>暂无任务节点，请先添加任务</p>
        ) : (
          <div className="space-y-1.5 max-h-32 overflow-y-auto rounded-md p-2" style={{ border: '0.5px solid rgba(0,0,0,0.06)' }}>
            {taskNodes.map((tn) => {
              const taskName = (tn.data as Record<string, unknown>)?.name as string || tn.id;
              const checked = trueBranchIds.includes(tn.id);
              return (
                <label key={tn.id} className="flex items-center gap-2 text-xs cursor-pointer">
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => { toggleTaskId('true_branch_task_ids', tn.id); setTimeout(() => submitRef.current(), 0); }}
                    className="rounded"
                    style={{ borderColor: 'rgba(0,0,0,0.06)' }}
                  />
                  <span className="truncate" style={{ color: '#6E6E73' }}>{taskName}</span>
                </label>
              );
            })}
          </div>
        )}
        <input {...register('true_branch')} className={`${inputClass} mt-1.5`} style={inputStyle} placeholder="分支描述（可选）" onBlur={handleSubmit(onSubmit)} />
      </div>
      <div>
        <label className={labelClass} style={labelStyle}>False 分支 - 执行的任务</label>
        {taskNodes.length === 0 ? (
          <p className="text-xs" style={{ color: '#6E6E73' }}>暂无任务节点，请先添加任务</p>
        ) : (
          <div className="space-y-1.5 max-h-32 overflow-y-auto rounded-md p-2" style={{ border: '0.5px solid rgba(0,0,0,0.06)' }}>
            {taskNodes.map((tn) => {
              const taskName = (tn.data as Record<string, unknown>)?.name as string || tn.id;
              const checked = falseBranchIds.includes(tn.id);
              return (
                <label key={tn.id} className="flex items-center gap-2 text-xs cursor-pointer">
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => { toggleTaskId('false_branch_task_ids', tn.id); setTimeout(() => submitRef.current(), 0); }}
                    className="rounded"
                    style={{ borderColor: 'rgba(0,0,0,0.06)' }}
                  />
                  <span className="truncate" style={{ color: '#6E6E73' }}>{taskName}</span>
                </label>
              );
            })}
          </div>
        )}
        <input {...register('false_branch')} className={`${inputClass} mt-1.5`} style={inputStyle} placeholder="分支描述（可选）" onBlur={handleSubmit(onSubmit)} />
      </div>
      <button type="submit" className="w-full flex items-center justify-center gap-2 py-2.5 text-13 font-medium radius-sm" style={{ background: '#0071E3', color: '#FFFFFF', border: 'none' }}>
        应用更改
      </button>
    </form>
  );
};

interface LoopFormProps { nodeId: string; data: LoopNodeData; }

const LoopPropertyForm: React.FC<LoopFormProps> = ({ nodeId, data }) => {
  const updateNodeData = useFlowStore((s) => s.updateNodeData);
  const allNodes = useFlowStore((s) => s.nodes);
  const taskNodes = useMemo(() => allNodes.filter((n) => n.type === 'task'), [allNodes]);

  const { register, handleSubmit, watch, setValue } = useForm<LoopNodeData>({
    defaultValues: {
      name: data.name || '',
      maxIterations: data.maxIterations || 10,
      condition: data.condition || '',
      exitOnFailure: data.exitOnFailure !== undefined ? data.exitOnFailure : true,
      loopBodyTaskIds: data.loopBodyTaskIds || [],
    },
  });

  const loopBodyIds = watch('loopBodyTaskIds') || [];

  const toggleTaskId = (taskId: string) => {
    const current = loopBodyIds;
    const next = current.includes(taskId) ? current.filter((id) => id !== taskId) : [...current, taskId];
    setValue('loopBodyTaskIds', next, { shouldDirty: true });
  };

  const onSubmit = (formData: LoopNodeData) => updateNodeData(nodeId, formData);
  const submitRef = useRef<() => void>(() => {});
  submitRef.current = () => { handleSubmit(onSubmit)(); };
  useEffect(() => { return () => { submitRef.current(); }; }, []);

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label className={labelClass} style={labelStyle}>节点名称</label>
        <input {...register('name', { required: true })} className={inputClass} style={inputStyle} placeholder="例如：质量迭代" onBlur={handleSubmit(onSubmit)} />
      </div>
      <div>
        <label className={labelClass} style={labelStyle}>最大迭代次数</label>
        <input
          type="number"
          {...register('maxIterations', { required: true, min: 1, max: 100, valueAsNumber: true })}
          className={inputClass}
          style={inputStyle}
          placeholder="10"
          onBlur={handleSubmit(onSubmit)}
        />
        <p className="text-10 mt-1.5" style={{ color: '#6E6E73' }}>范围 1-100，默认 10 次</p>
      </div>
      <div>
        <label className={labelClass} style={labelStyle}>继续循环条件</label>
        <textarea
          {...register('condition')}
          rows={3}
          className={`${inputClass} resize-none font-mono text-xs`}
          style={inputStyle}
          placeholder='例如: iteration < 5 或 len(results) < 10'
          onBlur={handleSubmit(onSubmit)}
        />
        <p className="text-10 mt-1.5 leading-relaxed" style={{ color: '#6E6E73' }}>
          Python 表达式，返回 True 继续循环。可用变量：<code className="px-1 py-0.5 rounded" style={{ background: 'rgba(0,0,0,0.03)', color: '#6E6E73' }}>context</code>、<code className="px-1 py-0.5 rounded" style={{ background: 'rgba(0,0,0,0.03)', color: '#6E6E73' }}>iteration</code>、<code className="px-1 py-0.5 rounded" style={{ background: 'rgba(0,0,0,0.03)', color: '#6E6E73' }}>results</code>
        </p>
      </div>
      <div>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            {...register('exitOnFailure')}
            className="rounded"
            style={{ borderColor: 'rgba(0,0,0,0.06)' }}
            onChange={(e) => {
              setValue('exitOnFailure', e.target.checked, { shouldDirty: true });
              setTimeout(() => submitRef.current(), 0);
            }}
          />
          <span className="text-13 font-medium" style={{ color: '#1D1D1F' }}>任务失败时退出循环</span>
        </label>
      </div>
      <div>
        <label className={labelClass} style={labelStyle}>循环体任务</label>
        {taskNodes.length === 0 ? (
          <p className="text-xs" style={{ color: '#6E6E73' }}>暂无任务节点，请先添加任务</p>
        ) : (
          <div className="space-y-1.5 max-h-32 overflow-y-auto rounded-md p-2" style={{ border: '0.5px solid rgba(0,0,0,0.06)' }}>
            {taskNodes.map((tn) => {
              const taskName = (tn.data as Record<string, unknown>)?.name as string || tn.id;
              const checked = loopBodyIds.includes(tn.id);
              return (
                <label key={tn.id} className="flex items-center gap-2 text-xs cursor-pointer">
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => { toggleTaskId(tn.id); setTimeout(() => submitRef.current(), 0); }}
                    className="rounded"
                    style={{ borderColor: 'rgba(0,0,0,0.06)' }}
                  />
                  <span className="truncate" style={{ color: '#6E6E73' }}>{taskName}</span>
                </label>
              );
            })}
          </div>
        )}
        <p className="text-10 mt-1.5" style={{ color: '#6E6E73' }}>选择需要在循环中重复执行的任务</p>
      </div>
      <button type="submit" className="w-full flex items-center justify-center gap-2 py-2.5 text-13 font-medium radius-sm" style={{ background: '#0071E3', color: '#FFFFFF', border: 'none' }}>
        应用更改
      </button>
    </form>
  );
};

interface HumanReviewFormProps { nodeId: string; data: HumanReviewNodeData; }

const HumanReviewPropertyForm: React.FC<HumanReviewFormProps> = ({ nodeId, data }) => {
  const updateNodeData = useFlowStore((s) => s.updateNodeData);

  const { register, handleSubmit, watch, setValue } = useForm<HumanReviewNodeData>({
    defaultValues: {
      name: data.name || '',
      reviewType: data.reviewType || 'approval',
      prompt: data.prompt || '',
      options: data.options || [],
      timeoutSeconds: data.timeoutSeconds || undefined,
      timeoutAction: data.timeoutAction || 'reject',
    },
  });

  const reviewType = watch('reviewType');
  const options = watch('options') || [];

  const onSubmit = (formData: HumanReviewNodeData) => updateNodeData(nodeId, formData);
  const submitRef = useRef<() => void>(() => {});
  submitRef.current = () => { handleSubmit(onSubmit)(); };
  useEffect(() => { return () => { submitRef.current(); }; }, []);

  const addOption = () => {
    const next = [...options, ''];
    setValue('options', next, { shouldDirty: true });
  };

  const removeOption = (index: number) => {
    const next = options.filter((_, i) => i !== index);
    setValue('options', next, { shouldDirty: true });
    setTimeout(() => submitRef.current(), 0);
  };

  const updateOption = (index: number, value: string) => {
    const next = [...options];
    next[index] = value;
    setValue('options', next, { shouldDirty: true });
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label className={labelClass} style={labelStyle}>节点名称</label>
        <input {...register('name', { required: true })} className={inputClass} style={inputStyle} placeholder="例如：人工确认" onBlur={handleSubmit(onSubmit)} />
      </div>
      <div>
        <label className={labelClass} style={labelStyle}>审核类型</label>
        <select
          {...register('reviewType')}
          className={inputClass}
          style={inputStyle}
          onBlur={handleSubmit(onSubmit)}
        >
          <option value="approval">审批（通过/拒绝）</option>
          <option value="input">输入（用户提供内容）</option>
          <option value="selection">选择（从选项中选择）</option>
        </select>
      </div>
      <div>
        <label className={labelClass} style={labelStyle}>审核提示</label>
        <textarea
          {...register('prompt', { required: true })}
          rows={4}
          className={`${inputClass} resize-none`}
          style={inputStyle}
          placeholder="展示给审核人的提示信息，支持 {variable} 占位符..."
          onBlur={handleSubmit(onSubmit)}
        />
        <p className="text-10 mt-1.5 leading-relaxed" style={{ color: '#6E6E73' }}>
          支持 {'{variable}'} 占位符，执行时将替换为上下文变量
        </p>
      </div>
      {reviewType === 'selection' && (
        <div>
          <label className={labelClass} style={labelStyle}>选项列表</label>
          <div className="space-y-1.5">
            {options.map((opt, index) => (
              <div key={index} className="flex items-center gap-2">
                <input
                  className={inputClass + ' flex-1'}
                  style={inputStyle}
                  value={opt}
                  placeholder={`选项 ${index + 1}`}
                  onChange={(e) => updateOption(index, e.target.value)}
                  onBlur={handleSubmit(onSubmit)}
                />
                <button
                  type="button"
                  onClick={() => removeOption(index)}
                  className="p-1.5 radius-sm"
                  style={{ color: '#FF453A' }}
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
          <button
            type="button"
            onClick={addOption}
            className="mt-2 text-xs"
            style={{ color: '#0071E3' }}
          >
            + 添加选项
          </button>
        </div>
      )}
      <div>
        <label className={labelClass} style={labelStyle}>超时时间（秒）</label>
        <input
          type="number"
          {...register('timeoutSeconds', { valueAsNumber: true, min: 0 })}
          className={inputClass}
          style={inputStyle}
          placeholder="留空表示永不超时"
          onBlur={handleSubmit(onSubmit)}
        />
      </div>
      <div>
        <label className={labelClass} style={labelStyle}>超时动作</label>
        <select
          {...register('timeoutAction')}
          className={inputClass}
          style={inputStyle}
          onBlur={handleSubmit(onSubmit)}
        >
          <option value="reject">拒绝（终止流程）</option>
          <option value="approve">自动批准</option>
          <option value="skip">跳过（继续执行）</option>
        </select>
      </div>
      <button type="submit" className="w-full flex items-center justify-center gap-2 py-2.5 text-13 font-medium radius-sm" style={{ background: '#0071E3', color: '#FFFFFF', border: 'none' }}>
        应用更改
      </button>
    </form>
  );
};

/* P1-1: 知识库关联选择器组件 */
const KnowledgeBaseSelector: React.FC<{ agentId: string }> = ({ agentId }) => {
  const { data: kbs } = useQuery({
    queryKey: ['knowledge-bases'],
    queryFn: async () => (await apiClient.get('/knowledge-bases/')).data,
  });

  const [linkedIds, setLinkedIds] = useState<Set<string>>(new Set());

  // 判断是否为数据库 UUID（保存后的 agent 才有 UUID 格式 ID）
  const isUUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(agentId);

  // 获取已关联的知识库
  useEffect(() => {
    if (!agentId || !isUUID) return;
    apiClient.get(`/knowledge-bases/`).then(res => {
      const linked = new Set<string>();
      for (const kb of (res.data || [])) {
        if (kb.agent_mappings?.some((m: any) => m.agent_id === agentId)) {
          linked.add(kb.id);
        }
      }
      setLinkedIds(linked);
    }).catch(() => {});
  }, [agentId, isUUID]);

  const toggleLink = async (kbId: string) => {
    if (!isUUID) return;
    const isLinked = linkedIds.has(kbId);
    try {
      if (isLinked) {
        const mappingsRes = await apiClient.get(`/knowledge-bases/${kbId}/agent-mappings`);
        const mapping = (mappingsRes.data || []).find((m: any) => m.agent_id === agentId);
        if (mapping) {
          await apiClient.delete(`/knowledge-bases/${kbId}/agent-mappings/${mapping.id}`);
        }
        setLinkedIds(prev => { const s = new Set(prev); s.delete(kbId); return s; });
      } else {
        await apiClient.post(`/knowledge-bases/${kbId}/agent-mappings`, { agent_id: agentId });
        setLinkedIds(prev => new Set(prev).add(kbId));
      }
    } catch {}
  };

  if (!kbs || kbs.length === 0) return null;

  return (
    <div className="mb-3">
      <label className="block text-11 font-medium mb-1.5 flex items-center gap-1.5" style={{ color: '#6E6E73' }}>
        <BookOpen style={{ width: 12, height: 12 }} />
        知识库关联
      </label>
      {!isUUID ? (
        <p className="text-10" style={{ color: '#86868B' }}>
          保存工作流后即可关联知识库
        </p>
      ) : (
        <>
          <div className="flex flex-wrap gap-1.5">
            {kbs.map((kb: any) => (
              <button
                key={kb.id}
                type="button"
                onClick={() => toggleLink(kb.id)}
                className="flex items-center gap-1 px-2 py-1 rounded-md text-11 transition-all"
                style={{
                  background: linkedIds.has(kb.id) ? 'rgba(0,113,227,0.12)' : 'rgba(0,0,0,0.03)',
                  color: linkedIds.has(kb.id) ? '#0071E3' : '#6E6E73',
                  border: linkedIds.has(kb.id) ? '1px solid rgba(0,113,227,0.3)' : '1px solid rgba(0,0,0,0.08)',
                  cursor: 'pointer',
                }}
              >
                <Database style={{ width: 10, height: 10 }} />
                {kb.name}
                <span style={{ fontSize: 9, opacity: 0.6 }}>{kb.document_count || 0}doc</span>
              </button>
            ))}
          </div>
          <p className="text-10 mt-1" style={{ color: '#86868B' }}>
            关联后，Agent 执行时会自动检索知识库内容
          </p>
        </>
      )}
    </div>
  );
};

// ── 工作流模式属性表单 ──────────────────────────────────────

interface WorkflowPatternFormProps {
  nodeId: string;
  patternType: string;
  data: Record<string, unknown>;
}

const WorkflowPatternPropertyForm: React.FC<WorkflowPatternFormProps> = ({ nodeId, patternType, data }) => {
  const { updateNodeData } = useFlowStore();
  const { register, handleSubmit } = useForm({
    defaultValues: {
      name: (data.name as string) || '',
      description: (data.description as string) || '',
      // Router
      condition_field: (data.condition_field as string) || '',
      // Evaluator
      max_iterations: (data.max_iterations as number) || 5,
      evaluation_criteria: (data.evaluation_criteria as string) || '',
      // Parallel
      mode: (data.mode as string) || 'sectioning',
      // Prompt Chain
      pass_output: data.pass_output !== false,
    },
  });

  const onSubmit = (formData: Record<string, unknown>) => {
    updateNodeData(nodeId, { ...formData, patternType } as any);
  };
  const submitRef = useRef<() => void>(() => {});
  submitRef.current = () => { handleSubmit(onSubmit)(); };
  useEffect(() => { return () => { submitRef.current(); }; }, []);

  const typeLabel = {
    router: 'Router 路由',
    parallel_flow: 'Parallel 并行',
    orchestrator: 'Orchestrator 编排',
    evaluator: 'Evaluator 评估',
    prompt_chain: 'Prompt Chain 链式',
  }[patternType] || patternType;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label className={labelClass} style={labelStyle}>节点名称</label>
        <input {...register('name', { required: true })} className={inputClass} style={inputStyle} placeholder={typeLabel} onBlur={handleSubmit(onSubmit)} />
      </div>

      {patternType === 'evaluator' && (
        <>
          <div>
            <label className={labelClass} style={labelStyle}>最大迭代次数</label>
            <input
              type="number"
              {...register('max_iterations', { min: 1, max: 20, valueAsNumber: true })}
              className={inputClass}
              style={inputStyle}
              placeholder="5"
              onBlur={handleSubmit(onSubmit)}
            />
          </div>
          <div>
            <label className={labelClass} style={labelStyle}>评估标准</label>
            <textarea
              {...register('evaluation_criteria')}
              rows={3}
              className={`${inputClass} resize-none`}
              style={inputStyle}
              placeholder="描述评估质量和改进方向的标准..."
              onBlur={handleSubmit(onSubmit)}
            />
          </div>
        </>
      )}

      {patternType === 'router' && (
        <div>
          <label className={labelClass} style={labelStyle}>路由条件</label>
          <textarea
            {...register('condition_field')}
            rows={3}
            className={`${inputClass} resize-none font-mono text-xs`}
            style={inputStyle}
            placeholder='result["category"] == "A"'
            onBlur={handleSubmit(onSubmit)}
          />
          <p className="text-10 mt-1.5" style={{ color: '#6E6E73' }}>
            根据条件将任务路由到不同分支
          </p>
        </div>
      )}

      {patternType === 'parallel_flow' && (
        <div>
          <label className={labelClass} style={labelStyle}>并行模式</label>
          <select {...register('mode')} className={inputClass} style={inputStyle} onBlur={handleSubmit(onSubmit)}>
            <option value="sectioning">分段处理 (Sectioning)</option>
            <option value="voting">投票决策 (Voting)</option>
          </select>
        </div>
      )}

      {patternType === 'prompt_chain' && (
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            {...register('pass_output')}
            id="pass_output"
            className="w-4 h-4 rounded"
          />
          <label htmlFor="pass_output" className="text-13" style={{ color: '#1D1D1F' }}>
            传递上一步输出到下一步
          </label>
        </div>
      )}

      <div>
        <label className={labelClass} style={labelStyle}>描述</label>
        <textarea
          {...register('description')}
          rows={2}
          className={`${inputClass} resize-none`}
          style={inputStyle}
          placeholder="可选描述"
          onBlur={handleSubmit(onSubmit)}
        />
      </div>
    </form>
  );
};

// ── Event Flow 属性表单 ────────────────────────────────────────

interface EventFlowFormProps {
  nodeId: string;
  flowType: string;
  data: Record<string, unknown>;
}

const EventFlowPropertyForm: React.FC<EventFlowFormProps> = ({ nodeId, flowType, data }) => {
  const { updateNodeData } = useFlowStore();
  const { register, handleSubmit, watch } = useForm({
    defaultValues: {
      name: (data.name as string) || '',
      event_name: (data.event_name as string) || '',
      condition: (data.condition as string) || '',
      description: (data.description as string) || '',
    },
  });

  const onSubmit = (formData: Record<string, string>) => {
    updateNodeData(nodeId, { ...formData, flowType } as any);
  };
  const submitRef = useRef<() => void>(() => {});
  submitRef.current = () => { handleSubmit(onSubmit)(); };
  useEffect(() => { return () => { submitRef.current(); }; }, []);

  const typeLabel = flowType === 'start' ? '@start' : flowType === 'listen' ? '@listen' : '@router';
  const typeDesc = flowType === 'start'
    ? 'Flow 入口，标记方法为流程启动点'
    : flowType === 'listen'
      ? '监听指定事件，事件触发后执行方法'
      : '根据返回值条件路由到不同事件';

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label className={labelClass} style={labelStyle}>节点名称</label>
        <input {...register('name', { required: true })} className={inputClass} style={inputStyle} placeholder={typeLabel} onBlur={handleSubmit(onSubmit)} />
      </div>

      <div>
        <label className={labelClass} style={labelStyle}>事件名</label>
        <input
          {...register('event_name')}
          className={`${inputClass} font-mono text-xs`}
          style={inputStyle}
          placeholder={flowType === 'start' ? 'on_start' : 'my_event_name'}
          onBlur={handleSubmit(onSubmit)}
        />
        <p className="text-10 mt-1.5" style={{ color: '#6E6E73' }}>{typeDesc}</p>
      </div>

      {flowType === 'router_event' && (
        <div>
          <label className={labelClass} style={labelStyle}>路由条件</label>
          <textarea
            {...register('condition')}
            rows={3}
            className={`${inputClass} resize-none font-mono text-xs`}
            style={inputStyle}
            placeholder='result["status"] == "success"'
            onBlur={handleSubmit(onSubmit)}
          />
          <p className="text-10 mt-1.5 leading-relaxed" style={{ color: '#6E6E73' }}>
            Python 表达式，返回 True 触发 <code className="px-1 py-0.5 rounded" style={{ background: 'rgba(0,0,0,0.03)', color: '#6E6E73' }}>event_name</code> 事件
          </p>
        </div>
      )}

      <div>
        <label className={labelClass} style={labelStyle}>描述</label>
        <textarea
          {...register('description')}
          rows={2}
          className={`${inputClass} resize-none`}
          style={inputStyle}
          placeholder="可选描述"
          onBlur={handleSubmit(onSubmit)}
        />
      </div>
    </form>
  );
};

export default PropertyPanel;
