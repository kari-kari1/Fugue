import React, { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';

interface HumanReviewNodeData {
  name: string;
  reviewType: 'approval' | 'input' | 'selection';
  prompt: string;
  timeoutSeconds?: number;
  timeoutAction?: 'approve' | 'reject' | 'skip';
  options?: string[];
}

const typeLabels: Record<string, string> = {
  approval: '审批',
  input: '输入',
  selection: '选择',
};

const HumanReviewNode: React.FC<NodeProps> = ({ data, selected }) => {
  const nodeData = data as unknown as HumanReviewNodeData;

  return (
    <div
      className="min-w-[240px] max-w-[300px] transition-all duration-[250ms] ease-out overflow-hidden"
      style={{
        background: '#FFFFFF',
        border: selected ? '1px solid #EC4899' : '1px solid rgba(0,0,0,0.08)',
        borderRadius: 'var(--radius-node)',
        boxShadow: selected
          ? 'inset 0 1px 0 rgba(255,255,255,1), 0 0 0 2px rgba(236,72,153,0.15)'
          : 'inset 0 1px 0 rgba(255,255,255,1)',
      }}
    >
      <div className="h-[2px]" style={{ background: 'linear-gradient(to right, rgba(236,72,153,0.5), rgba(168,85,247,0.5))' }} />
      <Handle type="target" position={Position.Top} />

      {/* Header */}
      <div className="px-6 pt-5 pb-2 flex items-center gap-3.5">
        <div className="relative w-10 h-10 flex items-center justify-center rounded-xl flex-shrink-0"
          style={{ background: 'rgba(236,72,153,0.08)', border: '0.5px solid rgba(236,72,153,0.15)' }}>
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <circle cx="10" cy="7" r="4" stroke="#EC4899" strokeWidth="1.5" fill="rgba(236,72,153,0.15)" />
            <path d="M3 18C3 14.134 6.13401 11 10 11C13.866 11 17 14.134 17 18" stroke="#EC4899" strokeWidth="1.5" strokeLinecap="round" />
            <path d="M13 5L15 7L13 9" stroke="#EC4899" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-sm leading-tight truncate" style={{ color: 'var(--text-primary)' }}>
            {nodeData.name || '人工审核'}
          </div>
          <div className="text-xs truncate mt-1" style={{ color: 'var(--text-secondary)' }}>
            {typeLabels[nodeData.reviewType] || '审批'}
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="px-6 pb-4">
        <div className="rounded-[var(--radius-sm)] p-2 text-xs line-clamp-2" style={{ background: 'rgba(0,0,0,0.03)', color: 'var(--text-secondary)' }}>
          {nodeData.prompt || '等待审核...'}
        </div>
        {nodeData.timeoutSeconds && (
          <div className="mt-2 text-xs" style={{ color: 'var(--text-tertiary)' }}>
            超时: {nodeData.timeoutSeconds}秒
          </div>
        )}
        {nodeData.reviewType === 'selection' && nodeData.options && nodeData.options.length > 0 && (
          <div className="mt-2 text-xs" style={{ color: 'var(--text-tertiary)' }}>
            选项: {nodeData.options.join(', ')}
          </div>
        )}
      </div>

      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};

export default memo(HumanReviewNode);
