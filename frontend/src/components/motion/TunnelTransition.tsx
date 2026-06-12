/*
 * 隧道过渡组件 — 超空间跃迁 v4
 * 入场: 光痕从屏幕中心(50vw,50vh)向四周爆射（更长持续时间）
 * 出场: 光痕从四周收拢到中心（更短持续时间）
 * 使用 left/top 像素定位 + translate 动画，确保中心点准确
 */

import React, { useEffect, useRef, useCallback, useMemo, useState } from 'react';
import { motion, useAnimation } from 'framer-motion';
import { useThemeStore } from '../../stores/themeStore';

const NUM_TRAILS = 72;
const EXIT_TRAIL_DURATION = 1.5;  // 退场光痕飞行时间（秒）

const seededRandom = (seed: number) => {
  let s = seed;
  return () => { s = (s * 16807) % 2147483647; return (s - 1) / 2147483646; };
};

interface TunnelTransitionProps {
  children: React.ReactNode;
}

interface TrailConfig {
  // 飞行方向（角度）
  angle: number;
  // 光痕尺寸
  length: number;
  width: number;
  // 动画时序
  delay: number;
  entryDuration: number;  // 入场：中心→四周
  exitDuration: number;   // 出场：四周→中心
  // 外观
  color: string;
  glowIntensity: number;
  // 飞行距离（从中心到边缘的倍率）
  distance: number;
}

