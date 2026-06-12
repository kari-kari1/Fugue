import React, { useMemo, useRef, useEffect } from 'react';
import type { ExecutionEvent } from '../../hooks/useExecutionMonitor';

interface RealtimeThoughtsProps {
  events: ExecutionEvent[];
  maxHeight?: string;
}

export const RealtimeThoughts: React.FC<RealtimeThoughtsProps> = ({
  events,
  maxHeight = '500px',
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new events
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [events.length]);

  const safeEvents = useMemo(
    () => events.map((e) => ({ ...e, data: e.data && typeof e.data === 'object' ? e.data : {} })),
    [events],
  );

  const formatTime = (ts: string) => {
    try {
      const d = new Date(ts);
      return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch { return ''; }
  };

  if (safeEvents.length === 0) {
    return (
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: '48px 24px', color: '#71717A', fontSize: 14,
      }}>
        等待执行事件...
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      style={{
        maxHeight,
        overflowY: 'auto',
        padding: '16px 0',
      }}
    >
      {safeEvents.map((event, index) => {
        const step = (event.data?.step as string) || '';
        const content = (event.data?.content as string) || '';
        const toolName = (event.data?.tool as string) || '';
        const isToolResult = step === 'tool_result';
        const isReasoning = step === 'reasoning';
        const isToolCall = event.type === 'agent.tool_call';

        return (
          <div
            key={`${event.timestamp}-${index}`}
            style={{
              padding: '8px 20px',
              borderLeft: '2px solid',
              borderLeftColor: isToolResult ? '#30D158' : isReasoning ? '#007AFF' : isToolCall ? '#FF9F0A' : '#48484A',
              marginLeft: 12,
              marginBottom: 4,
            }}
          >
            {/* Event header */}
            <div style={{
              display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4,
            }}>
              <span style={{
                fontSize: 11, fontWeight: 600, color: '#A1A1AA',
                fontFamily: "'SF Mono', 'JetBrains Mono', monospace",
                textTransform: 'uppercase', letterSpacing: '0.05em',
              }}>
                {isToolResult ? `🔧 ${toolName || 'tool'}` : isReasoning ? '💭 思考' : isToolCall ? `⚡ ${toolName}` : event.type}
              </span>
              <span style={{ fontSize: 10, color: '#636366' }}>
                {formatTime(event.timestamp)}
              </span>
            </div>

            {/* Content */}
            {isReasoning && content && (
              <div style={{
                fontSize: 14,
                lineHeight: 1.7,
                color: '#D4D4D8',
                whiteSpace: 'pre-wrap',
                fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Segoe UI', system-ui, sans-serif",
                fontWeight: 400,
              }}>
                {content}
              </div>
            )}

            {isToolResult && content && (
              <div style={{
                fontSize: 12.5,
                lineHeight: 1.6,
                color: '#A1A1AA',
                whiteSpace: 'pre-wrap',
                fontFamily: "'SF Mono', 'JetBrains Mono', monospace",
                background: 'rgba(255, 255, 255, 0.03)',
                padding: '8px 12px',
                borderRadius: 6,
                maxHeight: 200,
                overflowY: 'auto',
              }}>
                {content}
              </div>
            )}

            {!isReasoning && !isToolResult && content && (
              <div style={{
                fontSize: 13, color: '#A1A1AA', lineHeight: 1.6,
                whiteSpace: 'pre-wrap',
              }}>
                {content}
              </div>
            )}

            {/* Error */}
            {event.data?.error && (
              <div style={{
                fontSize: 12, color: '#FF453A', marginTop: 4,
                padding: '6px 10px', background: 'rgba(255, 69, 58, 0.08)',
                borderRadius: 6,
              }}>
                {event.data.error as string}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
