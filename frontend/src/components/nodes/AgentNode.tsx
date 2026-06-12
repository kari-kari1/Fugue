import React, { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import { getAgentIcon, getModelDotColor } from '../../lib/utils';
import type { AgentNodeData } from '../../types';

const AgentNode: React.FC<NodeProps> = ({ data, selected }) => {
  const nodeData = data as unknown as AgentNodeData;

  const statusDotColor = () => {
    switch (nodeData.status) {
      case 'running': return 'bg-[var(--accent-secondary)]';
      case 'completed': return 'bg-[var(--accent-green)]';
      case 'failed': return 'bg-[var(--accent-red)]';
      case 'paused': return 'bg-[var(--accent-amber)]';
      default: return 'bg-[var(--text-disabled)]';
    }
  };

  const statusTextColor = () => {
    switch (nodeData.status) {
      case 'completed': return 'text-accent-green';
      case 'failed': return 'text-accent-red';
      case 'running': return 'text-accent-secondary';
      case 'paused': return 'text-accent-amber';
      default: return 'text-tertiary';
    }
  };

  const statusLabel = () => {
    switch (nodeData.status) {
      case 'running': return '思考中';
      case 'completed': return '就绪';
      case 'failed': return '错误';
      case 'paused': return '暂停';
      case 'cancelled': return '已取消';
      default: return '待机';
    }
  };

  return (
    <div
      className="min-w-[240px] max-w-[300px] transition-all duration-[250ms] ease-out overflow-hidden"
      style={{
        background: '#FFFFFF',
        border: selected ? '1px solid #0071E3' : '1px solid rgba(0,0,0,0.08)',
        borderRadius: 'var(--radius-node)',
        boxShadow: selected
          ? 'inset 0 1px 0 rgba(255,255,255,1), 0 0 0 2px rgba(0,113,227,0.15)'
          : 'inset 0 1px 0 rgba(255,255,255,1)',
      }}
    >
      <div className="h-[2px]" style={{ background: 'linear-gradient(to right, rgba(0,113,227,0.5), rgba(88,86,214,0.5))' }} />

      <Handle type="target" position={Position.Top} />

      {/* Header */}
      <div className="px-6 pt-5 pb-2 flex items-center gap-3.5">
        <div className="relative w-10 h-10 flex items-center justify-center rounded-xl flex-shrink-0"
          style={{ background: 'rgba(0,0,0,0.03)', border: '0.5px solid rgba(0,0,0,0.06)' }}>
          {getAgentIcon(nodeData.role || '')}
        </div>

        <div className="flex-1 min-w-0">
          <div className="font-semibold text-sm leading-tight truncate" style={{ color: '#1D1D1F' }}>
            {nodeData.name || 'Agent'}
          </div>
          <div className="text-xs truncate mt-1" style={{ color: '#6E6E73' }}>
            {nodeData.role || '未设置角色'}
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
        <div className="flex items-center gap-1.5 text-xs">
          <span className="w-1.5 h-1.5 rounded-full inline-block flex-shrink-0"
            style={{ backgroundColor: getModelDotColor(nodeData.llm_provider || 'openai') }} />
          <span className="truncate font-mono" style={{ color: '#6E6E73' }}>
            {nodeData.llm_model || 'gpt-4o'}
          </span>
          {(nodeData.tools || []).length > 0 && (
            <>
              <span style={{ color: '#86868B' }}>·</span>
              <span style={{ color: '#6E6E73' }}>{(nodeData.tools || []).length} tools</span>
            </>
          )}
        </div>

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

export default memo(AgentNode);
