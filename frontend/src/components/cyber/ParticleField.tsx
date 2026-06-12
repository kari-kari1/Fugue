/*
 * Canvas 粒子背景 — 动态态深空粒子场（增强版）
 * 更多粒子 + 更强光晕 + 速度变化 + 呼吸脉动 + 光网连线
 * 性能: Canvas 2D，非 DOM 元素
 */

import React, { useRef, useEffect } from 'react';

interface ParticleFieldProps {
  width: number;
  height: number;
}

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  baseSize: number;
  color: string;
  glowColor: string;
  phase: number; // 脉动相位
  speed: number; // 速度倍率
}

const PARTICLE_COUNT = 120;
const CONNECTION_DISTANCE = 180;
const COLORS = [
  { fill: 'rgba(0, 212, 255, 0.35)', glow: 'rgba(0, 212, 255, 0.15)' },
  { fill: 'rgba(175, 82, 222, 0.25)', glow: 'rgba(175, 82, 222, 0.12)' },
  { fill: 'rgba(0, 212, 255, 0.2)',  glow: 'rgba(0, 212, 255, 0.1)' },
  { fill: 'rgba(48, 209, 88, 0.15)', glow: 'rgba(48, 209, 88, 0.08)' },
  { fill: 'rgba(255, 214, 10, 0.12)', glow: 'rgba(255, 214, 10, 0.06)' },
];

export const ParticleField: React.FC<ParticleFieldProps> = ({ width, height }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const particlesRef = useRef<Particle[]>([]);
  const animRef = useRef<number>(0);
  const timeRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // 高 DPI 支持
    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);

    // 初始化粒子 — 带速度变化和脉动
    particlesRef.current = Array.from({ length: PARTICLE_COUNT }, () => {
      const colorSet = COLORS[Math.floor(Math.random() * COLORS.length)];
      const baseSize = Math.random() * 2.5 + 0.8;
      return {
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        size: baseSize,
        baseSize,
        color: colorSet.fill,
        glowColor: colorSet.glow,
        phase: Math.random() * Math.PI * 2,
        speed: 0.5 + Math.random() * 1.0, // 0.5x - 1.5x 速度变化
      };
    });

    const animate = () => {
      ctx.clearRect(0, 0, width, height);
      timeRef.current += 0.016; // ~60fps
      const t = timeRef.current;
      const particles = particlesRef.current;

      // 更新和绘制粒子
      for (const p of particles) {
        // 带速度变化的移动
        p.x += p.vx * p.speed;
        p.y += p.vy * p.speed;

        // 边界反弹
        if (p.x < 0 || p.x > width) p.vx *= -1;
        if (p.y < 0 || p.y > height) p.vy *= -1;

        // 呼吸脉动 — 大小周期性变化
        const pulse = 1 + 0.3 * Math.sin(t * 2 + p.phase);
        p.size = p.baseSize * pulse;

        // 绘制光晕（更大更柔和的圆）
        const glowRadius = p.size * 3;
        const gradient = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, glowRadius);
        gradient.addColorStop(0, p.glowColor);
        gradient.addColorStop(1, 'transparent');
        ctx.beginPath();
        ctx.arc(p.x, p.y, glowRadius, 0, Math.PI * 2);
        ctx.fillStyle = gradient;
        ctx.fill();

        // 绘制核心粒子
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.fill();
      }

      // 粒子间连线 — 更亮、更远距离
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < CONNECTION_DISTANCE) {
            const alpha = (1 - dist / CONNECTION_DISTANCE) * 0.2;
            // 连线也有呼吸感
            const breathAlpha = alpha * (0.8 + 0.2 * Math.sin(t * 1.5 + i * 0.1));
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.strokeStyle = `rgba(0, 212, 255, ${breathAlpha})`;
            ctx.lineWidth = 0.5;
            ctx.stroke();
          }
        }
      }

      // 随机光闪 — 偶尔出现的明亮闪光点
      if (Math.random() < 0.02) {
        const fx = Math.random() * width;
        const fy = Math.random() * height;
        const flashGrad = ctx.createRadialGradient(fx, fy, 0, fx, fy, 30);
        flashGrad.addColorStop(0, 'rgba(0, 212, 255, 0.15)');
        flashGrad.addColorStop(1, 'transparent');
        ctx.beginPath();
        ctx.arc(fx, fy, 30, 0, Math.PI * 2);
        ctx.fillStyle = flashGrad;
        ctx.fill();
      }

      animRef.current = requestAnimationFrame(animate);
    };

    animate();
    return () => cancelAnimationFrame(animRef.current);
  }, [width, height]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width,
        height,
        pointerEvents: 'none',
        zIndex: 0,
      }}
    />
  );
};
