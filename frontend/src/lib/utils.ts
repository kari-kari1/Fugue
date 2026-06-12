import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import React from 'react';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** 将后端返回的无时区 UTC 时间字符串解析为正确的 Date 对象 */
export function parseUTC(date: string | Date): Date {
  if (date instanceof Date) return date;
  // 后端 utcnow() 剥去了时区标记，导致 new Date() 按本地时间解析
  // 补上 'Z' 后缀确保按 UTC 解析
  if (typeof date === 'string' && !date.endsWith('Z') && !date.includes('+') && !date.includes('-', 10)) {
    return new Date(date + 'Z');
  }
  return new Date(date);
}

export function formatDate(date: string | Date): string {
  return parseUTC(date).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatNumber(num: number): string {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toString();
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);
}

export function generateId(): string {
  return Math.random().toString(36).substring(2, 11);
}

export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}

export function getStatusColor(status: string): string {
  switch (status) {
    case 'completed':
      return 'text-accent-green bg-accent-green-dim';
    case 'running':
      return 'text-accent-cyan bg-accent-cyan-dim';
    case 'failed':
      return 'text-accent-red bg-accent-red-dim';
    case 'pending':
      return 'text-accent-amber bg-accent-amber-dim';
    case 'cancelled':
      return 'text-tertiary bg-white/[0.05]';
    case 'retrying':
      return 'text-accent-amber bg-accent-amber-dim';
    case 'paused':
      return 'text-[var(--accent-violet)] bg-[var(--accent-violet-dim)]';
    default:
      return 'text-tertiary bg-white/[0.05]';
  }
}

export function getAgentEmoji(role: string): string {
  const roleLower = role.toLowerCase();
  if (roleLower.includes('research') || roleLower.includes('研究')) return '🔍';
  if (roleLower.includes('writer') || roleLower.includes('写手') || roleLower.includes('撰写')) return '✍️';
  if (roleLower.includes('review') || roleLower.includes('审核')) return '🔍';
  if (roleLower.includes('analyst') || roleLower.includes('分析')) return '📊';
  if (roleLower.includes('developer') || roleLower.includes('开发')) return '💻';
  if (roleLower.includes('designer') || roleLower.includes('设计')) return '🎨';
  if (roleLower.includes('manager') || roleLower.includes('经理')) return '👔';
  return '🤖';
}

export function getModelIcon(provider: string): string {
  switch (provider.toLowerCase()) {
    case 'openai': return '🟢';
    case 'anthropic': return '🟠';
    case 'google': return '🔵';
    case 'ollama': return '🦙';
    default: return '⚪';
  }
}

export function getModelDotColor(provider: string): string {
  switch (provider.toLowerCase()) {
    case 'openai': return '#A3BE8C';
    case 'anthropic': return '#D9B867';
    case 'google': return '#89B4FA';
    case 'ollama': return '#C4A5E8';
    default: return '#5C5C6A';
  }
}

