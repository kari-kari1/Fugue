import React, { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import type { LoopNodeData } from '../../types';

const LoopNode: React.FC<NodeProps> = ({ data, selected }) => {
  const nodeData = data as unknown as LoopNodeData;

  return (
    <div
      className="min-w-[240px] max-w-[300px] transition-all duration-[250ms] ease-out overflow-hidden"
      style={{
        background: '#FFFFFF',
        border: selected ? '1px solid #FF9F0A' : '1px solid rgba(0,0,0,0.08)',
        borderRadius: 'var(--radius-node)',
        boxShadow: selected
          ? 'inset 0 1px 0 rgba(255,255,255,1), 0 0 0 2px rgba(255,159,10,0.15)'
          : 'inset 0 1px 0 rgba(255,255,255,1)',
      }}
    >
      <div className="h-[2px]" style={{ background: 'linear-gradient(to right, rgba(255,159,10,0.5), rgba(255,214,10,0.5))' }} />

      <Handle type="target" position={Position.Top} />

      {/* Header */}
      <div className="px-6 pt-5 pb-2 flex items-center gap-3.5">
        <div className="relative w-10 h-10 flex items-center justify-center rounded-xl flex-shrink-0"
          style={{ background: 'rgba(0,0,0,0.03)', border: '0.5px solid rgba(0,0,0,0.06)' }}>
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <defs>
              <linearGradient id="loop-grad" x1="0" y1="0" x2="20" y2="20">
                <stop offset="0%" stopColor="#FF9F0A" />
                <stop offset="100%" stopColor="#FFD60A" />
              </linearGradient>
            </defs>
            <path
              d="M14 4L16 6L14 8"
              stroke="url(#loop-grad)"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M16 6C16 6 12 6 10 6C7.79 6 6 7.79 6 10C6 12.21 7.79 14 10 14C12.21 14 14 12.21 14 10"
              stroke="url(#loop-grad)"
              strokeWidth="1.5"
              strokeLinecap="round"
              fill="none"
            />
            <path
              d="M6 16L4 14L6 12"
              stroke="url(#loop-grad)"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M4 14C4 14 8 14 10 14C12.21 14 14 12.21 14 10C14 7.79 12.21 6 10 6"
              stroke="url(#loop-grad)"
              strokeWidth="1.5"
              strokeLinecap="round"
              fill="none"
            />
          </svg>
        </div>

        <div className="flex-1 min-w-0">
          <div className="font-semibold text-sm leading-tight truncate" style={{ color: '#1D1D1F' }}>
            {nodeData.name || '循环'}
          </div>
          <div className="text-xs truncate mt-1" style={{ color: '#6E6E73' }}>
            迭代执行
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="px-6 pt-3 pb-5 space-y-3">
        <div className="flex items-center justify-between rounded-md px-3 py-2" style={{ background: 'rgba(0,0,0,0.02)', border: '0.5px solid rgba(0,0,0,0.06)' }}>
          <span className="text-xs" style={{ color: '#6E6E73' }}>最大迭代</span>
          <span className="text-xs font-semibold" style={{ color: '#1D1D1F' }}>{nodeData.maxIterations || 10} 次</span>
        </div>

        {nodeData.condition && (
          <div className="rounded-md px-3 py-2" style={{ background: 'rgba(0,0,0,0.02)', border: '0.5px solid rgba(0,0,0,0.06)' }}>
            <div className="text-10 mb-1" style={{ color: '#6E6E73' }}>循环条件</div>
            <code className="text-xs font-mono break-all leading-relaxed" style={{ color: '#6E6E73' }}>
              {nodeData.condition}
            </code>
          </div>
        )}

        {nodeData.exitOnFailure !== undefined && (
          <div className="flex items-center justify-between text-xs pt-2" style={{ color: '#6E6E73', borderTop: '0.5px solid rgba(0,0,0,0.06)' }}>
            <span>失败时退出</span>
            <span className="font-medium" style={{ color: nodeData.exitOnFailure ? '#FF453A' : '#34C759' }}>
              {nodeData.exitOnFailure ? '是' : '否'}
            </span>
          </div>
        )}
      </div>

      {/* Source handle */}
      <Handle
        type="source"
        position={Position.Bottom}
      />
    </div>
  );
};

export default memo(LoopNode);
