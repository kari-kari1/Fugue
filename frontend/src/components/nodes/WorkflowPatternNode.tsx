/* 工作流模式节点 — Anthropic 五种模式可视化
 * Router / Parallel / Orchestrator / Evaluator / PromptChain
 */

import React from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import {
  GitFork, Layers, Network, RefreshCw, ArrowRight,
  GitBranch, Split, Users, Repeat, Link2,
} from 'lucide-react';

export type WorkflowPatternType = 'router' | 'parallel' | 'orchestrator' | 'evaluator' | 'prompt_chain';

const PATTERN_CONFIG: Record<WorkflowPatternType, {
  icon: React.ReactNode;
  label: string;
  color: string;
  bgColor: string;
  borderColor: string;
}> = {
  router: {
    icon: <GitFork size={14} />,
    label: 'Router 路由',
    color: '#F59E0B',
    bgColor: 'rgba(245, 158, 11, 0.15)',
    borderColor: 'rgba(245, 158, 11, 0.4)',
  },
  parallel: {
    icon: <Split size={14} />,
    label: 'Parallel 并行',
    color: '#3B82F6',
    bgColor: 'rgba(59, 130, 246, 0.15)',
    borderColor: 'rgba(59, 130, 246, 0.4)',
  },
  orchestrator: {
    icon: <Network size={14} />,
    label: 'Orchestrator 编排',
    color: '#8B5CF6',
    bgColor: 'rgba(139, 92, 246, 0.15)',
    borderColor: 'rgba(139, 92, 246, 0.4)',
  },
  evaluator: {
    icon: <RefreshCw size={14} />,
    label: 'Evaluator 评估',
    color: '#10B981',
    bgColor: 'rgba(16, 185, 129, 0.15)',
    borderColor: 'rgba(16, 185, 129, 0.4)',
  },
  prompt_chain: {
    icon: <Link2 size={14} />,
    label: 'Prompt Chain 链式',
    color: '#EC4899',
    bgColor: 'rgba(236, 72, 153, 0.15)',
    borderColor: 'rgba(236, 72, 153, 0.4)',
  },
};

export const WorkflowPatternNode: React.FC<NodeProps> = ({ data, selected }) => {
  const patternType = (data?.patternType as WorkflowPatternType) || 'router';
  const config = PATTERN_CONFIG[patternType] || PATTERN_CONFIG.router;
  const name = (data?.name as string) || config.label;

  return (
    <div
      style={{
        padding: '12px 16px',
        borderRadius: 12,
        background: config.bgColor,
        border: `1.5px solid ${selected ? config.color : config.borderColor}`,
        boxShadow: selected
          ? `0 0 12px ${config.color}40`
          : `0 2px 8px rgba(0,0,0,0.15)`,
        minWidth: 180,
        transition: 'all 0.2s ease',
      }}
    >
      {/* 顶部Handle */}
      <Handle
        type="target"
        position={Position.Top}
        style={{
          background: config.color,
          border: '2px solid #1a1a2e',
          width: 10,
          height: 10,
        }}
      />

      {/* 头部 */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        marginBottom: 6,
      }}>
        <span style={{ color: config.color }}>{config.icon}</span>
        <span style={{
          fontSize: 12,
          fontWeight: 600,
          color: '#1D1D1F',
          fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif",
        }}>
          {name}
        </span>
      </div>

      {/* 类型标签 */}
      <span style={{
        display: 'inline-block',
        padding: '1px 8px',
        borderRadius: 6,
        fontSize: 9,
        fontWeight: 600,
        color: config.color,
        background: `${config.color}20`,
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
      }}>
        {config.label}
      </span>

      {/* 描述 / 额外信息 */}
      {data?.description && (
        <div style={{
          fontSize: 10,
          color: '#6E6E73',
          marginTop: 6,
          lineHeight: 1.4,
        }}>
          {(data.description as string).slice(0, 60)}
        </div>
      )}

      {/* 底部Handle */}
      <Handle
        type="source"
        position={Position.Bottom}
        style={{
          background: config.color,
          border: '2px solid #1a1a2e',
          width: 10,
          height: 10,
        }}
      />
    </div>
  );
};