export const TunnelTransition: React.FC<TunnelTransitionProps> = ({ children }) => {
  const { transitionDirection } = useThemeStore();
  const contentControls = useAnimation();
  const overlayControls = useAnimation();
  const flashControls = useAnimation();
  const prevDirection = useRef<string | null>(null);
  const [trailsVisible, setTrailsVisible] = useState(false);
  const [trailsExiting, setTrailsExiting] = useState(false);
  const [trailsReverse, setTrailsReverse] = useState(false);

  const CYAN = ['#00FFFF', '#00E5FF', '#00D4FF', '#22D3EE', '#06B6D4'];
  const VIOLET = ['#BF40FF', '#AF52DE', '#C084FC', '#A855F7', '#9333EA'];

  const trails: TrailConfig[] = useMemo(() => {
    const rng = seededRandom(42);
    return Array.from({ length: NUM_TRAILS }, (_, i) => {
      const isCyan = rng() > 0.45;
      const colorArr = isCyan ? CYAN : VIOLET;
      return {
        angle: (i / NUM_TRAILS) * 360 + (rng() - 0.5) * 8,
        length: 250 + rng() * 450,
        width: 2.5 + rng() * 4,
        delay: rng() * 0.3,
        entryDuration: 1.8,  // 入场光痕飞行 1.8s（配合 3s 总时长）
        exitDuration: 4.5,   // 退场由 EXIT_TRAIL_DURATION 覆盖
        color: colorArr[Math.floor(rng() * colorArr.length)],
        glowIntensity: 0.5 + rng() * 0.5,
        distance: 0.8 + rng() * 0.6, // 0.8-1.4 倍屏幕对角线
      };
    });
  }, []);

  const runToCyber = useCallback(async () => {
    // Phase 1: 按钮脉冲（0.2s）
    await contentControls.start({
      scale: [1, 1.05, 1],
      transition: { duration: 0.2, ease: [0.7, 0, 0.1, 1] },
    });

    // Phase 2: 启动光痕 + 黑色遮罩（0.15s）
    setTrailsExiting(false);
    setTrailsReverse(false);
    setTrailsVisible(true);
    overlayControls.start({ opacity: 1, transition: { duration: 0.15, ease: 'easeIn' } });

    // Phase 3: 内容缩小消失（0.4s）
    await contentControls.start({
      scale: 2.5, opacity: 0, filter: 'blur(16px)',
      transition: { duration: 0.4, ease: [0.5, 0, 1, 1] },
    });

    // Phase 4: 等待光痕飞行（1.8s + 0.3s max delay）
    await new Promise(r => setTimeout(r, 2000));

    // Phase 5: 光痕溶散（0.25s）
    setTrailsExiting(true);
    await new Promise(r => setTimeout(r, 250));
    setTrailsVisible(false);
  }, [contentControls, overlayControls]);

  const runToStatic = useCallback(async () => {
    // Phase 1: 启动逆向光痕 + 黑色遮罩（0.1s）
    setTrailsReverse(true);
    setTrailsExiting(false);
    setTrailsVisible(true);
    overlayControls.start({ opacity: 1, transition: { duration: 0.1 } });

    // Phase 2: 等待光痕收缩完成（1.5s flight + 0.3s max delay = 1.8s）
    await new Promise(r => setTimeout(r, 1900));

    // Phase 3: 光痕溶散 → 移除 DOM
    setTrailsVisible(false);

    // Phase 4: 白光过曝（0.3s）
    await flashControls.start({
      opacity: [0, 1, 0],
      transition: { duration: 0.3, times: [0, 0.08, 1], ease: 'easeOut' },
    });

    // 不淡出覆盖层 —— 保持全黑遮罩，由 navigate() 直接切换页面
    // 避免露出已切换为 static 主题的运行界面内容（退场闪烁根因）
  }, [overlayControls, flashControls]);

  useEffect(() => {
    if (transitionDirection === prevDirection.current) return;
    prevDirection.current = transitionDirection;
    if (transitionDirection === 'to-cyber') runToCyber();
    else if (transitionDirection === 'to-static') runToStatic();
  }, [transitionDirection, runToCyber, runToStatic]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      {/* 主内容 */}
      <motion.div
        animate={contentControls}
        initial={{ scale: 1, opacity: 1, filter: 'blur(0px)' }}
        style={{
          position: 'relative', width: '100%', height: '100%',
          transformOrigin: 'center center',
          willChange: 'transform, opacity, filter',
        }}
      >
        {children}
      </motion.div>

      {/* 黑色遮罩 */}
      <motion.div
        animate={overlayControls}
        initial={{ opacity: 0 }}
        style={{
          position: 'fixed', inset: 0, zIndex: 9998,
          background: '#000000',
          pointerEvents: 'none',
        }}
      />

      {/* 超空间光痕层 — 直接渲染，不用 AnimatePresence */}
      {trailsVisible && (
          <div
            style={{
              position: 'fixed', inset: 0, zIndex: 9999,
              pointerEvents: 'none',
              overflow: 'hidden',
            }}
          >
            {trails.map((t, i) => {
              // 计算光痕从中心(50%, 50%)飞出的位移
              // angle 0° = 正上方，顺时针
              const rad = (t.angle - 90) * (Math.PI / 180);
              // 飞行距离：屏幕对角线 * distance 倍率
              const diag = Math.sqrt(window.innerWidth ** 2 + window.innerHeight ** 2);
              const flyDist = diag * t.distance;
              const endX = Math.cos(rad) * flyDist;
              const endY = Math.sin(rad) * flyDist;

              // 入场: 从中心(0,0) 飞向 (endX, endY)
              // 出场: 从 (endX, endY) 收回 中心(0,0)
              const startX = 0;
              const startY = 0;

              return (
                <motion.div
                  key={i}
                  initial={{
                    x: trailsReverse ? endX : startX,
                    y: trailsReverse ? endY : startY,
                    opacity: 0,
                    scale: trailsReverse ? 1.2 : 0.1,
                  }}
                  animate={{
                    x: trailsReverse ? [endX, 0] : [0, endX],
                    y: trailsReverse ? [endY, 0] : [0, endY],
                    opacity: trailsExiting
                      ? [0.95, 0]
                      : trailsReverse
                        ? [0, 0.95, 0.95, 0]
                        : [0, 0.95, 0.85, 0],
                    scale: trailsReverse
                      ? [1.2, 0.05]
                      : [0.1, 1.6],
                    filter: trailsExiting
                      ? ['blur(0px)', 'blur(12px)']
                      : ['blur(0px)', 'blur(0px)'],
                  }}
                  transition={{
                    duration: trailsReverse ? EXIT_TRAIL_DURATION : t.entryDuration,
                    delay: trailsReverse ? (0.2 - t.delay * 0.2) : t.delay,
                    ease: trailsReverse
                      ? [0, 0, 0.15, 1]   // 出场: 极速减速
                      : [0.4, 0, 1, 1],    // 入场: ease-in 加速
                    opacity: { duration: trailsExiting ? 0.25 : (trailsReverse ? EXIT_TRAIL_DURATION : t.entryDuration) },
                    filter: { duration: trailsExiting ? 0.25 : 0 },
                  }}
                  style={{
                    position: 'absolute',
                    left: '50%',
                    top: '50%',
                    marginTop: `-${t.length}px`,
                    marginLeft: `-${t.width / 2}px`,
                    width: `${t.width}px`,
                    height: `${t.length}px`,
                    transformOrigin: '50% 100%',
                    rotate: `${t.angle}deg`,
                    background: `linear-gradient(to top, transparent 0%, ${t.color}15 10%, ${t.color}40 30%, ${t.color}80 55%, ${t.color} 80%, ${t.color}FF 92%, #FFFFFF 100%)`,
                    borderRadius: '1px 1px 0 0',
                    boxShadow: `
                      0 0 ${6 * t.glowIntensity}px ${t.color},
                      0 0 ${18 * t.glowIntensity}px ${t.color}80,
                      0 0 ${35 * t.glowIntensity}px ${t.color}40
                    `,
                    willChange: 'transform, opacity, filter',
                  }}
                >
                  {/* 光痕头部高亮点 */}
                  <div style={{
                    position: 'absolute',
                    top: 0, left: '50%', transform: 'translateX(-50%)',
                    width: t.width * 3, height: t.width * 3,
                    borderRadius: '50%',
                    background: `radial-gradient(circle, #FFFFFF 0%, ${t.color} 35%, transparent 70%)`,
                    filter: 'blur(1.5px)',
                    opacity: 0.95,
                  }} />
                </motion.div>
              );
            })}

            {/* 中心 glow 点 */}
            <motion.div
              initial={{ opacity: 0, scale: 0 }}
              animate={{ opacity: [0, 1, 0.85], scale: [0, 2.5, 1.5] }}
              transition={{ duration: 0.6, ease: 'easeOut' }}
              style={{
                position: 'absolute',
                left: '50%', top: '50%',
                width: 14, height: 14,
                transform: 'translate(-50%, -50%)',
                borderRadius: '50%',
                background: '#FFFFFF',
                boxShadow: `
                  0 0 30px #00FFFF,
                  0 0 60px #00FFFF90,
                  0 0 100px #BF40FF60,
                  0 0 160px #00FFFF30
                `,
              }}
            />

            {/* 扩散光环 */}
            <motion.div
              initial={{ opacity: 0, scale: 0 }}
              animate={{ opacity: [0, 0.35, 0], scale: [0, 4, 8] }}
              transition={{ duration: 1.5, ease: 'easeOut' }}
              style={{
                position: 'absolute',
                left: '50%', top: '50%',
                width: 80, height: 80,
                transform: 'translate(-50%, -50%)',
                borderRadius: '50%',
                border: '2px solid rgba(0, 255, 255, 0.3)',
                boxShadow: '0 0 50px rgba(0, 255, 255, 0.15)',
              }}
            />
          </div>
        )}

      {/* 白光过曝 */}
      <motion.div
        animate={flashControls}
        initial={{ opacity: 0 }}
        style={{
          position: 'fixed', inset: 0, zIndex: 10001,
          background: '#FFFFFF',
          pointerEvents: 'none',
        }}
      />
    </div>
  );
};
