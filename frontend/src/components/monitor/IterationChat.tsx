import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { Iteration } from '../../types/iteration';
import { IterationMessage } from './IterationMessage';
import { RefineControls } from './RefineControls';

interface IterationChatProps {
  executionId: string;
  iterations: Iteration[];
  onRefine: (feedback: string, mode: 'reexecute' | 'incremental') => void;
  isRefining: boolean;
  executionStatus: string;
}

export const IterationChat: React.FC<IterationChatProps> = ({
  executionId: _executionId,
  iterations,
  onRefine,
  isRefining,
  executionStatus,
}) => {
  const [feedback, setFeedback] = useState('');
  const [mode, setMode] = useState<'reexecute' | 'incremental'>('incremental');

  const handleSubmit = () => {
    if (feedback.trim() && !isRefining) {
      onRefine(feedback, mode);
      setFeedback('');
    }
  };

  const isRunning = executionStatus === 'running' || executionStatus === 'pending';
  const sortedIterations = [...iterations].sort(
    (a, b) => a.iteration_number - b.iteration_number
  );
  const latestIteration = sortedIterations[sortedIterations.length - 1];

  return (
    <div className="flex flex-col h-full bg-gray-900 border border-gray-700 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-gray-800/50 border-b border-gray-700">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-semibold text-white">迭代对话</h2>
          <span className="px-2.5 py-1 rounded-md text-xs font-medium bg-blue-600 text-white">
            {iterations.length} 次迭代
          </span>
        </div>
        {executionStatus && (
          <span className="text-xs text-gray-400">
            执行状态: {executionStatus}
          </span>
        )}
      </div>

      {/* Iteration list */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <AnimatePresence mode="popLayout">
          {sortedIterations.map((iteration) => (
            <motion.div
              key={iteration.id}
              layout
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.2 }}
            >
              <IterationMessage
                iteration={iteration}
                isLatest={iteration.id === latestIteration?.id}
              />
            </motion.div>
          ))}
        </AnimatePresence>

        {iterations.length === 0 && (
          <div className="text-center py-12">
            <svg
              className="w-16 h-16 mx-auto text-gray-600 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
            <p className="text-gray-500">暂无迭代历史</p>
            <p className="text-sm text-gray-600 mt-1">提交反馈开始优化</p>
          </div>
        )}
      </div>

      {/* Refine controls — 执行完成后显示输入框，执行中隐藏 */}
      {!isRunning && (
        <div className="p-4 border-t border-gray-700">
          <RefineControls
            feedback={feedback}
            onFeedbackChange={setFeedback}
            mode={mode}
            onModeChange={setMode}
            onSubmit={handleSubmit}
            isDisabled={false}
            isRefining={isRefining}
          />
        </div>
      )}
    </div>
  );
};
