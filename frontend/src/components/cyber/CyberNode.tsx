/*
 * 动态态节点 — WWDC 霓虹脉冲过载节点
 * 多层 box-shadow bloom + 心跳脉冲 + 状态驱动光效
 * 设计规范: "0 0 10px #0ff, 0 0 20px #0ff, 0 0 40px #0ff"
 */

import React, { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import { motion } from 'framer-motion';

interface CyberNodeData {
  label?: string;
  name?: string;
  status?: 'idle' | 'running' | 'completed' | 'failed' | 'pending' | 'paused' | 'cancelled';
  type?: string;
  role?: string;
  llm_model?: string;
  output_type?: string;
  description?: string;
  [key: string]: unknown;
}

const TYPE_ICONS: Record<string, string> = {
  agent: 'A',
  task: 'T',
  condition: '?',
  loop: 'L',
  humanReview: 'H',
};

const getBloomColor = (type: string) => {
  switch (type) {
    case 'agent': return { main: '#00D4FF', dim: 'rgba(0, 212, 255,' };
    case 'task': return { main: '#AF52DE', dim: 'rgba(175, 82, 222,' };
    case 'condition': return { main: '#FFD60A', dim: 'rgba(255, 214, 10,' };
    case 'loop': return { main: '#FF9500', dim: 'rgba(255, 149, 0,' };
    case 'humanReview': return { main: '#FF453A', dim: 'rgba(255, 69, 58,' };
    default: return { main: '#00D4FF', dim: 'rgba(0, 212, 255,' };
  }
};

const getStatusBloom = (status: string, colors: { main: string; dim: string }) => {
  switch (status) {
    case 'running':
      return {
        border: `${colors.main}80`,
        boxShadow: `0 0 10px ${colors.dim} 0.3), 0 0 20px ${colors.dim} 0.2), 0 0 40px ${colors.dim} 0.1), inset 0 0 15px ${colors.dim} 0.05)`,
        animation: 'bloomPulse 2s ease-in-out infinite',
      };
    case 'completed':
      return {
        border: 'rgba(48, 209, 88, 0.6)',
        boxShadow: '0 0 10px rgba(48,209,88,0.3), 0 0 20px rgba(48,209,88,0.2), 0 0 40px rgba(48,209,88,0.1)',
        animation: 'none',
      };
    case 'failed':
      return {
        border: 'rgba(255, 69, 58, 0.6)',
        boxShadow: '0 0 10px rgba(255,69,58,0.3), 0 0 20px rgba(255,69,58,0.2), 0 0 40px rgba(255,69,58,0.1)',
        animation: 'cyberGlitch 0.3s ease-in-out 1',
      };
    default:
      return {
        border: 'rgba(255, 255, 255, 0.08)',
        boxShadow: 'none',
        animation: 'none',
      };
  }
};

const CyberNode: React.FC<NodeProps> = ({ data, type, selected }) => {
  const d = data as unknown as CyberNodeData;
  const nodeType = type || 'agent';
  const status = d.status || 'idle';
  const label = d.name || d.label || 'Node';
  const colors = getBloomColor(nodeType);
  const statusBloom = getStatusBloom(status, colors);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{
        opacity: 1,
        scale: status === 'running' ? [1, 1.03, 1] : 1,
      }}
      transition={
        status === 'running'
          ? { scale: { duration: 1.5, repeat: Infinity, ease: 'easeInOut' } }
          : { duration: 0.3 }
      }
      style={{
        position: 'relative',
        minWidth: 180,
        maxWidth: 280,
      }}
    >
      <Handle
        type="target"
        position={Position.Top}
        style={{
          background: colors.main,
          width: 8,
          height: 8,
          border: `1px solid ${colors.main}80`,
          boxShadow: `0 0 8px ${colors.main}60`,
        }}
      />

      <div
        style={{
          background: 'rgba(8, 8, 12, 0.92)',
          border: `1px solid ${selected ? colors.main : statusBloom.border}`,
          borderRadius: 12,
          padding: '14px 18px',
          boxShadow: selected
            ? `0 0 0 1px ${colors.main}, ${statusBloom.boxShadow}`
            : statusBloom.boxShadow,
          animation: statusBloom.animation,
          backdropFilter: 'blur(10px)',
          overflow: 'hidden',
        }}
      >
        {/* 顶部 accent 线 — 霓虹渐变 */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: '15%',
            right: '15%',
            height: 2,
            background: `linear-gradient(to right, transparent, ${colors.main}, transparent)`,
            borderRadius: 1,
            opacity: status === 'running' ? 0.9 : 0.4,
          }}
        />

        {/* 扫描线纹理 — 运行态 */}
        {status === 'running' && (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,212,255,0.015) 2px, rgba(0,212,255,0.015) 4px)',
              pointerEvents: 'none',
              animation: 'scanline 4s linear infinite',
              opacity: 0.5,
            }}
          />
        )}

        {/* 节点头部 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {/* 类型标识 */}
          <div
            style={{
              width: 28,
              height: 28,
              borderRadius: 8,
              background: `${colors.dim} 0.1)`,
              border: `0.5px solid ${colors.dim} 0.3)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontFamily: "'JetBrains Mono', 'SF Mono', monospace",
              fontSize: 11,
              fontWeight: 600,
              color: colors.main,
              flexShrink: 0,
            }}
          >
            {TYPE_ICONS[nodeType] || '?'}
          </div>

          <div style={{ flex: 1, minWidth: 0 }}>
            <div
              style={{
                fontFamily: "'JetBrains Mono', 'SF Mono', monospace",
                fontSize: 12,
                fontWeight: 500,
                color: '#E0E0E0',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {label}
            </div>
            {d.role && (
              <div style={{ fontSize: 10, color: '#636366', marginTop: 2 }}>
                {d.role}
              </div>
            )}
          </div>

          {/* 状态指示器 */}
          <div style={{ flexShrink: 0 }}>
            {status === 'running' && (
              <motion.div
                animate={{ scale: [1, 1.4, 1], opacity: [0.8, 0.3, 0.8] }}
                transition={{ duration: 1.5, repeat: Infinity }}
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  background: colors.main,
                  boxShadow: `0 0 8px ${colors.main}80`,
                }}
              />
            )}
            {status === 'completed' && (
              <svg width="16" height="16" viewBox="0 0 16 16">
                <circle cx="8" cy="8" r="7" fill="none" stroke="#30D158" strokeWidth="1.5" />
                <motion.path
                  d="M4.5 8.5L7 11L11.5 5.5"
                  fill="none"
                  stroke="#30D158"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  initial={{ pathLength: 0 }}
                  animate={{ pathLength: 1 }}
                  transition={{ duration: 0.5, delay: 0.2 }}
                />
              </svg>
            )}
            {status === 'failed' && (
              <div style={{
                width: 8, height: 8, borderRadius: '50%',
                background: '#FF453A',
                boxShadow: '0 0 8px rgba(255,69,58,0.5)',
              }} />
            )}
            {(status === 'idle' || status === 'pending') && (
              <div style={{
                width: 6, height: 6, borderRadius: '50%',
                background: 'rgba(255,255,255,0.15)',
              }} />
            )}
          </div>
        </div>

        {/* 状态文字 */}
        {status === 'running' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            style={{
              fontSize: 10,
              color: colors.main,
              textAlign: 'center',
              marginTop: 8,
              fontFamily: "'JetBrains Mono', 'SF Mono', monospace",
            }}
          >
            <span style={{ animation: 'neonFlicker 2s ease-in-out infinite' }}>
              PROCESSING
            </span>
            <motion.span
              animate={{ opacity: [0, 1] }}
              transition={{ duration: 0.5, repeat: Infinity }}
            >
              _
            </motion.span>
          </motion.div>
        )}

        {/* 模型信息 */}
        {d.llm_model && (
          <div style={{
            fontSize: 10,
            color: '#48484A',
            marginTop: 6,
            fontFamily: "'JetBrains Mono', 'SF Mono', monospace",
            borderTop: '0.5px solid rgba(255,255,255,0.04)',
            paddingTop: 6,
          }}>
            {d.llm_model}
          </div>
        )}
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        style={{
          background: colors.main,
          width: 8,
          height: 8,
          border: `1px solid ${colors.main}80`,
          boxShadow: `0 0 8px ${colors.main}60`,
        }}
      />
    </motion.div>
  );
};

export default memo(CyberNode);
