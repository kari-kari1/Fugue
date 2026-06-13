import React from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import { Play, Radio, GitBranch } from 'lucide-react';

export type EventFlowType = 'start' | 'listen' | 'router_event';

interface FlowNodeConfig {
  icon: React.ReactNode;
  label: string;
  color: string;
  bgColor: string;
  borderColor: string;
}

const EVENT_FLOW_CONFIG: Record<EventFlowType, FlowNodeConfig> = {
  start: {
    icon: <Play size={14} />,
    label: '@start',
    color: '#06B6D4',
    bgColor: 'rgba(6, 182, 212, 0.12)',
    borderColor: 'rgba(6, 182, 212, 0.4)',
  },
  listen: {
    icon: <Radio size={14} />,
    label: '@listen',
    color: '#8B5CF6',
    bgColor: 'rgba(139, 92, 246, 0.12)',
    borderColor: 'rgba(139, 92, 246, 0.4)',
  },
  router_event: {
    icon: <GitBranch size={14} />,
    label: '@router',
    color: '#F59E0B',
    bgColor: 'rgba(245, 158, 11, 0.12)',
    borderColor: 'rgba(245, 158, 11, 0.4)',
  },
};

const EventFlowNode = ({ data, selected }: NodeProps) => {
  const flowType = (data?.flowType as EventFlowType) || 'start';
  const config: FlowNodeConfig = EVENT_FLOW_CONFIG[flowType] || EVENT_FLOW_CONFIG.start;
  const name: string = (data?.name as string) || config.label;
  const eventName: string = (data?.event_name as string) || '';

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
      {flowType !== 'start' && (
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
      )}

      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
        <span style={{ color: config.color }}>{config.icon as React.ReactNode}</span>
        <span style={{
          fontSize: 12,
          fontWeight: 600,
          color: '#1D1D1F',
          fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif",
        }}>
          {name}
        </span>
      </div>

      <span>{String(config.label)}</span>

      {eventName && (
        <div style={{
          fontSize: 10,
          color: '#6E6E73',
          marginTop: 6,
          fontFamily: "'SF Mono', Menlo, monospace",
          padding: '2px 6px',
          borderRadius: 4,
          background: 'rgba(0,0,0,0.04)',
          display: 'inline-block',
        }}>
          {eventName}
        </div>
      )}

      {flowType === 'router_event' && (data?.condition as string) && (
        <div style={{
          fontSize: 10,
          color: '#6E6E73',
          marginTop: 4,
          fontStyle: 'italic',
        }}>
          if: {(data.condition as string).slice(0, 40)}
        </div>
      )}

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

export default EventFlowNode;
