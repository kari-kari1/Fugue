/*
 * 主题状态管理 — 静态态 ↔ 动态态切换
 * 隧道过渡期间为 'transitioning' 状态
 */

import { create } from 'zustand';

export type ThemeMode = 'static' | 'cyber' | 'transitioning';

interface ThemeState {
  mode: ThemeMode;
  transitionDirection: 'to-cyber' | 'to-static' | null;

  enterCyberMode: () => void;
  exitCyberMode: () => void;
  setTransitioning: (dir: 'to-cyber' | 'to-static') => void;
}

export const useThemeStore = create<ThemeState>((set) => ({
  mode: 'static',
  transitionDirection: null,

  setTransitioning: (dir) => {
    set({ mode: 'transitioning', transitionDirection: dir });
    document.documentElement.setAttribute('data-theme', dir === 'to-cyber' ? 'cyber' : 'static');
  },

  enterCyberMode: () => {
    set({ mode: 'cyber', transitionDirection: null });
    document.documentElement.setAttribute('data-theme', 'cyber');
  },

  exitCyberMode: () => {
    set({ mode: 'static', transitionDirection: null });
    document.documentElement.setAttribute('data-theme', 'static');
  },
}));
