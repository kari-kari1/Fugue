/* 检查点面板 — 时间旅行调试
 * 显示执行过程中的检查点时间轴，支持从检查点恢复执行
 */

import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  GitBranch, Play, Pause, Clock, CheckCircle2, AlertCircle,
  RefreshCw, ChevronRight, Activity
} from 'lucide-react';
import toast from 'react-hot-toast';

import { executionsApi } from '../../api/executions';

interface Checkpoint {
  id: string;
  checkpoint_type: string; // auto 或 manual
  task_id: string | null;
  task_name: string | null;
  completed_task_count: number;
  total_tokens_so_far: number;
  created_at: string;
}

interface CheckpointPanelProps {
  executionId: string;
  status: string;
  onStatusChange?: () => void;
}

export const CheckpointPanel: React.FC<CheckpointPanelProps> = ({
  executionId,
  status,
  onStatusChange,
}) => {
  const [checkpoints, setCheckpoints] = useState<Checkpoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const fetchCheckpoints = async () => {
    setLoading(true);
    try {
      const data = await executionsApi.getCheckpoints(executionId);
      setCheckpoints(data);
    } catch {
      // 静默处理
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCheckpoints();
    const interval = setInterval(() => {
      if (status === 'running') fetchCheckpoints();
    }, 10000);
    return () => clearInterval(interval);
  }, [executionId, status]);

  const handlePause = async () => {
    try {
      await executionsApi.pause(executionId);
      toast.success('已发送暂停信号');
      onStatusChange?.();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || '暂停失败');
    }
  };

  const handleResume = async () => {
    try {
      await executionsApi.resume(executionId);
      toast.success('已恢复执行');
      onStatusChange?.();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || '恢复失败');
    }
  };

  const autoCPs = checkpoints.filter(c => c.checkpoint_type === 'auto');
  const manualCPs = checkpoints.filter(c => c.checkpoint_type === 'manual');

  return (
    <div style={{
      background: 'rgba(255, 255, 255, 0.04)',
      border: '1px solid rgba(192, 132, 252, 0.2)',
      borderRadius: 12,
      overflow: 'hidden',
    }}>
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '12px 16px',
          background: 'transparent',
          border: 'none',
          cursor: 'pointer',
          color: '#e4e4e7',
          fontSize: 13,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <GitBranch size={14} style={{ color: '#C084FC' }} />
          <span style={{ fontWeight: 600 }}>时间旅行调试</span>
          <span style={{
            padding: '1px 6px',
            borderRadius: 8,
            fontSize: 10,
            background: 'rgba(192, 132, 252, 0.2)',
            color: '#C084FC',
          }}>
            {checkpoints.length} 检查点
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          {/* 暂停/恢复按钮 */}
          {status === 'running' && (
            <button
              onClick={(e) => { e.stopPropagation(); handlePause(); }}
              style={{
                display: 'flex', alignItems: 'center', gap: 4,
                padding: '4px 10px', borderRadius: 6,
                background: 'rgba(250, 204, 21, 0.15)',
                border: '0.5px solid rgba(250, 204, 21, 0.3)',
                color: '#FACC15', fontSize: 11, cursor: 'pointer',
              }}
            >
              <Pause size={12} /> 暂停
            </button>
          )}
          {status === 'paused' && (
            <button
              onClick={(e) => { e.stopPropagation(); handleResume(); }}
              style={{
                display: 'flex', alignItems: 'center', gap: 4,
                padding: '4px 10px', borderRadius: 6,
                background: 'rgba(74, 222, 128, 0.15)',
                border: '0.5px solid rgba(74, 222, 128, 0.3)',
                color: '#4ADE80', fontSize: 11, cursor: 'pointer',
              }}
            >
              <Play size={12} /> 从检查点恢复
            </button>
          )}
          <motion.div
            animate={{ rotate: expanded ? 90 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <ChevronRight size={14} style={{ color: '#71717A' }} />
          </motion.div>
        </div>
      </button>

      {/* Expanded content — 检查点时间轴 */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            style={{ overflow: 'hidden' }}
          >
            <div style={{ padding: '0 16px 16px' }}>
              {/* 刷新按钮 */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 10 }}>
                <button
                  onClick={(e) => { e.stopPropagation(); fetchCheckpoints(); }}
                  disabled={loading}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 4,
                    padding: '2px 8px', borderRadius: 4,
                    background: 'rgba(255,255,255,0.05)',
                    border: '0.5px solid rgba(255,255,255,0.1)',
                    color: '#a1a1aa', fontSize: 11, cursor: 'pointer',
                  }}
                >
                  <RefreshCw size={10} className={loading ? 'animate-spin' : ''} />
                  刷新
                </button>
              </div>

              {checkpoints.length === 0 ? (
                <div style={{
                  textAlign: 'center', padding: '20px 0',
                  color: '#71717A', fontSize: 12,
                }}>
                  <Activity size={20} style={{ margin: '0 auto 6px', opacity: 0.4 }} />
                  暂无检查点 — 执行任务后自动生成
                </div>
              ) : (
                <div style={{ position: 'relative' }}>
                  {/* 时间轴线 */}
                  <div style={{
                    position: 'absolute', left: 11, top: 0, bottom: 0,
                    width: 2,
                    background: 'linear-gradient(to bottom, rgba(192,132,252,0.4), rgba(34,211,238,0.2))',
                  }} />

                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {[...checkpoints].reverse().map((cp, idx) => (
                      <div key={cp.id} style={{
                        position: 'relative',
                        paddingLeft: 30,
                      }}>
                        {/* 时间轴节点 */}
                        <div style={{
                          position: 'absolute', left: 5, top: 4,
                          width: 14, height: 14, borderRadius: '50%',
                          background: cp.checkpoint_type === 'manual'
                            ? 'rgba(192, 132, 252, 0.3)'
                            : 'rgba(34, 211, 238, 0.3)',
                          border: `2px solid ${cp.checkpoint_type === 'manual' ? '#C084FC' : '#22D3EE'}`,
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                        }}>
                          {cp.checkpoint_type === 'manual' ? (
                            <Pause size={7} style={{ color: '#C084FC' }} />
                          ) : (
                            <CheckCircle2 size={7} style={{ color: '#22D3EE' }} />
                          )}
                        </div>

                        {/* 检查点信息 */}
                        <div style={{
                          background: 'rgba(255, 255, 255, 0.03)',
                          border: '0.5px solid rgba(255, 255, 255, 0.06)',
                          borderRadius: 8,
                          padding: '8px 12px',
                        }}>
                          <div style={{
                            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                            marginBottom: 4,
                          }}>
                            <span style={{
                              fontSize: 11,
                              color: cp.checkpoint_type === 'manual' ? '#C084FC' : '#22D3EE',
                              fontWeight: 600,
                              display: 'flex', alignItems: 'center', gap: 4,
                            }}>
                              {cp.checkpoint_type === 'manual' ? <Pause size={10} /> : <CheckCircle2 size={10} />}
                              {cp.checkpoint_type === 'auto' ? '自动检查点' : '手动检查点'}
                            </span>
                            <span style={{ fontSize: 10, color: '#71717A' }}>
                              <Clock size={10} style={{ display: 'inline', marginRight: 2 }} />
                              {cp.created_at ? new Date(cp.created_at).toLocaleTimeString() : ''}
                            </span>
                          </div>

                          {cp.task_name && (
                            <div style={{ fontSize: 11, color: '#a1a1aa', marginBottom: 2 }}>
                              任务: {cp.task_name}
                            </div>
                          )}

                          <div style={{
                            display: 'flex', gap: 12, fontSize: 10, color: '#71717A',
                          }}>
                            <span>{cp.completed_task_count} 个任务完成</span>
                            <span>{cp.total_tokens_so_far || 0} tokens</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 图例 */}
              {checkpoints.length > 0 && (
                <div style={{
                  display: 'flex', gap: 16, marginTop: 12,
                  paddingTop: 8,
                  borderTop: '0.5px solid rgba(255,255,255,0.06)',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 10, color: '#71717A' }}>
                    <CheckCircle2 size={10} style={{ color: '#22D3EE' }} /> 自动检查点
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 10, color: '#71717A' }}>
                    <Pause size={10} style={{ color: '#C084FC' }} /> 手动检查点
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
