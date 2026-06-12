/* 执行监控页面 — 动态态 Cyber Theme 全面赛博化
 * 粒子背景 + 扫描线 + neon HUD + 打字机终端 + bloom 任务卡片
 */

import React, { useEffect, useState, useRef, useMemo, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, XCircle, RefreshCw, Clock, CheckCircle2, XCircleIcon, Loader2, SkipForward, Download, Shield, GitBranch, Box } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';

import { executionsApi } from '../api/executions';
import { crewsApi } from '../api/crews';
import { iterationsApi } from '../api/iterations';
import { apiClient } from '../api/client';
import { useExecutionMonitor } from '../hooks/useExecutionMonitor';
import { RealtimeThoughts } from '../components/monitor/RealtimeThoughts';
import { ConnectionStatus } from '../components/monitor/ConnectionStatus';
import { ExportModal } from '../components/editor/ExportModal';
import { useThemeStore } from '../stores/themeStore';
import { TunnelTransition } from '../components/motion/TunnelTransition';
import { parseUTC } from '../lib/utils';
import { ParticleField } from '../components/cyber/ParticleField';
import { TypewriterText } from '../components/cyber/TypewriterText';
import { IterationChat } from '../components/monitor/IterationChat';
import { CheckpointPanel } from '../components/monitor/CheckpointPanel';
import { TRACE_EVENT_LABELS } from '../types';
import type { Iteration } from '../types/iteration';

const STATUS_CONFIG: Record<string, { color: string; glow: string; icon: React.ReactNode; label: string }> = {
  pending: { color: '#71717A', glow: 'none', icon: <Clock className="w-3.5 h-3.5" />, label: '等待中' },
  running: { color: '#22D3EE', glow: '0 0 8px rgba(34,211,238,0.8)', icon: <Loader2 className="w-3.5 h-3.5 animate-spin" />, label: '执行中' },
  completed: { color: '#4ADE80', glow: '0 0 8px rgba(74,222,128,0.5)', icon: <CheckCircle2 className="w-3.5 h-3.5" />, label: '完成' },
  failed: { color: '#F87171', glow: '0 0 8px rgba(248,113,113,0.5)', icon: <XCircleIcon className="w-3.5 h-3.5" />, label: '失败' },
  cancelled: { color: '#FACC15', glow: '0 0 8px rgba(250,204,21,0.3)', icon: <XCircle className="w-3.5 h-3.5" />, label: '已取消' },
  skipped: { color: '#71717A', glow: 'none', icon: <SkipForward className="w-3.5 h-3.5" />, label: '跳过' },
  retrying: { color: '#FACC15', glow: '0 0 8px rgba(250,204,21,0.3)', icon: <RefreshCw className="w-3.5 h-3.5 animate-spin" />, label: '重试中' },
  paused: { color: '#C084FC', glow: '0 0 8px rgba(192,132,252,0.3)', icon: <Clock className="w-3.5 h-3.5" />, label: '暂停' },
};

// 卡片底板样式 — Precision HUD
const CARD_STYLE: React.CSSProperties = {
  background: 'rgba(255, 255, 255, 0.05)',
  border: '1px solid rgba(255, 255, 255, 0.1)',
  borderRadius: 12,
  padding: 20,
  backdropFilter: 'blur(12px)',
};

/* Neon 状态 Badge */
const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.pending;
  return (
    <span
      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium"
      style={{
        color: config.color,
        background: `${config.color}15`,
        border: `0.5px solid ${config.color}30`,
        boxShadow: config.glow,
        fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, system-ui, sans-serif",
      }}
    >
      {config.icon}
      {config.label}
    </span>
  );
};

