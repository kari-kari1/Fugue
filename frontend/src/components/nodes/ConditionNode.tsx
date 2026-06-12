import React, { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import type { ConditionNodeData } from '../../types';

const ConditionNode: React.FC<NodeProps> = ({ data, selected }) => {
  const nodeData = data as unknown as ConditionNodeData;

  return (
    <div
      className="min-w-[240px] max-w-[300px] transition-all duration-[250ms] ease-out overflow-hidden"
      style={{
        background: '#FFFFFF',
        border: selected ? '1px solid #AF52DE' : '1px solid rgba(0,0,0,0.08)',
        borderRadius: 'var(--radius-node)',
        boxShadow: selected
          ? 'inset 0 1px 0 rgba(255,255,255,1), 0 0 0 2px rgba(175,82,222,0.15)'
          : 'inset 0 1px 0 rgba(255,255,255,1)',
      }}
    >
      <div className="h-[2px]" style={{ background: 'linear-gradient(to right, rgba(175,82,222,0.5), rgba(255,159,10,0.5))' }} />

      <Handle type="target" position={Position.Top} />

      {/* Header */}
      <div className="px-6 pt-5 pb-2 flex items-center gap-3.5">
        <div className="relative w-10 h-10 flex items-center justify-center rounded-xl flex-shrink-0"
          style={{ background: 'rgba(0,0,0,0.03)', border: '0.5px solid rgba(0,0,0,0.06)' }}>
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <defs>
              <linearGradient id="cond-grad" x1="0" y1="0" x2="20" y2="20">
                <stop offset="0%" stopColor="#AF52DE" />
                <stop offset="100%" stopColor="#FF9F0A" />
              </linearGradient>
            </defs>
            <path d="M10 2L18 10L10 18L2 10L10 2Z" stroke="url(#cond-grad)" strokeWidth="1.5" fill="url(#cond-grad)" fillOpacity="0.1" />
            <path d="M7 8L10 5L13 8" stroke="url(#cond-grad)" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M10 5V13" stroke="url(#cond-grad)" strokeWidth="1.2" strokeLinecap="round" />
            <path d="M7 12L10 15L13 12" stroke="url(#cond-grad)" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>

        <div className="flex-1 min-w-0">
          <div className="font-semibold text-sm leading-tight truncate" style={{ color: '#1D1D1F' }}>
            {nodeData.name || '条件判断'}
          </div>
          <div className="text-xs truncate mt-1" style={{ color: '#6E6E73' }}>
            条件分支
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="px-6 pt-3 pb-5 space-y-3">
        <div className="rounded-md px-3 py-2" style={{ background: 'rgba(0,0,0,0.02)', border: '0.5px solid rgba(0,0,0,0.06)' }}>
          <code className="text-xs font-mono break-all leading-relaxed" style={{ color: '#6E6E73' }}>
            {nodeData.expression || '未设置条件'}
          </code>
        </div>

        {/* Branch labels */}
        <div className="flex items-center justify-between pt-2 mt-2" style={{ borderTop: '0.5px solid rgba(0,0,0,0.06)' }}>
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full" style={{ background: '#34C759' }} />
            <span className="text-xs" style={{ color: '#6E6E73' }}>True</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full" style={{ background: '#FF453A' }} />
            <span className="text-xs" style={{ color: '#6E6E73' }}>False</span>
          </div>
        </div>
      </div>

      {/* Source handles for True/False branches */}
      <Handle
        type="source"
        position={Position.Bottom}
        id="true"
        style={{ left: '30%' }}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="false"
        style={{ left: '70%' }}
      />
    </div>
  );
};

export default memo(ConditionNode);
