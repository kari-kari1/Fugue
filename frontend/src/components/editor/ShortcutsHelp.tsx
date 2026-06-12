/* 快捷键帮助弹窗 */

import React, { useState } from 'react';
import { createPortal } from 'react-dom';
import { Keyboard, X } from 'lucide-react';
import { useThemeStore } from '../../stores/themeStore';

const shortcuts = [
  { keys: ['Ctrl', 'S'], description: '保存' },
  { keys: ['Ctrl', 'Z'], description: '撤销' },
  { keys: ['Ctrl', 'Shift', 'Z'], description: '重做' },
  { keys: ['Ctrl', 'C'], description: '复制' },
  { keys: ['Ctrl', 'V'], description: '粘贴' },
  { keys: ['Delete'], description: '删除选中' },
  { keys: ['Ctrl', 'A'], description: '全选' },
  { keys: ['Ctrl', '+'], description: '放大' },
  { keys: ['Ctrl', '-'], description: '缩小' },
  { keys: ['Ctrl', '0'], description: '适应画布' },
];

export const ShortcutsHelp: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const themeMode = useThemeStore((s) => s.mode);
  const isDark = themeMode !== 'static';

  const modal = isOpen ? createPortal(
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: isDark ? 'rgba(0,0,0,0.6)' : 'rgba(0,0,0,0.35)',
        backdropFilter: 'blur(8px)',
        WebkitBackdropFilter: 'blur(8px)',
      }}
      onClick={() => setIsOpen(false)}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: '420px',
          maxWidth: '90vw',
          maxHeight: '80vh',
          borderRadius: '16px',
          background: isDark ? '#1C1C1E' : '#FFFFFF',
          border: isDark ? '0.5px solid rgba(255,255,255,0.1)' : '1px solid rgba(0,0,0,0.08)',
          boxShadow: '0 24px 80px rgba(0,0,0,0.3)',
          padding: '24px',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* 标题栏 */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px' }}>
          <span style={{ fontSize: '16px', fontWeight: 600, color: isDark ? '#F5F5F7' : '#1D1D1F' }}>
            快捷键
          </span>
          <button
            onClick={() => setIsOpen(false)}
            style={{
              width: '28px', height: '28px',
              borderRadius: '8px',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)',
              border: 'none', cursor: 'pointer',
              transition: 'background 0.15s',
            }}
            onMouseEnter={(e) => { e.currentTarget.style.background = isDark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.1)'; }}
            onMouseLeave={(e) => { e.currentTarget.style.background = isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.05)'; }}
          >
            <X style={{ width: '16px', height: '16px', color: isDark ? '#A1A1A6' : '#636366' }} />
          </button>
        </div>

        {/* 快捷键列表 */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', overflowY: 'auto' }}>
          {shortcuts.map((shortcut, idx) => (
            <div
              key={idx}
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '6px 0',
                borderBottom: idx < shortcuts.length - 1
                  ? (isDark ? '0.5px solid rgba(255,255,255,0.06)' : '0.5px solid rgba(0,0,0,0.06)')
                  : 'none',
              }}
            >
              <span style={{ fontSize: '13px', color: isDark ? '#A1A1A6' : '#636366' }}>
                {shortcut.description}
              </span>
              <div style={{ display: 'flex', gap: '4px' }}>
                {shortcut.keys.map((key, keyIdx) => (
                  <kbd
                    key={keyIdx}
                    style={{
                      padding: '3px 8px',
                      borderRadius: '6px',
                      fontSize: '11px',
                      fontFamily: 'monospace',
                      fontWeight: 500,
                      background: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.04)',
                      color: isDark ? '#F5F5F7' : '#1D1D1F',
                      border: isDark ? '0.5px solid rgba(255,255,255,0.1)' : '0.5px solid rgba(0,0,0,0.1)',
                    }}
                  >
                    {key}
                  </kbd>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>,
    document.body
  ) : null;

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="p-2 rounded-lg transition-colors"
        style={{ color: '#6E6E73', background: 'transparent' }}
        onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(0,0,0,0.03)'; e.currentTarget.style.color = '#1D1D1F'; }}
        onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = '#6E6E73'; }}
        title="快捷键"
      >
        <Keyboard className="w-5 h-5" />
      </button>
      {modal}
    </>
  );
};
