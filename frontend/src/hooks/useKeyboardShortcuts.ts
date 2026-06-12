/* 全局快捷键 Hook */

import { useEffect, useCallback } from 'react';

interface ShortcutHandlers {
  onSave?: () => void;
  onUndo?: () => void;
  onRedo?: () => void;
  onCopy?: () => void;
  onPaste?: () => void;
  onDelete?: () => void;
  onSelectAll?: () => void;
  onZoomIn?: () => void;
  onZoomOut?: () => void;
  onZoomFit?: () => void;
}

export function useKeyboardShortcuts(handlers: ShortcutHandlers) {
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      const target = event.target as HTMLElement;
      if (
        target instanceof HTMLInputElement ||
        target instanceof HTMLTextAreaElement ||
        target instanceof HTMLSelectElement ||
        target.isContentEditable
      ) {
        return;
      }

      const isCtrl = event.ctrlKey || event.metaKey;
      const isShift = event.shiftKey;

      // Ctrl+S - 保存
      if (isCtrl && event.key === 's') {
        event.preventDefault();
        handlers.onSave?.();
        return;
      }

      // Ctrl+Z - 撤销
      if (isCtrl && !isShift && event.key === 'z') {
        event.preventDefault();
        handlers.onUndo?.();
        return;
      }

      // Ctrl+Shift+Z 或 Ctrl+Y - 重做
      if ((isCtrl && isShift && event.key === 'z') || (isCtrl && event.key === 'y')) {
        event.preventDefault();
        handlers.onRedo?.();
        return;
      }

      // Ctrl+C - 复制
      if (isCtrl && event.key === 'c') {
        event.preventDefault();
        handlers.onCopy?.();
        return;
      }

      // Ctrl+V - 粘贴
      if (isCtrl && event.key === 'v') {
        event.preventDefault();
        handlers.onPaste?.();
        return;
      }

      // Delete/Backspace - 删除
      if (event.key === 'Delete' || event.key === 'Backspace') {
        event.preventDefault();
        handlers.onDelete?.();
        return;
      }

      // Ctrl+A - 全选
      if (isCtrl && event.key === 'a') {
        event.preventDefault();
        handlers.onSelectAll?.();
        return;
      }

      // Ctrl+= / Ctrl++ - 放大
      if (isCtrl && (event.key === '=' || event.key === '+')) {
        event.preventDefault();
        handlers.onZoomIn?.();
        return;
      }

      // Ctrl+- - 缩小
      if (isCtrl && event.key === '-') {
        event.preventDefault();
        handlers.onZoomOut?.();
        return;
      }

      // Ctrl+0 - 适应画布
      if (isCtrl && event.key === '0') {
        event.preventDefault();
        handlers.onZoomFit?.();
        return;
      }
    },
    [handlers]
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);
}
