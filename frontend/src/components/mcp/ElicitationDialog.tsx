/* MCP Elicitation 弹窗 — 监听 SSE 事件，弹出确认/输入/选择对话框 */
import React, { useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, AlertTriangle, CheckCircle } from 'lucide-react';

interface ElicitationRequest {
  id: string;
  type: 'elicitation';
  elicitation_type: 'confirm' | 'input' | 'selection';
  message: string;
  options?: string[];
  timestamp: string;
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

export const ElicitationListener: React.FC = () => {
  const [pending, setPending] = useState<ElicitationRequest | null>(null);
  const [inputValue, setInputValue] = useState('');
  const [selectedOption, setSelectedOption] = useState('');

  const dismiss = useCallback(() => setPending(null), []);

  useEffect(() => {
    const sseUrl = `${API_BASE}/mcp-server/sse`.replace('/api/v1', '/api/v1');
    let eventSource: EventSource | null = null;
    let retries = 0;

    const connect = () => {
      eventSource = new EventSource(sseUrl);
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'elicitation') {
            setPending(data as ElicitationRequest);
            setInputValue('');
            setSelectedOption(data.options?.[0] || '');
          }
        } catch { /* ignore non-JSON pings */ }
      };
      eventSource.onerror = () => {
        eventSource?.close();
        retries++;
        if (retries < 5) setTimeout(connect, 5000);
      };
    };
    connect();
    return () => eventSource?.close();
  }, []);

  if (!pending) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        style={{
          position: 'fixed', inset: 0, zIndex: 10000,
          background: 'rgba(0,0,0,0.4)', backdropFilter: 'blur(4px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}
        onClick={dismiss}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          onClick={(e) => e.stopPropagation()}
          style={{
            background: 'white', borderRadius: 16, padding: 24, minWidth: 360, maxWidth: 480,
            boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <AlertTriangle size={18} style={{ color: '#F59E0B' }} />
              <span style={{ fontSize: 14, fontWeight: 600, color: '#1D1D1F' }}>MCP 请求</span>
            </div>
            <button onClick={dismiss} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#86868B' }}>
              <X size={16} />
            </button>
          </div>

          <p style={{ fontSize: 13, color: '#1D1D1F', marginBottom: 20, lineHeight: 1.5 }}>
            {pending.message}
          </p>

          {pending.elicitation_type === 'input' && (
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="输入回复..."
              autoFocus
              style={{
                width: '100%', padding: '10px 12px', borderRadius: 8, border: '1px solid rgba(0,0,0,0.15)',
                fontSize: 13, color: '#1D1D1F', marginBottom: 16, boxSizing: 'border-box',
              }}
            />
          )}

          {pending.elicitation_type === 'selection' && pending.options && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 16 }}>
              {pending.options.map((opt) => (
                <label key={opt} style={{
                  display: 'flex', alignItems: 'center', gap: 8, padding: '8px 12px',
                  borderRadius: 8, border: `1.5px solid ${selectedOption === opt ? '#0071E3' : 'rgba(0,0,0,0.1)'}`,
                  cursor: 'pointer', fontSize: 13, color: '#1D1D1F',
                  background: selectedOption === opt ? 'rgba(0,113,227,0.05)' : 'transparent',
                }}>
                  <input type="radio" name="elicit" value={opt} checked={selectedOption === opt}
                    onChange={() => setSelectedOption(opt)} style={{ accentColor: '#0071E3' }} />
                  {opt}
                </label>
              ))}
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
            {pending.elicitation_type === 'confirm' && (
              <>
                <button onClick={dismiss} style={{
                  padding: '8px 20px', borderRadius: 8, border: '1px solid rgba(0,0,0,0.1)',
                  background: 'white', color: '#6E6E73', fontSize: 13, cursor: 'pointer',
                }}>取消</button>
                <button onClick={dismiss} style={{
                  padding: '8px 20px', borderRadius: 8, border: 'none',
                  background: '#0071E3', color: 'white', fontSize: 13, fontWeight: 600, cursor: 'pointer',
                  display: 'flex', alignItems: 'center', gap: 4,
                }}><CheckCircle size={14} /> 确认</button>
              </>
            )}
            {(pending.elicitation_type === 'input' || pending.elicitation_type === 'selection') && (
              <button onClick={dismiss} style={{
                padding: '8px 20px', borderRadius: 8, border: 'none',
                background: '#0071E3', color: 'white', fontSize: 13, fontWeight: 600, cursor: 'pointer',
              }}>提交</button>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};
