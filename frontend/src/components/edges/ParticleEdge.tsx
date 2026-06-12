import React from 'react';
import { getBezierPath, type EdgeProps } from '@xyflow/react';

const ParticleEdge: React.FC<EdgeProps> = ({
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

  const colorKey = (data as { color?: string })?.color === 'green' ? 'sage' : 'steel';
  const isExecuting = (data as { executing?: boolean })?.executing;

  // 颜色配置
  const mainColor = colorKey === 'sage' ? '#34C759' : '#0071E3';
  const glowColor = colorKey === 'sage' ? 'rgba(52,199,89,' : 'rgba(0,113,227,';

  // 动态参数
  const particleDur = isExecuting ? '1.5s' : '3s';
  const particleCount = isExecuting ? 6 : 4;
  return (
    <g>
      {/* 定义渐变和滤镜 */}
      <defs>
        {/* 流动渐变 — 从源到目标 */}
        <linearGradient id={`edge-grad-${id}`} x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor={mainColor} stopOpacity={selected ? 0.8 : 0.3} />
          <stop offset="50%" stopColor={mainColor} stopOpacity={selected ? 1 : 0.5} />
          <stop offset="100%" stopColor={mainColor} stopOpacity={selected ? 0.8 : 0.3} />
        </linearGradient>

        {/* 粒子发光滤镜 */}
        <filter id={`glow-${id}`} x="-100%" y="-100%" width="300%" height="300%">
          <feGaussianBlur in="SourceGraphic" stdDeviation="3" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>

        {/* 大光晕滤镜 */}
        <filter id={`glow-lg-${id}`} x="-200%" y="-200%" width="500%" height="500%">
          <feGaussianBlur in="SourceGraphic" stdDeviation="6" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* 底层：极淡虚线流动轨迹 */}
      <path
        d={edgePath}
        fill="none"
        stroke={selected ? `${glowColor}0.15)` : `${glowColor}0.04)`}
        strokeWidth={selected ? 8 : 4}
        strokeLinecap="round"
      />

      {/* 中层：渐变主线 */}
      <path
        d={edgePath}
        fill="none"
        stroke={`url(#edge-grad-${id})`}
        strokeWidth={selected ? 2.5 : 1.5}
        strokeLinecap="round"
        markerEnd={markerEnd}
      />

      {/* 流动虚线覆盖层（选中/执行时） */}
      {(selected || isExecuting) && (
        <path
          d={edgePath}
          fill="none"
          stroke={mainColor}
          strokeWidth={1}
          strokeDasharray="6 8"
          strokeLinecap="round"
          opacity={0.4}
        >
          <animate
            attributeName="stroke-dashoffset"
            values="0;-28"
            dur="1s"
            repeatCount="indefinite"
          />
        </path>
      )}

      {/* 粒子光点 */}
      {Array.from({ length: particleCount }).map((_, i) => {
        const begin = `${i * (parseFloat(particleDur) / particleCount)}s`;
        const isLead = i === 0;
        return (
          <g key={i}>
            {/* 大光晕（领头粒子） */}
            {isLead && (
              <circle
                r={6}
                fill={mainColor}
                opacity={0}
                filter={`url(#glow-lg-${id})`}
              >
                <animateMotion
                  dur={particleDur}
                  repeatCount="indefinite"
                  begin={begin}
                  path={edgePath}
                />
                <animate
                  attributeName="opacity"
                  values="0;0.3;0.3;0"
                  dur={particleDur}
                  repeatCount="indefinite"
                  begin={begin}
                />
              </circle>
            )}

            {/* 粒子本体 */}
            <circle
              r={isLead ? 3 : 2}
              fill={isLead ? '#FFFFFF' : mainColor}
              opacity={0}
              filter={`url(#glow-${id})`}
            >
              <animateMotion
                dur={particleDur}
                repeatCount="indefinite"
                begin={begin}
                path={edgePath}
              />
              <animate
                attributeName="opacity"
                values="0;0.9;0.9;0.1"
                dur={particleDur}
                repeatCount="indefinite"
                begin={begin}
              />
              <animate
                attributeName="r"
                values={isLead ? '1;3.5;3;1' : '0.5;2.5;2;0.5'}
                dur={particleDur}
                repeatCount="indefinite"
                begin={begin}
              />
            </circle>

            {/* 拖尾 */}
            {isLead && (
              <circle
                r={2}
                fill={mainColor}
                opacity={0}
              >
                <animateMotion
                  dur={particleDur}
                  repeatCount="indefinite"
                  begin={begin}
                  keyPoints="0;0.92"
                  keyTimes="0;1"
                  path={edgePath}
                />
                <animate
                  attributeName="opacity"
                  values="0;0.4;0.4;0"
                  dur={particleDur}
                  repeatCount="indefinite"
                  begin={begin}
                />
                <animate
                  attributeName="r"
                  values="0.5;2;1.5;0.5"
                  dur={particleDur}
                  repeatCount="indefinite"
                  begin={begin}
                />
              </circle>
            )}
          </g>
        );
      })}

      {/* 起点发光点 */}
      <circle cx={sourceX} cy={sourceY} r={selected ? 4 : 2.5} fill={mainColor} opacity={selected ? 0.6 : 0.2}>
        <animate attributeName="r" values={`${selected ? 3 : 2};${selected ? 5 : 3};${selected ? 3 : 2}`} dur="2s" repeatCount="indefinite" />
        <animate attributeName="opacity" values={`${selected ? 0.4 : 0.15};${selected ? 0.7 : 0.3};${selected ? 0.4 : 0.15}`} dur="2s" repeatCount="indefinite" />
      </circle>

      {/* 终点发光点 */}
      <circle cx={targetX} cy={targetY} r={selected ? 4 : 2.5} fill={mainColor} opacity={selected ? 0.6 : 0.2}>
        <animate attributeName="r" values={`${selected ? 3 : 2};${selected ? 5 : 3};${selected ? 3 : 2}`} dur="2.3s" repeatCount="indefinite" />
        <animate attributeName="opacity" values={`${selected ? 0.4 : 0.15};${selected ? 0.7 : 0.3};${selected ? 0.4 : 0.15}`} dur="2.3s" repeatCount="indefinite" />
      </circle>
    </g>
  );
};

export default ParticleEdge;
