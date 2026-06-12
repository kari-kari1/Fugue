import React from 'react';
import { AlertCircle, AlertTriangle, CheckCircle, X } from 'lucide-react';
import type { DAGValidationError } from '../../stores/flowStore';

interface DAGValidationPanelProps {
  errors: DAGValidationError[];
  warnings: DAGValidationError[];
  onNodeClick?: (nodeId: string) => void;
  onEdgeClick?: (edgeId: string) => void;
  onClose?: () => void;
}

export const DAGValidationPanel: React.FC<DAGValidationPanelProps> = ({
  errors,
  warnings,
  onNodeClick,
  onEdgeClick: _onEdgeClick,
  onClose,
}) => {
  if (errors.length === 0 && warnings.length === 0) {
    return (
      <div className="flex items-center gap-2 px-4 py-2 rounded-lg" style={{
        background: 'rgba(255, 255, 255, 0.45)',
        backdropFilter: 'blur(40px) saturate(1.8)',
        WebkitBackdropFilter: 'blur(40px) saturate(1.8)',
        border: '0.5px solid rgba(255, 255, 255, 0.6)',
        boxShadow: '0 2px 20px rgba(0,0,0,0.04), inset 0 1px 0 rgba(255,255,255,0.8)',
        color: '#34C759',
      }}>
        <CheckCircle className="w-4 h-4" />
        <span className="text-sm font-medium">DAG 校验通过</span>
      </div>
    );
  }

  return (
    <div className="rounded-lg max-w-sm" style={{
      background: 'rgba(255, 255, 255, 0.45)',
      backdropFilter: 'blur(40px) saturate(1.8)',
      WebkitBackdropFilter: 'blur(40px) saturate(1.8)',
      border: '0.5px solid rgba(255, 255, 255, 0.6)',
      boxShadow: '0 2px 20px rgba(0,0,0,0.04), inset 0 1px 0 rgba(255,255,255,0.8)',
    }}>
      <div className="flex items-center justify-between px-4 py-2" style={{ borderBottom: '0.5px solid rgba(0,0,0,0.06)' }}>
        <h4 className="font-medium" style={{ color: '#1D1D1F' }}>DAG 校验结果</h4>
        {onClose && (
          <button onClick={onClose} className="p-1 rounded" style={{ color: '#6E6E73' }}>
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      <div className="p-4 space-y-3 max-h-60 overflow-y-auto">
        {/* 错误 */}
        {errors.map((error, idx) => (
          <div
            key={`error-${idx}`}
            className="flex gap-2 p-3 rounded-lg cursor-pointer transition-colors"
            style={{ background: 'rgba(255,59,48,0.06)' }}
            onClick={() => {
              if (error.nodeIds?.[0]) onNodeClick?.(error.nodeIds[0]);
            }}
          >
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: '#FF453A' }} />
            <div>
              <div className="text-sm font-medium" style={{ color: '#FF453A' }}>{error.message}</div>
              {error.nodeIds && error.nodeIds.length > 0 && (
                <div className="text-xs mt-1" style={{ color: 'rgba(255,69,58,0.7)' }}>
                  涉及 {error.nodeIds.length} 个节点
                </div>
              )}
            </div>
          </div>
        ))}

        {/* 警告 */}
        {warnings.map((warning, idx) => (
          <div
            key={`warning-${idx}`}
            className="flex gap-2 p-3 rounded-lg cursor-pointer transition-colors"
            style={{ background: 'rgba(255,149,0,0.06)' }}
            onClick={() => {
              if (warning.nodeIds?.[0]) onNodeClick?.(warning.nodeIds[0]);
            }}
          >
            <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: '#FF9F0A' }} />
            <div>
              <div className="text-sm font-medium" style={{ color: '#FF9F0A' }}>{warning.message}</div>
              {warning.nodeIds && warning.nodeIds.length > 0 && (
                <div className="text-xs mt-1" style={{ color: 'rgba(255,159,10,0.7)' }}>
                  涉及 {warning.nodeIds.length} 个节点
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