// Abstract geometric SVG icons for agent roles
export function getAgentIcon(role: string): React.ReactNode {
  const roleLower = role.toLowerCase();

  const gradientId = `grad-${role.replace(/[^a-z]/gi, '')}`;

  if (roleLower.includes('research') || roleLower.includes('研究')) {
    return React.createElement('svg', { width: 20, height: 20, viewBox: '0 0 20 20', fill: 'none' },
      React.createElement('defs', null,
        React.createElement('linearGradient', { id: gradientId, x1: '0', y1: '0', x2: '20', y2: '20' },
          React.createElement('stop', { offset: '0%', stopColor: '#89B4FA' }),
          React.createElement('stop', { offset: '100%', stopColor: '#C4A5E8' })
        )
      ),
      React.createElement('circle', { cx: '8', cy: '8', r: '5.5', stroke: `url(#${gradientId})`, strokeWidth: '1.5', fill: 'none' }),
      React.createElement('line', { x1: '12', y1: '12', x2: '17', y2: '17', stroke: `url(#${gradientId})`, strokeWidth: '1.5', strokeLinecap: 'round' })
    );
  }

  if (roleLower.includes('writer') || roleLower.includes('写手') || roleLower.includes('撰写')) {
    return React.createElement('svg', { width: 20, height: 20, viewBox: '0 0 20 20', fill: 'none' },
      React.createElement('defs', null,
        React.createElement('linearGradient', { id: gradientId, x1: '0', y1: '0', x2: '20', y2: '20' },
          React.createElement('stop', { offset: '0%', stopColor: '#89B4FA' }),
          React.createElement('stop', { offset: '100%', stopColor: '#A3BE8C' })
        )
      ),
      React.createElement('path', { d: 'M3 17L7 3L10 13L13 7L17 17', stroke: `url(#${gradientId})`, strokeWidth: '1.5', strokeLinecap: 'round', strokeLinejoin: 'round', fill: 'none' })
    );
  }

  if (roleLower.includes('analyst') || roleLower.includes('分析')) {
    return React.createElement('svg', { width: 20, height: 20, viewBox: '0 0 20 20', fill: 'none' },
      React.createElement('defs', null,
        React.createElement('linearGradient', { id: gradientId, x1: '0', y1: '20', x2: '20', y2: '0' },
          React.createElement('stop', { offset: '0%', stopColor: '#89B4FA' }),
          React.createElement('stop', { offset: '100%', stopColor: '#D9B867' })
        )
      ),
      React.createElement('rect', { x: '2', y: '12', width: '3', height: '6', rx: '1', fill: `url(#${gradientId})`, opacity: '0.6' }),
      React.createElement('rect', { x: '7', y: '8', width: '3', height: '10', rx: '1', fill: `url(#${gradientId})`, opacity: '0.8' }),
      React.createElement('rect', { x: '12', y: '4', width: '3', height: '14', rx: '1', fill: `url(#${gradientId})` }),
      React.createElement('line', { x1: '2', y1: '4', x2: '18', y2: '4', stroke: `url(#${gradientId})`, strokeWidth: '1', opacity: '0.3' })
    );
  }

  if (roleLower.includes('developer') || roleLower.includes('开发')) {
    return React.createElement('svg', { width: 20, height: 20, viewBox: '0 0 20 20', fill: 'none' },
      React.createElement('defs', null,
        React.createElement('linearGradient', { id: gradientId, x1: '0', y1: '0', x2: '20', y2: '20' },
          React.createElement('stop', { offset: '0%', stopColor: '#89B4FA' }),
          React.createElement('stop', { offset: '100%', stopColor: '#C4A5E8' })
        )
      ),
      React.createElement('polyline', { points: '7,6 3,10 7,14', stroke: `url(#${gradientId})`, strokeWidth: '1.5', strokeLinecap: 'round', strokeLinejoin: 'round', fill: 'none' }),
      React.createElement('polyline', { points: '13,6 17,10 13,14', stroke: `url(#${gradientId})`, strokeWidth: '1.5', strokeLinecap: 'round', strokeLinejoin: 'round', fill: 'none' }),
      React.createElement('line', { x1: '11', y1: '4', x2: '9', y2: '16', stroke: `url(#${gradientId})`, strokeWidth: '1.5', strokeLinecap: 'round', opacity: '0.6' })
    );
  }

  // Default: neural network node pattern
  return React.createElement('svg', { width: 20, height: 20, viewBox: '0 0 20 20', fill: 'none' },
    React.createElement('defs', null,
      React.createElement('linearGradient', { id: gradientId, x1: '0', y1: '0', x2: '20', y2: '20' },
        React.createElement('stop', { offset: '0%', stopColor: '#89B4FA' }),
        React.createElement('stop', { offset: '100%', stopColor: '#C4A5E8' })
      )
    ),
    React.createElement('circle', { cx: '10', cy: '6', r: '2.5', stroke: `url(#${gradientId})`, strokeWidth: '1.5', fill: 'none' }),
    React.createElement('circle', { cx: '5', cy: '15', r: '2.5', stroke: `url(#${gradientId})`, strokeWidth: '1.5', fill: 'none' }),
    React.createElement('circle', { cx: '15', cy: '15', r: '2.5', stroke: `url(#${gradientId})`, strokeWidth: '1.5', fill: 'none' }),
    React.createElement('line', { x1: '10', y1: '8.5', x2: '5', y2: '12.5', stroke: `url(#${gradientId})`, strokeWidth: '1', opacity: '0.5' }),
    React.createElement('line', { x1: '10', y1: '8.5', x2: '15', y2: '12.5', stroke: `url(#${gradientId})`, strokeWidth: '1', opacity: '0.5' }),
    React.createElement('line', { x1: '7.5', y1: '15', x2: '12.5', y2: '15', stroke: `url(#${gradientId})`, strokeWidth: '1', opacity: '0.3' })
  );
}

// Task icon - abstract checklist
export function getTaskIcon(): React.ReactNode {
  return React.createElement('svg', { width: 20, height: 20, viewBox: '0 0 20 20', fill: 'none' },
    React.createElement('defs', null,
      React.createElement('linearGradient', { id: 'task-grad', x1: '0', y1: '0', x2: '20', y2: '20' },
        React.createElement('stop', { offset: '0%', stopColor: '#A3BE8C' }),
        React.createElement('stop', { offset: '100%', stopColor: '#89B4FA' })
      )
    ),
    React.createElement('rect', { x: '3', y: '3', width: '14', height: '14', rx: '3', stroke: 'url(#task-grad)', strokeWidth: '1.5', fill: 'none' }),
    React.createElement('polyline', { points: '7,10 9,12 13,8', stroke: 'url(#task-grad)', strokeWidth: '1.5', strokeLinecap: 'round', strokeLinejoin: 'round', fill: 'none' })
  );
}

