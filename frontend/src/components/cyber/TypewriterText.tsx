/*
 * 打字机效果 — Agent 思考/输出实时显示
 * JetBrains Mono + cyan 光标闪烁 + CRT 扫描线 + 荧光
 */

import React, { useState, useEffect, useRef } from 'react';

interface TypewriterTextProps {
  text: string;
  speed?: number;
  className?: string;
  showScanlines?: boolean;
}

export const TypewriterText: React.FC<TypewriterTextProps> = ({
  text,
  speed = 30,
  className = '',
  showScanlines: _showScanlines = true,
}) => {
  const [displayed, setDisplayed] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setDisplayed('');
    let i = 0;
    const interval = setInterval(() => {
      if (i < text.length) {
        setDisplayed(text.slice(0, i + 1));
        i++;
      } else {
        clearInterval(interval);
      }
    }, speed);
    return () => clearInterval(interval);
  }, [text, speed]);

  // Auto-scroll to bottom
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [displayed]);

  return (
    <div
      ref={containerRef}
      className={className}
      style={{
        position: 'relative',
        fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Segoe UI', 'Helvetica Neue', system-ui, sans-serif",
        fontSize: 14,
        fontWeight: 500,
        color: '#E8E8ED',
        lineHeight: 1.8,
        padding: '16px 20px',
        background: 'rgba(20, 20, 24, 0.95)',
        borderRadius: 10,
        border: '0.5px solid rgba(255, 255, 255, 0.08)',
        maxHeight: 400,
        overflowY: 'auto',
        letterSpacing: '0.01em',
      }}
    >
      {/* 文字内容 + 闪烁光标 */}
      <span style={{ position: 'relative', zIndex: 1 }}>
        {displayed}
        <span
          style={{
            display: 'inline-block',
            width: 2,
            height: 16,
            background: '#A0A0A5',
            marginLeft: 1,
            verticalAlign: 'text-bottom',
            animation: 'blink-caret 0.8s step-end infinite',
          }}
        />
      </span>

      <style>{`
        @keyframes blink-caret {
          from, to { opacity: 0; }
          50% { opacity: 1; }
        }
      `}</style>
    </div>
  );
};
