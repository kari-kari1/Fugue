/*
 * 霓虹光轨 Edge — WWDC 风格紫青渐变 + 流动光点 + glow 拖尾
 * 设计规范: linearGradient #BF40FF→#00FFFF + strokeDasharray 流动 + drop-shadow
 */

import React, { memo } from 'react';
import { getBezierPath, type EdgeProps } from '@xyflow/react';

const CyberTrail: React.FC<EdgeProps> = ({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  selected,
  markerEnd,
}) => {
  const [edgePath] = getBezierPath({
    sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition,
  });

  const isActive = (data as { executing?: boolean })?.executing || (data as { active?: boolean })?.active;
  const particleDur = isActive ? '1.5s' : '3s';
  const particleCount = isActive ? 5 : 3;
  const baseColor = (data as { color?: string })?.color || 'cyan';

  // 根据颜色选择渐变
  const gradientColors = baseColor === 'green'
    ? { start: '#30D158', mid: '#00D4FF', end: '#30D158' }
    : { start: '#00D4FF', mid: '#AF52DE', end: '#00D4FF' };

  const glowColor = baseColor === 'green'
    ? 'rgba(48, 209, 88,'
    : 'rgba(0, 212, 255,';

  return (
    <g>
      <defs>
        <linearGradient id={`cyber-grad-${id}`} x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor={gradientColors.start} />
          <stop offset="50%" stopColor={gradientColors.mid} />
          <stop offset="100%" stopColor={gradientColors.end} />
        </linearGradient>
        <filter id={`cyber-glow-${id}`}>
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* 底层宽光轨 — glow 扩散 */}
      <path
        d={edgePath}
        fill="none"
        stroke={`url(#cyber-grad-${id})`}
        strokeWidth={isActive ? 6 : 3}
        strokeLinecap="round"
        style={{
          filter: `drop-shadow(0 0 8px ${glowColor} 0.6)) drop-shadow(0 0 20px ${glowColor} 0.3))`,
          opacity: isActive ? 0.4 : 0.15,
        }}
      />

      {/* 主光轨 — strokeDasharray 流动 */}
      <path
        d={edgePath}
        fill="none"
        stroke={`url(#cyber-grad-${id})`}
        strokeWidth={isActive ? 2.5 : 1.5}
        strokeLinecap="round"
        strokeDasharray="40 1000"
        style={{
          filter: `drop-shadow(0 0 6px ${glowColor} 0.6))`,
          animation: isActive
            ? 'cyberFlow 1.5s cubic-bezier(0.4, 0, 0.2, 1) infinite'
            : 'cyberFlow 3s cubic-bezier(0.4, 0, 0.2, 1) infinite',
        }}
      />

      {/* 选中态: 高亮实线 */}
      {selected && (
        <path
          d={edgePath}
          fill="none"
          stroke={gradientColors.start}
          strokeWidth={2}
          strokeLinecap="round"
          opacity={0.8}
          style={{
            filter: `drop-shadow(0 0 10px ${gradientColors.start})`,
          }}
        />
      )}

      {/* 流动光点 — 高速光束粒子 */}
      {Array.from({ length: particleCount }).map((_, i) => {
        const dotColor = i % 2 === 0 ? gradientColors.start : gradientColors.mid;
        return (
          <circle
            key={i}
            r={isActive ? 3 : 2}
            fill={dotColor}
            opacity="0.9"
            style={{
              filter: `drop-shadow(0 0 6px ${dotColor}) drop-shadow(0 0 12px ${dotColor}80)`,
            }}
          >
            <animateMotion
              dur={particleDur}
              repeatCount="indefinite"
              begin={`${(i * parseFloat(isActive ? '1.5' : '3')) / particleCount}s`}
              path={edgePath}
            />
            <animate
              attributeName="opacity"
              values="0;0.9;0.9;0.2"
              dur={particleDur}
              repeatCount="indefinite"
              begin={`${(i * parseFloat(isActive ? '1.5' : '3')) / particleCount}s`}
            />
            <animate
              attributeName="r"
              values={`1;${isActive ? 3.5 : 2.5};${isActive ? 3 : 2};1`}
              dur={particleDur}
              repeatCount="indefinite"
              begin={`${(i * parseFloat(isActive ? '1.5' : '3')) / particleCount}s`}
            />
          </circle>
        );
      })}

      {/* 拖尾效果 — 每个光点后面带一条短尾迹 */}
      {isActive && Array.from({ length: 2 }).map((_, i) => {
        const tailColor = i === 0 ? gradientColors.start : gradientColors.mid;
        return (
          <circle
            key={`tail-${i}`}
            r={1.5}
            fill={tailColor}
            opacity="0.4"
            style={{ filter: `drop-shadow(0 0 4px ${tailColor}60)` }}
          >
            <animateMotion
              dur={particleDur}
              repeatCount="indefinite"
              begin={`${(i * 1.5) / 2 + 0.15}s`}
              path={edgePath}
              keyPoints="0;1"
              keyTimes="0;1"
              calcMode="linear"
            />
            <animate
              attributeName="opacity"
              values="0;0.5;0.3;0"
              dur={particleDur}
              repeatCount="indefinite"
              begin={`${(i * 1.5) / 2 + 0.15}s`}
            />
          </circle>
        );
      })}

      {/* marker */}
      {markerEnd && <path d={edgePath} fill="none" stroke="none" markerEnd={markerEnd} />}
    </g>
  );
};

export default memo(CyberTrail);
