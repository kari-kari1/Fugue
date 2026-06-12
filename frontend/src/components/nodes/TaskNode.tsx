import React, { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import { getTaskIcon } from '../../lib/utils';
import type { TaskNodeData } from '../../types';

const TaskNode: React.FC<NodeProps> = ({ data, selected }) => {
  const nodeData = data as unknown as TaskNodeData;

  const statusDotColor = () => {
    switch (nodeData.status) {
      case 'running': return 'bg-[var(--accent-secondary)]';
      case 'completed': return 'bg-[var(--accent-green)]';
      case 'failed': return 'bg-[var(--accent-red)]';
      case 'retrying': return 'bg-[var(--accent-amber)]';
      default: return 'bg-[var(--text-disabled)]';
    }
  };

  const statusTextColor = () => {
    switch (nodeData.status) {
      case 'completed': return 'text-accent-green';
      case 'failed': return 'text-accent-red';
      case 'running': return 'text-accent-secondary';
      case 'retrying': return 'text-accent-amber';
      default: return 'text-tertiary';
    }
  };

  const statusLabel = () => {
    switch (nodeData.status) {
      case 'running': return '执行中';
      case 'completed': return '已完成';
      case 'failed': return '失败';
      case 'retrying': return '重试中';
      case 'skipped': return '跳过';
      default: return '待执行';
    }
  };

  return (
    <div
      className="min-w-[220px] max-w-[280px] transition-all duration-[250ms] ease-out overflow-hidden"
      style={{
        background: '#FFFFFF',
        border: selected ? '1px solid #34C759' : '1px solid rgba(0,0,0,0.08)',
        borderRadius: 'var(--radius-node)',
        boxShadow: selected
          ? 'inset 0 1px 0 rgba(255,255,255,1), 0 0 0 2px rgba(52,199,89,0.15)'
          : 'inset 0 1px 0 rgba(255,255,255,1)',
      }}
    >
      <div className="h-[2px]" style={{ background: 'linear-gradient(to right, rgba(52,199,89,0.5), rgba(90,200,250,0.5))' }} />

      <Handle type="target" position={Position.Top} />

      {/* Header */}
      <div className="px-6 pt-5 pb-2 flex items-center gap-3.5">
        <div className="relative w-10 h-10 flex items-center justify-center rounded-xl flex-shrink-0"
          style={{ background: 'rgba(0,0,0,0.03)', border: '0.5px solid rgba(0,0,0,0.06)' }}>
          {getTaskIcon()}
        </div>

        <div className="flex-1 min-w-0">
          <div className="font-semibold text-sm leading-tight truncate" style={{ color: '#1D1D1F' }}>
            {nodeData.name || 'Task'}
          </div>
          <div className="text-xs truncate mt-1" style={{ color: '#6E6E73' }}>
            {nodeData.output_type || 'text'} · {nodeData.agent_name || '未分配'}
          </div>
        </div>

        <div className="relative flex-shrink-0">
          <div className={`w-2 h-2 rounded-full ${statusDotColor()}`} />
          {nodeData.status === 'running' && (
            <div className="absolute inset-[-2px] rounded-full animate-ping opacity-20 bg-[var(--accent-secondary)]" />
          )}
        </div>
      </div>

      {/* Content */}
      <div className="px-6 pt-3 pb-5 space-y-3">
        {nodeData.description && (
          <p className="text-xs line-clamp-2 leading-relaxed" style={{ color: '#6E6E73' }}>
            {nodeData.description}
          </p>
        )}

        {nodeData.status && (
          <div className="flex items-center gap-1.5 pt-2 mt-2" style={{ borderTop: '0.5px solid rgba(0,0,0,0.06)' }}>
            <span className={`text-xs font-medium ${statusTextColor()}`}>
              {statusLabel()}
            </span>
          </div>
        )}
      </div>

      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};

export default memo(TaskNode);
