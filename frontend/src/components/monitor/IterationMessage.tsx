import React from 'react';
import { motion } from 'framer-motion';
import type { Iteration } from '../../types/iteration';
import { parseUTC } from '../../lib/utils';

interface IterationMessageProps {
  iteration: Iteration;
  isLatest: boolean;
}

export const IterationMessage: React.FC<IterationMessageProps> = ({
  iteration,
  isLatest,
}) => {
  const formatTimestamp = (timestamp: string) => {
    const date = parseUTC(timestamp);
    return date.toLocaleString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const getModeLabel = (mode: Iteration['mode']) => {
    return mode === 'incremental' ? '增量优化' : '重新执行';
  };

  const getStatusColor = (status: Iteration['status']) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-500';
      case 'running':
        return 'bg-blue-500';
      case 'completed':
        return 'bg-green-500';
      case 'failed':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusLabel = (status: Iteration['status']) => {
    switch (status) {
      case 'pending':
        return '等待中';
      case 'running':
        return '运行中';
      case 'completed':
        return '已完成';
      case 'failed':
        return '失败';
      default:
        return '未知';
    }
  };

  const formatTokens = (tokens: number) => {
    if (tokens >= 1000) {
      return `${(tokens / 1000).toFixed(1)}k`;
    }
    return tokens.toString();
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -20, scale: 0.95 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className={`relative p-4 rounded-lg border transition-all duration-200 ${
        isLatest
          ? 'bg-gray-800 border-blue-500/50 shadow-lg shadow-blue-500/10'
          : 'bg-gray-800/50 border-gray-700 hover:border-gray-600'
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          {/* Iteration number badge */}
          <div
            className={`px-2.5 py-1 rounded-md text-xs font-semibold ${
              isLatest
                ? 'bg-blue-600 text-white'
                : 'bg-gray-700 text-gray-300'
            }`}
          >
            迭代 #{iteration.iteration_number}
          </div>

          {/* Mode label */}
          <span
            className={`px-2 py-0.5 rounded text-xs ${
              iteration.mode === 'incremental'
                ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                : 'bg-orange-500/20 text-orange-300 border border-orange-500/30'
            }`}
          >
            {getModeLabel(iteration.mode)}
          </span>

          {/* Status indicator */}
          <div className="flex items-center gap-1.5">
            <div
              className={`w-2 h-2 rounded-full ${getStatusColor(iteration.status)} ${
                iteration.status === 'running' ? 'animate-pulse' : ''
              }`}
            />
            <span className="text-xs text-gray-400">
              {getStatusLabel(iteration.status)}
            </span>
          </div>
        </div>

        {/* Timestamp */}
        <span className="text-xs text-gray-500">
          {formatTimestamp(iteration.created_at)}
        </span>
      </div>

      {/* Feedback content */}
      <div className="mb-3">
        <div className="text-sm font-medium text-gray-400 mb-1">反馈</div>
        <p className="text-sm text-gray-200 bg-gray-900/50 rounded p-3 whitespace-pre-wrap">
          {iteration.feedback || '(无反馈)'}
        </p>
      </div>

      {/* Refined output (if completed) */}
      {iteration.status === 'completed' && iteration.refined_output && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="mb-3"
        >
          <div className="text-sm font-medium text-gray-400 mb-1">优化结果</div>
          <div className="text-sm text-green-300 bg-green-900/20 rounded p-3 border border-green-500/20 whitespace-pre-wrap">
            {iteration.refined_output}
          </div>
        </motion.div>
      )}

      {/* Error message (if failed) */}
      {iteration.context_snapshot && Object.keys(iteration.context_snapshot).length > 0 && (
        <div className="mb-3">
          <details className="group">
            <summary className="text-sm font-medium text-gray-400 cursor-pointer hover:text-gray-300 flex items-center gap-1">
              <svg className="w-3 h-3 transition-transform group-open:rotate-90" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M6 4l8 6-8 6V4z" />
              </svg>
              执行上下文快照
            </summary>
            <div className="mt-2 text-xs text-gray-500 bg-gray-900/50 rounded p-3 border border-gray-700/30 max-h-40 overflow-y-auto">
              {Object.entries(iteration.context_snapshot).map(([key, value]) => (
                <div key={key} className="mb-1">
                  <span className="text-gray-400 font-mono">{key}:</span>{' '}
                  <span className="text-gray-300">{typeof value === 'string' ? value.slice(0, 200) : JSON.stringify(value).slice(0, 200)}</span>
                </div>
              ))}
            </div>
          </details>
        </div>
      )}

      {/* Error message (if failed) */}
      {iteration.status === 'failed' && iteration.error_message && (
        <div className="mb-3">
          <div className="text-sm font-medium text-gray-400 mb-1">错误</div>
          <p className="text-sm text-red-400 bg-red-900/20 rounded p-3 border border-red-500/20">
            {iteration.error_message}
          </p>
        </div>
      )}

      {/* Footer: Token usage, cost, and duration */}
      <div className="flex items-center justify-between text-xs text-gray-500 pt-3 border-t border-gray-700/50">
        <div className="flex items-center gap-4">
          {/* Token usage */}
          <div className="flex items-center gap-1.5">
            <svg
              className="w-3.5 h-3.5 text-purple-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"
              />
            </svg>
            <span className="text-purple-300">
              {formatTokens(iteration.tokens_used)} tokens
            </span>
          </div>

          {/* Cost */}
          <div className="flex items-center gap-1.5">
            <svg
              className="w-3.5 h-3.5 text-green-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span className="text-green-300">${iteration.cost_usd.toFixed(4)}</span>
          </div>
        </div>

        {/* Duration */}
        {iteration.completed_at && (
          <div className="flex items-center gap-1.5">
            <svg
              className="w-3.5 h-3.5 text-blue-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span className="text-blue-300">
              {(() => {
                const start = parseUTC(iteration.created_at);
                const end = parseUTC(iteration.completed_at);
                const durationMs = end.getTime() - start.getTime();
                const seconds = Math.floor(durationMs / 1000);
                if (seconds < 60) return `${seconds}s`;
                const minutes = Math.floor(seconds / 60);
                const remainingSeconds = seconds % 60;
                return `${minutes}m ${remainingSeconds}s`;
              })()}
            </span>
          </div>
        )}
      </div>
    </motion.div>
  );
};
