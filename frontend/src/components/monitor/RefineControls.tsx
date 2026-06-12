import React from 'react';

interface RefineControlsProps {
  feedback: string;
  onFeedbackChange: (value: string) => void;
  mode: 'reexecute' | 'incremental';
  onModeChange: (mode: 'reexecute' | 'incremental') => void;
  onSubmit: () => void;
  isDisabled: boolean;
  isRefining: boolean;
}

export const RefineControls: React.FC<RefineControlsProps> = ({
  feedback,
  onFeedbackChange,
  mode,
  onModeChange,
  onSubmit,
  isDisabled,
  isRefining,
}) => {
  const handleModeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onModeChange(e.target.value as 'reexecute' | 'incremental');
  };

  return (
    <div className="space-y-4">
      {/* Feedback input */}
      <div className="w-full">
        <label
          htmlFor="refine-feedback"
          className="block text-sm font-medium text-gray-300 mb-2"
        >
          反馈内容
        </label>
        <textarea
          id="refine-feedback"
          rows={4}
          value={feedback}
          onChange={(e) => onFeedbackChange(e.target.value)}
          disabled={isDisabled || isRefining}
          className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg
                     text-white placeholder-gray-400 focus:outline-none focus:ring-2
                     focus:ring-blue-500 focus:border-blue-500 transition-all
                     disabled:opacity-50 disabled:cursor-not-allowed resize-none"
          placeholder="输入你的反馈，指导下一步优化方向..."
        />
      </div>

      {/* Controls row */}
      <div className="flex items-center gap-3">
        {/* Mode selector */}
        <div className="flex-1">
          <select
            id="refine-mode"
            value={mode}
            onChange={handleModeChange}
            disabled={isDisabled || isRefining}
            className="w-full px-4 py-2.5 bg-gray-800 border border-gray-600 rounded-lg
                       text-white focus:outline-none focus:ring-2 focus:ring-blue-500
                       focus:border-blue-500 transition-all disabled:opacity-50
                       disabled:cursor-not-allowed"
          >
            <option value="incremental">增量优化</option>
            <option value="reexecute">重新执行</option>
          </select>
        </div>

        {/* Submit button */}
        <button
          onClick={onSubmit}
          disabled={isDisabled || isRefining}
          className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-medium
                     rounded-lg transition-all focus:outline-none focus:ring-2
                     focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900
                     disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {isRefining ? (
            <>
              <svg
                className="animate-spin h-4 w-4 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              <span>优化中...</span>
            </>
          ) : (
            <span>提交</span>
          )}
        </button>
      </div>
    </div>
  );
};
