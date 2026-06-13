/**
 * 新手教程引导覆盖层 — 报告第2章要求: "引入新手教程模式"
 *
 * 当 tutorial_mode=true 时，在关键 UI 区域显示引导提示。
 * 用户可在任何步骤点击"关闭教程"永久关闭。
 */

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { t } from '../lib/i18n';
import { useTutorialStore } from '../stores/tutorialStore';

interface GuideTip {
  id: string;
  target: string;      // CSS 选择器
  titleKey: string;    // i18n key for title
  contentKey: string;  // i18n key for content
  position: 'top' | 'bottom' | 'left' | 'right';
}

const GUIDE_TIPS: GuideTip[] = [
  {
    id: 'sidebar-crews',
    target: '[data-guide="sidebar-crews"], nav a[href*="/"]',
    titleKey: 'tutorial.tip_0.title',
    contentKey: 'tutorial.tip_0.content',
    position: 'right',
  },
  {
    id: 'create-crew',
    target: '[data-guide="create-crew"], button[data-guide="new-crew"]',
    titleKey: 'tutorial.tip_1.title',
    contentKey: 'tutorial.tip_1.content',
    position: 'bottom',
  },
  {
    id: 'templates',
    target: 'a[href*="templates"], [data-guide="templates"]',
    titleKey: 'tutorial.tip_2.title',
    contentKey: 'tutorial.tip_2.content',
    position: 'right',
  },
  {
    id: 'settings-apikey',
    target: 'a[href*="settings"], [data-guide="settings"]',
    titleKey: 'tutorial.tip_3.title',
    contentKey: 'tutorial.tip_3.content',
    position: 'right',
  },
  {
    id: 'knowledge-bases',
    target: 'a[href*="knowledge"], [data-guide="knowledge"]',
    titleKey: 'tutorial.tip_4.title',
    contentKey: 'tutorial.tip_4.content',
    position: 'right',
  },
  {
    id: 'mcp-tools',
    target: 'a[href*="mcp"], [data-guide="mcp"]',
    titleKey: 'tutorial.tip_5.title',
    contentKey: 'tutorial.tip_5.content',
    position: 'right',
  },
  {
    id: 'execution-monitor',
    target: '[data-guide="execution"], a[href*="execution"]',
    titleKey: 'tutorial.tip_6.title',
    contentKey: 'tutorial.tip_6.content',
    position: 'right',
  },
];

export default function TutorialOverlay() {
  const [isActive, setIsActive] = useState(false);
  const [targetRect, setTargetRect] = useState<DOMRect | null>(null);

  const tutorialMode = useTutorialStore((s) => s.tutorialMode);
  const setTutorialMode = useTutorialStore((s) => s.setTutorialMode);
  const currentTipIndex = useTutorialStore((s) => s.currentTipIndex);
  const setTipIndex = useTutorialStore((s) => s.setTipIndex);

  useEffect(() => {
    if (tutorialMode) {
      // 延迟启动，等待页面加载完成
      const timer = setTimeout(() => setIsActive(true), 1500);
      return () => clearTimeout(timer);
    }
  }, [tutorialMode]);

  useEffect(() => {
    if (!isActive) return;
    const tip = GUIDE_TIPS[currentTipIndex];
    if (!tip) {
      setIsActive(false);
      return;
    }

    const findTarget = () => {
      const el = document.querySelector(tip.target);
      if (el) {
        setTargetRect(el.getBoundingClientRect());
      } else {
        // 目标元素不存在，跳到下一个
        handleNext();
      }
    };

    findTarget();
    const observer = new MutationObserver(findTarget);
    observer.observe(document.body, { childList: true, subtree: true });

    return () => observer.disconnect();
  }, [isActive, currentTipIndex]);

  const handleNext = () => {
    if (currentTipIndex < GUIDE_TIPS.length - 1) {
      setTipIndex(currentTipIndex + 1);
    } else {
      handleDismiss();
    }
  };

  const handleDismiss = () => {
    setIsActive(false);
    setTutorialMode(false);
  };

  if (!isActive || !targetRect) return null;

  const tip = GUIDE_TIPS[currentTipIndex];
  if (!tip) return null;

  // 计算提示框位置
  const tooltipStyle: React.CSSProperties = {
    position: 'fixed',
    zIndex: 99999,
    ...(tip.position === 'bottom' && {
      top: targetRect.bottom + 12,
      left: targetRect.left + targetRect.width / 2 - 150,
    }),
    ...(tip.position === 'top' && {
      top: targetRect.top - 80,
      left: targetRect.left + targetRect.width / 2 - 150,
    }),
    ...(tip.position === 'right' && {
      top: targetRect.top + targetRect.height / 2 - 40,
      left: targetRect.right + 12,
    }),
    ...(tip.position === 'left' && {
      top: targetRect.top + targetRect.height / 2 - 40,
      left: targetRect.left - 312,
    }),
  };

  // 高亮框位置
  const highlightStyle: React.CSSProperties = {
    position: 'fixed',
    top: targetRect.top - 4,
    left: targetRect.left - 4,
    width: targetRect.width + 8,
    height: targetRect.height + 8,
    border: '2px solid #3b82f6',
    borderRadius: 8,
    zIndex: 99998,
    pointerEvents: 'none',
    boxShadow: '0 0 0 9999px rgba(0, 0, 0, 0.4)',
  };

  return (
    <>
      <div style={highlightStyle} />
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        style={tooltipStyle}
        className="w-[300px] bg-gray-900 border border-blue-500/50 rounded-xl p-4 shadow-2xl"
      >
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-blue-400 font-medium">
            🎓 {t('common.tutorial_label')}{' '}
            {t('common.step_counter', { current: currentTipIndex + 1, total: GUIDE_TIPS.length })}
          </span>
          <button
            onClick={handleDismiss}
            className="text-xs text-gray-500 hover:text-white"
            aria-label={t('common.close_tutorial')}
          >
            {t('common.close_tutorial')} ✕
          </button>
        </div>
        <h4 className="text-white font-semibold mb-1">{t(tip.titleKey)}</h4>
        <p className="text-sm text-gray-400 mb-3">{t(tip.contentKey)}</p>
        <button
          onClick={handleNext}
          className="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-all"
        >
          {currentTipIndex < GUIDE_TIPS.length - 1
            ? t('common.next_step')
            : t('common.complete_tutorial')}
        </button>
      </motion.div>
    </>
  );
}