// Condition icon - diamond branch
export function getConditionIcon(): React.ReactNode {
  return React.createElement('svg', { width: 20, height: 20, viewBox: '0 0 20 20', fill: 'none' },
    React.createElement('defs', null,
      React.createElement('linearGradient', { id: 'cond-grad-icon', x1: '0', y1: '0', x2: '20', y2: '20' },
        React.createElement('stop', { offset: '0%', stopColor: '#AF52DE' }),
        React.createElement('stop', { offset: '100%', stopColor: '#FF9F0A' })
      )
    ),
    React.createElement('path', { d: 'M10 2L18 10L10 18L2 10L10 2Z', stroke: 'url(#cond-grad-icon)', strokeWidth: '1.5', fill: 'url(#cond-grad-icon)', fillOpacity: '0.1' }),
    React.createElement('path', { d: 'M7 8L10 5L13 8', stroke: 'url(#cond-grad-icon)', strokeWidth: '1.2', strokeLinecap: 'round', strokeLinejoin: 'round' }),
    React.createElement('path', { d: 'M10 5V13', stroke: 'url(#cond-grad-icon)', strokeWidth: '1.2', strokeLinecap: 'round' }),
    React.createElement('path', { d: 'M7 12L10 15L13 12', stroke: 'url(#cond-grad-icon)', strokeWidth: '1.2', strokeLinecap: 'round', strokeLinejoin: 'round' })
  );
}

// Loop icon - circular arrow
export function getLoopIcon(): React.ReactNode {
  return React.createElement('svg', { width: 20, height: 20, viewBox: '0 0 20 20', fill: 'none' },
    React.createElement('defs', null,
      React.createElement('linearGradient', { id: 'loop-grad-icon', x1: '0', y1: '0', x2: '20', y2: '20' },
        React.createElement('stop', { offset: '0%', stopColor: '#FF9F0A' }),
        React.createElement('stop', { offset: '100%', stopColor: '#FFD60A' })
      )
    ),
    React.createElement('path', { d: 'M14 4L16 6L14 8', stroke: 'url(#loop-grad-icon)', strokeWidth: '1.5', strokeLinecap: 'round', strokeLinejoin: 'round' }),
    React.createElement('path', { d: 'M16 6C16 6 12 6 10 6C7.79 6 6 7.79 6 10C6 12.21 7.79 14 10 14C12.21 14 14 12.21 14 10', stroke: 'url(#loop-grad-icon)', strokeWidth: '1.5', strokeLinecap: 'round', fill: 'none' }),
    React.createElement('path', { d: 'M6 16L4 14L6 12', stroke: 'url(#loop-grad-icon)', strokeWidth: '1.5', strokeLinecap: 'round', strokeLinejoin: 'round' }),
    React.createElement('path', { d: 'M4 14C4 14 8 14 10 14C12.21 14 14 12.21 14 10', stroke: 'url(#loop-grad-icon)', strokeWidth: '1.5', strokeLinecap: 'round', fill: 'none' })
  );
}

// Human review icon - person with checkmark
export function getReviewIcon(): React.ReactNode {
  return React.createElement('svg', { width: 20, height: 20, viewBox: '0 0 20 20', fill: 'none' },
    React.createElement('defs', null,
      React.createElement('linearGradient', { id: 'review-grad-icon', x1: '0', y1: '0', x2: '20', y2: '20' },
        React.createElement('stop', { offset: '0%', stopColor: '#EC4899' }),
        React.createElement('stop', { offset: '100%', stopColor: '#F472B6' })
      )
    ),
    React.createElement('circle', { cx: '10', cy: '7', r: '3.5', stroke: 'url(#review-grad-icon)', strokeWidth: '1.5', fill: '#FCE7F3' }),
    React.createElement('path', { d: 'M4 17C4 13.686 6.68629 11 10 11C13.3137 11 16 13.686 16 17', stroke: 'url(#review-grad-icon)', strokeWidth: '1.5', strokeLinecap: 'round' }),
    React.createElement('path', { d: 'M14 5L15.5 6.5L18 4', stroke: 'url(#review-grad-icon)', strokeWidth: '1.5', strokeLinecap: 'round', strokeLinejoin: 'round' })
  );
}
