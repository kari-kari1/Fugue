/*
 * Fugue — Framer Motion 变体定义
 * 所有弹簧参数来自 Apple SwiftUI .spring() (v)
 */

import type { Variants, Transition } from 'framer-motion';

/* Apple 默认弹簧 — response: 0.55s, damping: 0.826 (v) */
export const springDefault: Transition = {
  type: 'spring',
  stiffness: 120,
  damping: 15,
  mass: 1.0,
};

/* 交互弹簧 — 更快响应 (v) */
export const springInteractive: Transition = {
  type: 'spring',
  stiffness: 300,
  damping: 25,
  mass: 1.0,
};

/* 文字揭示弹簧 — 高初速度，干脆停下 */
export const springReveal: Transition = {
  type: 'spring',
  stiffness: 200,
  damping: 25,
  mass: 0.5,
};

/* 文字遮罩揭示 — Carbon Neutral 核心动效 (v) */
export const textRevealVariants: Variants = {
  hidden: {
    y: '100%',
    clipPath: 'inset(0% 0% 100% 0%)',
  },
  visible: {
    y: '0%',
    clipPath: 'inset(0% 0% 0% 0%)',
    transition: springReveal,
  },
};

/* Stagger 容器 — 50ms 间隔 (v) */
export const staggerContainer: Variants = {
  hidden: {},
  visible: {
    transition: {
      staggerChildren: 0.05,
      delayChildren: 0.1,
    },
  },
};

/* Stagger 子元素 — 从下方滑入 (v) */
export const staggerItem: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: springDefault,
  },
};

/* 按钮交互 — whileTap: scale(0.97), whileHover: scale(1.02) (v) */
export const buttonTap = { scale: 0.97 };
export const buttonHover = { scale: 1.02 };
export const buttonTransition: Transition = springInteractive;

/* 卡片悬浮 */
export const cardHover = { y: -2 };

/* 淡入上升 — 通用入场 */
export const fadeInUp: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: springDefault,
  },
};

/* 隧道过渡 — 静态态 → 动态态 */
export const tunnelToStatic: Variants = {
  cyber: {
    scale: [1, 1.1, 1],
    opacity: [1, 0.5, 1],
    filter: ['blur(0px)', 'blur(4px)', 'blur(0px)'],
  },
  static: {
    scale: 1,
    opacity: 1,
    filter: 'blur(0px)',
    transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] },
  },
};