/* 赛博任务卡片 — neon 边框 + bloom glow */
const CyberTaskCard: React.FC<{
  index: number;
  taskExec: Record<string, unknown>;
  isExpanded: boolean;
  onToggle: () => void;
}> = ({ index, taskExec, isExpanded, onToggle }) => {
  const te = taskExec as { id: string; task_name?: string; agent_name?: string; status: string; output?: string; error_message?: string; thoughts?: Array<{ type: string; content: string }>; cost_usd?: number; tokens_used?: number; started_at?: string; completed_at?: string };
  // 如果是 failed 且 error_message 包含"取消"，显示为"已取消"
  const status = te.status === 'failed' && te.error_message?.includes('取消') ? 'cancelled' : te.status;
  const statusConfig = STATUS_CONFIG[status] || STATUS_CONFIG.pending;

  // 计算任务执行时长
  const taskDuration = te.started_at && te.completed_at
    ? Math.floor((parseUTC(te.completed_at).getTime() - parseUTC(te.started_at).getTime()) / 1000)
    : null;

  const bloomAnimation = status === 'running'
    ? 'bloomPulse 2s ease-in-out infinite'
    : status === 'completed'
    ? 'bloomPulseGreen 3s ease-in-out infinite'
    : status === 'failed'
    ? 'bloomPulseRed 2s ease-in-out 1'
    : 'none';

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05, type: 'spring', stiffness: 120, damping: 15 }}
      onClick={onToggle}
      style={{
        cursor: 'pointer',
        background: 'rgba(255, 255, 255, 0.05)',
        border: `1px solid ${statusConfig.color}30`,
        borderRadius: 12,
        padding: '16px 20px',
        marginBottom: 12,
        backdropFilter: 'blur(12px)',
        animation: bloomAnimation,
        transition: 'border-color 0.3s, box-shadow 0.3s',
      }}
      whileHover={{
        borderColor: `${statusConfig.color}50`,
        boxShadow: `0 0 12px ${statusConfig.color}15`,
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{
            fontSize: 15,
            fontWeight: 600,
            color: '#F4F4F5',
            fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, system-ui, sans-serif",
          }}>
            {te.task_name || `Task ${index + 1}`}
          </div>
          <div style={{
            fontSize: 12,
            color: '#A1A1AA',
            fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, system-ui, sans-serif",
            marginTop: 4,
          }}>
            {te.agent_name || 'Unknown Agent'}
          </div>
        </div>
        <StatusBadge status={status} />
      </div>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            style={{ overflow: 'hidden' }}
          >
            <div style={{
              marginTop: 16,
              paddingTop: 16,
              borderTop: '0.5px solid rgba(255,255,255,0.06)',
            }}>
              {te.output && (
                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: 10, color: '#636366', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    输出结果
                  </div>
                  <div style={{
                    background: 'rgba(0, 0, 0, 0.5)',
                    borderRadius: 8,
                    padding: '12px 14px',
                    fontSize: 12,
                    color: '#A1A1A6',
                    whiteSpace: 'pre-wrap',
                    maxHeight: 240,
                    overflowY: 'auto',
                    fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, system-ui, sans-serif",
                    border: '0.5px solid rgba(0, 212, 255, 0.08)',
                    lineHeight: 1.6,
                  }}>
                    {te.output}
                  </div>
                </div>
              )}
              {te.error_message && (
                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: 10, color: '#FF453A', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    错误信息
                  </div>
                  <div style={{
                    background: 'rgba(255, 69, 58, 0.06)',
                    borderRadius: 8,
                    padding: '12px 14px',
                    fontSize: 12,
                    color: '#FF453A',
                    fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, system-ui, sans-serif",
                    border: '0.5px solid rgba(255, 69, 58, 0.15)',
                    lineHeight: 1.6,
                  }}>
                    {te.error_message}
                  </div>
                </div>
              )}
              {(te.cost_usd ?? 0) > 0 && (
                <div style={{
                  fontSize: 11,
                  color: '#FFD60A',
                  fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, system-ui, sans-serif",
                }}>
                  费用: ${Number(te.cost_usd).toFixed(4)} | Token: {(te.tokens_used ?? 0).toLocaleString()}
                </div>
              )}
              {taskDuration != null && (
                <div style={{
                  fontSize: 11,
                  color: '#22D3EE',
                  fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, system-ui, sans-serif",
                }}>
                  时长: {taskDuration}s
                </div>
              )}

              {/* 思考过程显示 */}
              {te.thoughts && te.thoughts.length > 0 && (
                <div style={{ marginTop: 12, paddingTop: 12, borderTop: '0.5px solid rgba(255,255,255,0.06)' }}>
                  <div style={{ fontSize: 10, color: '#636366', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    思考过程 ({te.thoughts.length} 步)
                  </div>
                  <div style={{
                    background: 'rgba(0, 0, 0, 0.5)',
                    borderRadius: 8,
                    padding: '12px 14px',
                    maxHeight: 200,
                    overflowY: 'auto',
                    fontSize: 11,
                    color: '#A1A1AA',
                    fontFamily: "'JetBrains Mono', 'SF Mono', monospace",
                    lineHeight: 1.6,
                  }}>
                    {te.thoughts.map((thought, i) => (
                      <div key={i} style={{ marginBottom: 8 }}>
                        <div style={{ color: '#FFD60A', fontSize: 10, marginBottom: 2 }}>
                          {thought.type === 'thinking' ? '💭 思考' : thought.type === 'tool_use' ? '🔧 工具调用' : thought.type === 'tool_result' ? '📊 工具结果' : thought.type}
                        </div>
                        <div style={{ color: '#D4D4D8' }}>{thought.content}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

/* Neon 统计数字 — Precision HUD 规范 */
const NeonStat: React.FC<{ label: string; value: string; color: string }> = ({ label, value, color }) => (
  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0' }}>
    <span style={{ fontSize: 14, color: '#A1A1AA', fontFamily: "'JetBrains Mono', 'SF Mono', monospace" }}>{label}</span>
    <span style={{
      fontSize: 18,
      fontWeight: 700,
      color,
      fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, system-ui, sans-serif",
      textShadow: `0 0 10px ${color}50`,
      letterSpacing: '-0.02em',
    }}>
      {value}
    </span>
  </div>
);

/** 工具名 → 中文名映射（覆盖内置 + MCP 工具） */
const TOOL_NAME_CN: Record<string, string> = {
  // 内置工具
  file_write: '写入文件', file_read: '读取文件',
  code_execute: '执行代码', shell_execute: '执行命令',
  database_query: '数据库查询', api_call: '调用接口',
  web_search: '网络搜索', image_generation: '生成图片',
  text_analysis: '文本分析',
  // MCP Local-FS 工具
  fs_write: '写入文件', fs_read: '读取文件',
  fs_list: '浏览目录', fs_info: '查看文件信息',
  fs_mkdir: '创建文件夹', fs_delete: '删除文件',
  fs_move: '移动文件', fs_copy: '复制文件',
  // MCP Doc 工具
  doc_read: '读取文档', doc_write: '创建文档',
  doc_edit: '编辑文档', doc_list: '浏览文档列表',
  docx_read: '读取文档', docx_create: '创建文档',
  docx_edit: '编辑文档', docx_list: '浏览文档列表',
  docx_delete: '删除文档',
  // MCP 其他常见工具
  calculator: '计算', execute_workflow: '运行工作流',
  list_workflows: '查看工作流列表', get_execution_status: '查看执行状态',
  send_message: '发送消息', read_page: '读取网页',
  search: '搜索',
};

/** 工具名 → 中文 */
function friendlyToolName(toolName: string): string {
  return TOOL_NAME_CN[toolName] || toolName;
}

/** 将工具名+参数转为人类可读的审批描述 */
function friendlyToolDescription(toolName: string, args: Record<string, unknown> | undefined): string {
  const cnName = friendlyToolName(toolName);
  if (!args) return `请求${cnName}`;
  const a = args as Record<string, any>;
  const filePath: string = a.file_path || a.path || a.source || '';
  const fileName = filePath.split(/[/\\]/).pop() || '';
  const ext = fileName.split('.').pop()?.toLowerCase();

  // 文件写入类（file_write / fs_write / doc_write / docx_create）
  if (['file_write', 'fs_write', 'doc_write', 'docx_create'].includes(toolName)) {
    if (ext === 'docx' || ext === 'doc') return `请求创建 Word 文档（${fileName}）`;
    if (ext === 'xlsx' || ext === 'xls') return `请求创建 Excel 表格（${fileName}）`;
    if (ext === 'pdf') return `请求创建 PDF 文档（${fileName}）`;
    if (ext === 'pptx' || ext === 'ppt') return `请求创建 PPT 演示文稿（${fileName}）`;
    if (ext === 'csv') return `请求创建 CSV 数据表（${fileName}）`;
    if (ext === 'txt' || ext === 'md') return `请求写入文本文件（${fileName}）`;
    if (ext === 'json') return `请求写入 JSON 文件（${fileName}）`;
    if (ext === 'py' || ext === 'js' || ext === 'ts') return `请求写入代码文件（${fileName}）`;
    return `请求写入文件（${fileName || filePath}）`;
  }

  // 文件读取类
  if (['file_read', 'fs_read', 'doc_read', 'docx_read'].includes(toolName)) {
    return `请求读取文件（${fileName || filePath}）`;
  }

  // 目录浏览
  if (['fs_list', 'doc_list'].includes(toolName)) {
    return `请求浏览文件夹（${filePath || a.directory || '当前目录'}）`;
  }

  // 文件操作
  if (toolName === 'fs_mkdir') return `请求创建文件夹（${a.name || a.path || ''}）`;
  if (toolName === 'fs_delete') return `请求删除文件（${fileName || a.path || ''}）`;
  if (toolName === 'fs_move') return `请求移动文件（${fileName}）`;
  if (toolName === 'fs_copy') return `请求复制文件（${fileName}）`;
  if (toolName === 'fs_info') return `请求查看文件信息（${fileName}）`;

  // 文档编辑
  if (toolName === 'doc_edit') return `请求编辑文档（${fileName || ''}）`;

  // 系统命令
  if (toolName === 'shell_execute') return `请求执行命令：${(a.command || '').toString().slice(0, 60)}`;
  if (toolName === 'code_execute') return `请求执行代码`;

  // 计算器
  if (toolName === 'calculator') return `请求计算：${a.expression || a.input || ''}`;

  // 网络 / API
  if (toolName === 'web_search' || toolName === 'search') return `请求搜索：${a.query || a.search || ''}`;
  if (toolName === 'api_call') return `请求调用外部接口`;
  if (toolName === 'read_page') return `请求读取网页`;

  // 工作流
  if (toolName === 'execute_workflow') return `请求运行工作流`;
  if (toolName === 'send_message') return `请求发送消息`;

  // 兜底：用中文名 + 可读参数
  const key = a.description || a.message || a.expression || a.query || a.command || filePath;
  if (key) return `请求${cnName}（${String(key).slice(0, 50)}）`;
  return `请求${cnName}`;
}

const ExecutionView: React.FC = () => {
  const { executionId } = useParams<{ executionId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [expandedTask, setExpandedTask] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'timeline' | 'realtime'>('realtime');
  const [showExportModal, setShowExportModal] = useState(false);
  const autoScrollRef = useRef<HTMLDivElement>(null);
  const prevStatusRef = useRef<string | null>(null);
  const [windowSize, setWindowSize] = useState({ w: window.innerWidth, h: window.innerHeight });
  const waitStartTimeRef = useRef<number>(Date.now());
  const [waitTooLong, setWaitTooLong] = useState(false);
  const [iterations, setIterations] = useState<Iteration[]>([]);
  const [isRefining, setIsRefining] = useState(false);
  const [dismissedApprovals, setDismissedApprovals] = useState<Set<string>>(new Set());

  // 进入执行页面自动切换到赛博模式
  useEffect(() => {
    useThemeStore.getState().enterCyberMode();
  }, []);

  // 退出时触发逆向隧道动画（总时长 ~2.5s）
  const handleBackWithTransition = useCallback(() => {
    // 等待覆盖层完全遮住屏幕后再切换主题，避免白闪
    setTimeout(() => {
      useThemeStore.getState().setTransitioning('to-static');
    }, 200);
    // 等待退出动画全部完成（1.5s 光痕 + 0.3s 闪光 + 0.2s 覆盖层淡出 ≈ 2.5s）再导航
    setTimeout(() => {
      useThemeStore.getState().exitCyberMode();
      navigate('/');
    }, 3000);
  }, [navigate]);

  // 窗口尺寸跟踪 (ParticleField 需要)
  useEffect(() => {
    const handleResize = () => setWindowSize({ w: window.innerWidth, h: window.innerHeight });
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const { data: execution, isLoading: execLoading } = useQuery({
    queryKey: ['execution', executionId],
    queryFn: () => executionsApi.get(executionId!),
    enabled: !!executionId,
    refetchInterval: (query) => {
      const data = query.state.data as any;
      if (!data) return 2000;
      return ['pending', 'running', 'waiting_review'].includes(data.status) ? 2000 : false;
    },
  });

  // WebSocket实时监控 — 仅在执行中保持连接
  // 任务执行中或有活跃迭代时保持 WebSocket 连接
  const isExecRunning = execution ? (
    ['pending', 'running', 'waiting_review'].includes(execution.status) ||
    isRefining
  ) : false;
  const {
    isConnected,
    events: realtimeEvents,
    progress: _realtimeProgress,
    cost: realtimeCost,
  } = useExecutionMonitor({
    executionId: executionId || '',
    enabled: !!executionId,
    isRunning: isExecRunning,
  });

  // 实时执行时间计时器
  const [elapsedSeconds, setElapsedSeconds] = useState<number | null>(null);
  useEffect(() => {
    if (!execution) return;
    const isRunning = ['pending', 'running', 'waiting_review'].includes(execution.status);
    if (isRunning && execution.started_at) {
      const updateElapsed = () => {
        setElapsedSeconds(Math.floor((Date.now() - parseUTC(execution.started_at!).getTime()) / 1000));
      };
      updateElapsed();
      const interval = setInterval(updateElapsed, 1000);
      return () => clearInterval(interval);
    } else if (execution.completed_at && execution.started_at) {
      setElapsedSeconds(Math.floor((parseUTC(execution.completed_at).getTime() - parseUTC(execution.started_at).getTime()) / 1000));
    } else {
      setElapsedSeconds(null);
    }
  }, [execution?.started_at, execution?.completed_at, execution?.status]);

  const isExecuting = execution ? ['pending', 'running', 'waiting_review'].includes(execution.status) : false;
  const { data: taskExecutions } = useQuery({
    queryKey: ['task-executions', executionId],
    queryFn: () => executionsApi.getTaskExecutions(executionId!),
    enabled: !!executionId,
    refetchInterval: isExecuting ? 2000 : false,
  });

  // 超时保护: 30秒无任务则标记
  useEffect(() => {
    if (isExecuting && (!taskExecutions || taskExecutions.length === 0)) {
      const elapsed = Date.now() - waitStartTimeRef.current;
      if (elapsed > 30000) {
        setWaitTooLong(true);
      } else {
        const timer = setTimeout(() => setWaitTooLong(true), 30000 - elapsed);
        return () => clearTimeout(timer);
      }
    } else {
      setWaitTooLong(false);
      waitStartTimeRef.current = Date.now();
    }
  }, [isExecuting, taskExecutions]);

  useEffect(() => {
    if (!execution) return;
    const cur = execution.status;
    const prev = prevStatusRef.current;
    prevStatusRef.current = cur;
    if (prev === 'running' && !['pending', 'running', 'waiting_review'].includes(cur)) {
      queryClient.invalidateQueries({ queryKey: ['task-executions', executionId] });
    }
  }, [execution?.status, executionId, queryClient]);

  const { data: crew } = useQuery({
    queryKey: ['crew', execution?.crew_id],
    queryFn: () => crewsApi.get(execution!.crew_id),
    enabled: !!execution?.crew_id,
  });

  // 获取迭代列表
  useEffect(() => {
    if (executionId) {
      iterationsApi.list(executionId).then(setIterations).catch(() => {});
    }
  }, [executionId]);

  // 创建迭代回调
  const handleRefine = useCallback(async (feedback: string, mode: 'reexecute' | 'incremental') => {
    if (!executionId) return;
    setIsRefining(true);
    try {
      const newIteration = await iterationsApi.create(executionId, { feedback, mode });
      // 立即刷新列表显示 pending 状态
      let updatedIterations = await iterationsApi.list(executionId);
      setIterations(updatedIterations);

      // 轮询等待迭代完成（最多 120 秒）
      const iterId = newIteration.id;
      const maxPolls = 60;
      for (let i = 0; i < maxPolls; i++) {
        await new Promise(r => setTimeout(r, 2000));
        updatedIterations = await iterationsApi.list(executionId);
        setIterations(updatedIterations);
        const current = updatedIterations.find(it => it.id === iterId);
        if (current && (current.status === 'completed' || current.status === 'failed')) {
          break;
        }
      }
    } catch (error) {
      console.error('Failed to create iteration:', error);
    } finally {
      setIsRefining(false);
    }
  }, [executionId]);

  useEffect(() => {
    if (autoScrollRef.current) {
      autoScrollRef.current.scrollTop = autoScrollRef.current.scrollHeight;
    }
  }, [execution?.trace]);

  const handleCancel = async () => {
    if (!executionId) return;
    try {
      await executionsApi.cancel(executionId);
      toast.success('已取消执行');
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      toast.error(e.response?.data?.detail || '取消失败');
    }
  };

  // 打字机日志 — 从已完成任务的 thoughts 提取 reasoning 内容
  const logLines = useMemo(() => {
    const lines: string[] = [];
    // 从已完成的任务提取 reasoning 思考内容
    if (taskExecutions && taskExecutions.length > 0) {
      for (const te of taskExecutions) {
        const teData = te as { task_name?: string; agent_name?: string; thoughts?: Array<{ type: string; content: string }> };
        if (teData.thoughts && teData.thoughts.length > 0) {
          const agentLabel = teData.agent_name || teData.task_name || 'Agent';
          for (const t of teData.thoughts) {
            if (t.content) {
              lines.push(`[${agentLabel}] ${t.content}`);
            }
          }
        }
      }
    }
    // 如果没有 thoughts，使用实时事件中的 agent.thinking
    if (lines.length === 0) {
      const thinkingEvents = realtimeEvents.filter((e) => e.type === 'agent.thinking');
      for (const e of thinkingEvents) {
        const content = e.data?.content || e.data?.step || '';
        const agent = e.agentName ? `[${e.agentName}]` : '>';
        if (content) lines.push(`${agent} ${content}`);
      }
    }
    return lines;
  }, [taskExecutions, realtimeEvents]);

  if (execLoading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#000' }}>
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          style={{
            width: 32, height: 32, borderRadius: '50%',
            border: '2px solid rgba(0,212,255,0.15)',
            borderTopColor: '#00D4FF',
            boxShadow: '0 0 15px rgba(0,212,255,0.2)',
          }}
        />
      </div>
    );
  }

  if (!execution) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#000' }}>
        <p style={{ color: '#636366', fontFamily: "'JetBrains Mono', monospace" }}>执行记录不存在</p>
      </div>
    );
  }

  const isRunning = ['pending', 'running', 'waiting_review'].includes(execution.status);
  const totalTasks = taskExecutions?.length || 0;
  const completedTasks = taskExecutions?.filter((te) => ['completed', 'skipped'].includes(te.status)).length || 0;
  const progressPct = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : (isRunning ? 0 : 100);

  const progressColor = isRunning ? '#22D3EE'
    : execution.status === 'completed' ? '#4ADE80'
    : execution.status === 'failed' ? '#F87171' : '#71717A';

  return (
    <TunnelTransition>
    <div style={{ minHeight: '100vh', background: '#000000', position: 'relative', overflow: 'hidden' }}>
      {/* 粒子背景 */}
      <ParticleField width={windowSize.w} height={windowSize.h} />

      {/* 扫描线叠加 — 带呼吸感的 CRT 效果 */}
      <div style={{
        position: 'fixed', inset: 0, zIndex: 1, pointerEvents: 'none',
        background: 'repeating-linear-gradient(0deg, transparent, transparent 3px, rgba(0,212,238,0.01) 3px, rgba(0,212,238,0.01) 6px)',
        animation: 'crtFlicker 5s ease-in-out infinite',
      }} />

      {/* 全局呼吸光晕 — 运行态环境氛围（纯 opacity，不抖动） */}
      {isRunning && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none',
          background: 'radial-gradient(ellipse at 30% 50%, rgba(0,212,238,0.04) 0%, transparent 50%), radial-gradient(ellipse at 70% 50%, rgba(192,132,252,0.03) 0%, transparent 50%)',
          animation: 'ambientPulse 4s ease-in-out infinite',
        }} />
      )}

      {/* Header — neon HUD 带呼吸边框 */}
      <header style={{
        position: 'relative', zIndex: 10,
        background: 'rgba(0, 0, 0, 0.85)',
        backdropFilter: 'blur(40px) saturate(1.8)',
        WebkitBackdropFilter: 'blur(40px) saturate(1.8)',
        borderBottom: isRunning ? '1px solid rgba(0, 212, 255, 0.15)' : '0.5px solid rgba(255, 255, 255, 0.06)',
        padding: '12px 20px',
        boxShadow: isRunning ? '0 1px 20px rgba(0, 212, 255, 0.06)' : 'none',
        transition: 'border-color 1s ease, box-shadow 1s ease',
      }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', display: 'flex', alignItems: 'center', gap: 16 }}>
          <motion.button
            onClick={handleBackWithTransition}
            whileHover={{ backgroundColor: 'rgba(0,212,255,0.08)', color: '#00D4FF' }}
            whileTap={{ scale: 0.97 }}
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '6px 12px', borderRadius: 8,
              color: '#A1A1A6', background: 'transparent', border: 'none',
              fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, system-ui, sans-serif", fontSize: 13,
              cursor: 'pointer',
            }}
          >
            <ArrowLeft style={{ width: 14, height: 14 }} />
            返回
          </motion.button>

          <div style={{ flex: 1 }}>
            <h1 style={{
              fontSize: 17, fontWeight: 600, color: '#F4F4F5',
              fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, system-ui, sans-serif",
            }}>
              {crew?.name || '工作流'}
              <span style={{ color: '#A1A1AA', fontWeight: 400 }}> — 执行监控</span>
            </h1>
            <p style={{ fontSize: 11, color: '#71717A', fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, system-ui, sans-serif", marginTop: 2 }}>
              ID: {execution.id}
            </p>
          </div>

          <StatusBadge status={execution.status} />

          {/* 安全指示器 */}
          <div style={{ display: 'flex', gap: 6 }}>
            {/* 审批模式 */}
            {(crew as any)?.approval_mode && (
              <span style={{
                display: 'inline-flex', alignItems: 'center', gap: 4,
                padding: '3px 8px', borderRadius: 6,
                fontSize: 10, fontWeight: 500,
                color: (crew as any).approval_mode === 'full_auto' ? '#FF453A' : '#A1A1A6',
                background: (crew as any).approval_mode === 'full_auto' ? 'rgba(255,69,58,0.1)' : 'rgba(255,255,255,0.05)',
                border: `0.5px solid ${(crew as any).approval_mode === 'full_auto' ? 'rgba(255,69,58,0.2)' : 'rgba(255,255,255,0.08)'}`,
              }}>
                <Shield style={{ width: 10, height: 10 }} />
                {(crew as any).approval_mode === 'safe' ? '限制' : (crew as any).approval_mode === 'semi_auto' ? '默认' : '完全'}
              </span>
            )}
            {/* Worktree 隔离 */}
            {(execution as any)?.worktree_path && (
              <span style={{
                display: 'inline-flex', alignItems: 'center', gap: 4,
                padding: '3px 8px', borderRadius: 6,
                fontSize: 10, fontWeight: 500,
                color: '#4ADE80',
                background: 'rgba(74,222,128,0.08)',
                border: '0.5px solid rgba(74,222,128,0.15)',
              }}>
                <GitBranch style={{ width: 10, height: 10 }} />
                隔离
              </span>
            )}
            {/* 沙箱保护 — 仅在非 none 模式下显示 */}
            {(execution as any)?.sandbox_type && (execution as any).sandbox_type !== 'none' && (
              <span style={{
                display: 'inline-flex', alignItems: 'center', gap: 4,
                padding: '3px 8px', borderRadius: 6,
                fontSize: 10, fontWeight: 500,
                color: '#C084FC',
                background: 'rgba(192,132,252,0.08)',
                border: '0.5px solid rgba(192,132,252,0.15)',
              }}>
                <Box style={{ width: 10, height: 10 }} />
                沙箱:{(execution as any).sandbox_type}
              </span>
            )}
          </div>

          {/* Neon 进度条 */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 140 }}>
            <div style={{
              flex: 1, height: 4, borderRadius: 2,
              background: 'rgba(255,255,255,0.06)',
              overflow: 'hidden',
            }}>
              <motion.div
                animate={{
                  width: `${progressPct}%`,
                  boxShadow: isRunning
                    ? [`0 0 8px ${progressColor}40, 0 0 20px ${progressColor}20`, `0 0 15px ${progressColor}70, 0 0 35px ${progressColor}35`, `0 0 8px ${progressColor}40, 0 0 20px ${progressColor}20`]
                    : `0 0 8px ${progressColor}60, 0 0 20px ${progressColor}30`,
                }}
                transition={isRunning
                  ? { width: { duration: 0.5, ease: 'easeOut' }, boxShadow: { duration: 2, repeat: Infinity, ease: 'easeInOut' } }
                  : { duration: 0.5, ease: 'easeOut' }
                }
                style={{
                  height: '100%', borderRadius: 2,
                  background: isRunning
                    ? `linear-gradient(90deg, ${progressColor}, ${progressColor}CC, ${progressColor})`
                    : `linear-gradient(90deg, ${progressColor}, ${progressColor}CC)`,
                  backgroundSize: isRunning ? '200% 100%' : '100% 100%',
                  animation: isRunning ? 'dataStream 2s linear infinite' : 'none',
                }}
              />
            </div>
            <span style={{
              fontSize: 11, color: '#636366',
              fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, system-ui, sans-serif",
              whiteSpace: 'nowrap',
            }}>
              {completedTasks}/{totalTasks}
            </span>
          </div>

          {isRunning && (
            <motion.button
              onClick={handleCancel}
              whileHover={{ borderColor: 'rgba(255,69,58,0.4)', color: '#FF453A', boxShadow: '0 0 12px rgba(255,69,58,0.2)' }}
              whileTap={{ scale: 0.97 }}
              style={{
                display: 'flex', alignItems: 'center', gap: 6,
                padding: '6px 14px', borderRadius: 8,
                color: '#FF453A', background: 'transparent',
                border: '0.5px solid rgba(255,69,58,0.2)',
                fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, system-ui, sans-serif", fontSize: 12,
                cursor: 'pointer',
              }}
            >
              <XCircle style={{ width: 14, height: 14 }} /> 取消
            </motion.button>
          )}

          {!isRunning && (
            <motion.button
              onClick={() => setShowExportModal(true)}
              whileHover={{ borderColor: 'rgba(0,212,255,0.3)', color: '#00D4FF' }}
              whileTap={{ scale: 0.97 }}
              style={{
                display: 'flex', alignItems: 'center', gap: 6,
                padding: '6px 14px', borderRadius: 8,
                color: '#A1A1A6', background: 'transparent',
                border: '0.5px solid rgba(255,255,255,0.08)',
                fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, system-ui, sans-serif", fontSize: 12,
                cursor: 'pointer',
              }}
            >
              <Download style={{ width: 14, height: 14 }} /> 导出
            </motion.button>
          )}
        </div>
      </header>

      {/* 主内容区 */}
      <main style={{
        position: 'relative', zIndex: 5,
        maxWidth: 1200, margin: '0 auto', padding: '32px 20px',
        display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 24,
      }}>
        {/* 左侧：任务时间线 / 实时监控 */}
        <div>
          {/* 标签页切换 */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 24,
            borderBottom: '0.5px solid rgba(255,255,255,0.06)',
            marginBottom: 24,
          }}>
            {(['realtime', 'timeline'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                style={{
                  paddingBottom: 8, paddingLeft: 4, paddingRight: 4,
                  fontSize: 13, fontWeight: 500,
                  color: activeTab === tab ? '#00D4FF' : '#636366',
                  background: 'transparent', border: 'none',
                  borderBottom: activeTab === tab ? '2px solid #00D4FF' : '2px solid transparent',
                  cursor: 'pointer',
                  fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, system-ui, sans-serif",
                  transition: 'color 0.2s, border-color 0.2s',
                  display: 'flex', alignItems: 'center', gap: 8,
                }}
              >
                {tab === 'timeline' ? '任务时间线' : '实时监控'}
                {tab === 'realtime' && (
                  <span style={{
                    width: 6, height: 6, borderRadius: '50%',
                    background: isConnected ? '#30D158' : '#FF453A',
                    boxShadow: isConnected ? '0 0 6px rgba(48,209,88,0.5)' : 'none',
                    animation: isConnected ? 'statusPulse 2s ease-in-out infinite' : 'none',
                  }} />
                )}
              </button>
            ))}
          </div>

          {/* 时间线内容 */}
          {activeTab === 'timeline' && (
            <div ref={autoScrollRef} style={{ maxHeight: 'calc(100vh - 250px)', overflowY: 'auto' }}>
              {taskExecutions && taskExecutions.length > 0 ? (
                taskExecutions.map((te, i) => (
                  <CyberTaskCard
                    key={te.id}
                    index={i}
                    taskExec={te as unknown as Record<string, unknown>}
                    isExpanded={expandedTask === te.id}
                    onToggle={() => setExpandedTask(expandedTask === te.id ? null : te.id)}
                  />
                ))
              ) : isRunning ? (
                <div style={{ textAlign: 'center', padding: '60px 0' }}>
                  {!waitTooLong ? (
                    <>
                      <motion.div
                        animate={{ scale: [1, 1.1, 1], opacity: [0.4, 0.8, 0.4] }}
                        transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
                        style={{
                          width: 48, height: 48, borderRadius: '50%', margin: '0 auto 20px',
                          border: '2px solid rgba(0, 212, 255, 0.2)',
                          borderTopColor: '#00D4FF',
                          boxShadow: '0 0 20px rgba(0, 212, 255, 0.15)',
                        }}
                      />
                      <p style={{
                        fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, system-ui, sans-serif", fontSize: 13,
                        color: '#00D4FF', animation: 'neonFlicker 2s ease-in-out infinite',
                      }}>
                        正在初始化任务队列...
                      </p>
                      <p style={{
                        fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, system-ui, sans-serif", fontSize: 11,
                        color: '#71717A', marginTop: 8,
                      }}>
                        Agent 正在准备执行环境
                      </p>
                    </>
                  ) : (
                    <>
                      <div style={{
                        width: 48, height: 48, borderRadius: '50%', margin: '0 auto 20px',
                        border: '2px solid rgba(250, 204, 21, 0.3)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        color: '#FACC15', fontSize: 20,
                      }}>!</div>
                      <p style={{
                        fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, system-ui, sans-serif", fontSize: 13,
                        color: '#FACC15',
                      }}>
                        任务初始化超时
                      </p>
                      <p style={{
                        fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, system-ui, sans-serif", fontSize: 11,
                        color: '#71717A', marginTop: 8,
                      }}>
                        后端执行引擎可能未启动，请检查后端服务和日志
                      </p>
                      <button
                        onClick={() => { waitStartTimeRef.current = Date.now(); setWaitTooLong(false); }}
                        style={{
                          marginTop: 16, padding: '6px 16px', borderRadius: 8,
                          background: 'rgba(250, 204, 21, 0.1)',
                          border: '1px solid rgba(250, 204, 21, 0.3)',
                          color: '#FACC15', fontSize: 12,
                          fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, system-ui, sans-serif",
                          cursor: 'pointer',
                        }}
                      >
                        重新等待
                      </button>
                    </>
                  )}
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '48px 0', color: '#48484A' }}>
                  <p style={{ fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, system-ui, sans-serif", fontSize: 13 }}>暂无任务执行记录</p>
                </div>
              )}
            </div>
          )}

          {/* 实时监控标签页 */}
          {activeTab === 'realtime' && (
            <div style={CARD_STYLE}>
              <RealtimeThoughts events={realtimeEvents} />
            </div>
          )}

          {/* 打字机终端日志 */}
          {logLines.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3, type: 'spring', stiffness: 120, damping: 15 }}
              style={{ marginTop: 24 }}
            >
              <div style={{
                fontSize: 10, color: '#48484A', marginBottom: 8,
                textTransform: 'uppercase', letterSpacing: '0.08em',
                fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, system-ui, sans-serif",
              }}>
                MATRIX TERMINAL
              </div>
              <TypewriterText
                text={logLines.slice(-20).join('\n')}
                speed={15}
                showScanlines={true}
              />
            </motion.div>
          )}

          {/* 迭代对话 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, type: 'spring', stiffness: 120, damping: 15 }}
            style={{ marginTop: 24 }}
          >
            <IterationChat
              executionId={executionId || ''}
              iterations={iterations}
              onRefine={handleRefine}
              isRefining={isRefining}
              executionStatus={execution?.status || 'pending'}
            />
          </motion.div>
        </div>

        {/* 右侧：统计和控制面板 */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* 统计卡片 — 呼吸边框 */}
          <motion.div
            animate={isRunning ? {
              borderColor: ['rgba(34,211,238,0.1)', 'rgba(34,211,238,0.25)', 'rgba(34,211,238,0.1)'],
              boxShadow: ['0 0 0px rgba(34,211,238,0)', '0 0 15px rgba(34,211,238,0.08)', '0 0 0px rgba(34,211,238,0)'],
            } : {}}
            transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
            style={CARD_STYLE}
          >
            <div style={{
              fontSize: 11, color: '#A1A1AA', marginBottom: 16,
              textTransform: 'uppercase', letterSpacing: '0.1em',
              fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, system-ui, sans-serif", fontWeight: 500,
            }}>
              执行统计
            </div>
            <NeonStat
              label="费用"
              value={`$${Number(realtimeCost?.totalCost?.replace('$', '') || execution.total_cost_usd || 0).toFixed(4)}`}
              color="#FACC15"
            />
            <div style={{ height: 0, borderTop: '0.5px solid rgba(255,255,255,0.04)' }} />
            <NeonStat
              label="Token 使用"
              value={(realtimeCost?.totalTokens || execution.total_tokens_used || 0).toLocaleString()}
              color="#C084FC"
            />
            <div style={{ height: 0, borderTop: '0.5px solid rgba(255,255,255,0.04)' }} />
            <NeonStat
              label="时长"
              value={elapsedSeconds != null ? `${elapsedSeconds}s` : '--'}
              color="#22D3EE"
            />
          </motion.div>

          {/* 连接状态 */}
          <div style={CARD_STYLE}>
            <div style={{
              fontSize: 11, color: '#A1A1AA', marginBottom: 12,
              textTransform: 'uppercase', letterSpacing: '0.1em',
              fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, system-ui, sans-serif", fontWeight: 500,
            }}>
              连接状态
            </div>
            <ConnectionStatus isConnected={isConnected} />
          </div>

          {/* 审批请求面板 */}
          {(() => {
            const approvalEvents = realtimeEvents.filter(
              (e) => e.type === 'system.warning' && e.data?.approval_request_id && !dismissedApprovals.has(e.data.approval_request_id)
            );
            const pendingApproval = approvalEvents[approvalEvents.length - 1];
            if (!pendingApproval) return null;
            const d = pendingApproval.data;
            const friendlyDesc = friendlyToolDescription(d.tool_name, d.tool_args);
            const riskLabels: Record<string, string> = { low: '低', medium: '中', high: '高', critical: '极高' };
            return (
              <motion.div
                key={d.approval_request_id}
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                style={{
                  ...CARD_STYLE,
                  border: '1px solid rgba(255, 159, 10, 0.3)',
                  background: 'rgba(255, 159, 10, 0.06)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
                  <span style={{ fontSize: 18 }}>⚠️</span>
                  <div>
                    <div style={{ fontSize: 14, fontWeight: 600, color: '#FF9F0A', fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif" }}>
                      需要审批
                    </div>
                    <div style={{ fontSize: 12, color: '#D4D4D8', fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif", marginTop: 4 }}>
                      {friendlyDesc}
                    </div>
                    <div style={{ fontSize: 10, color: '#71717A', fontFamily: "'JetBrains Mono', monospace", marginTop: 2 }}>
                      操作: {friendlyToolName(d.tool_name)} · 风险等级: {riskLabels[d.risk_level] || d.risk_level}
                    </div>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={async () => {
                      try {
                        await apiClient.post(`/approvals/${d.approval_request_id}/reject`, { reason: '用户拒绝' });
                        setDismissedApprovals(prev => new Set(prev).add(d.approval_request_id));
                        toast.error('已拒绝工具调用');
                      } catch (err: any) {
                        toast.error(err.response?.data?.detail || '拒绝失败');
                      }
                    }}
                    style={{
                      flex: 1, padding: '10px 16px', borderRadius: 10,
                      background: 'rgba(255,69,58,0.1)', color: '#FF453A',
                      border: '0.5px solid rgba(255,69,58,0.2)',
                      fontSize: 13, fontWeight: 600, cursor: 'pointer',
                      fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif",
                    }}
                  >
                    ✕ 拒绝
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={async () => {
                      try {
                        await apiClient.post(`/approvals/${d.approval_request_id}/approve`);
                        setDismissedApprovals(prev => new Set(prev).add(d.approval_request_id));
                        toast.success('已批准工具调用');
                      } catch (err: any) {
                        toast.error(err.response?.data?.detail || '批准失败');
                      }
                    }}
                    style={{
                      flex: 1, padding: '10px 16px', borderRadius: 10,
                      background: '#30D158', color: '#fff',
                      border: 'none',
                      fontSize: 13, fontWeight: 600, cursor: 'pointer',
                      fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif",
                    }}
                  >
                    ✓ 批准
                  </motion.button>
                </div>
              </motion.div>
            );
          })()}

          {/* 时间旅行调试 - 检查点面板 */}
          <CheckpointPanel
            executionId={executionId!}
            status={execution?.status || ''}
            onStatusChange={() => queryClient.invalidateQueries({ queryKey: ['execution', executionId] })}
          />

          {/* 最近事件 */}
          {realtimeEvents && realtimeEvents.length > 0 && (
            <div style={CARD_STYLE}>
              <div style={{
                fontSize: 11, color: '#A1A1AA', marginBottom: 12,
                textTransform: 'uppercase', letterSpacing: '0.1em',
                fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, system-ui, sans-serif", fontWeight: 500,
              }}>
                最近事件
              </div>
              <div style={{ maxHeight: 300, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 8 }}>
                {realtimeEvents.slice(-10).reverse().map((event, i) => (
                  <div key={i} style={{
                    fontSize: 12, color: '#D4D4D8',
                    fontFamily: "'JetBrains Mono', 'SF Mono', monospace",
                    padding: '8px 12px',
                    background: 'rgba(255, 255, 255, 0.03)',
                    borderRadius: 8,
                    border: '1px solid rgba(255,255,255,0.06)',
                    lineHeight: 1.5,
                  }}>
                    <span style={{ color: '#22D3EE', fontWeight: 600 }}>
                      [{TRACE_EVENT_LABELS[event.type] || event.type}]
                    </span> {(event as any).message ?? event.data?.message ?? ''}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>

      {/* 导出模态框 */}
      <ExportModal
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
        executionId={executionId || undefined}
        type="execution"
      />
    </div>
    </TunnelTransition>
  );
};

export default ExecutionView;
