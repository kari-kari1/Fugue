/**
 * 反馈按钮组件（报告第2章 UX优化）
 * 提供正/负反馈按钮、重新生成功能
 */
import { useState, useCallback } from 'react';
import { ThumbsUp, ThumbsDown, RefreshCw } from 'lucide-react';

interface FeedbackButtonsProps {
  onPositive: () => void;
  onNegative: () => void;
  onRegenerate: () => void;
  disabled?: boolean;
}

export function FeedbackButtons({ onPositive, onNegative, onRegenerate, disabled }: FeedbackButtonsProps) {
  const [feedback, setFeedback] = useState<'positive' | 'negative' | null>(null);
  const [regenerating, setRegenerating] = useState(false);

  const handlePositive = useCallback(() => {
    setFeedback('positive');
    onPositive();
  }, [onPositive]);

  const handleNegative = useCallback(() => {
    setFeedback('negative');
    onNegative();
  }, [onNegative]);

  const handleRegenerate = useCallback(() => {
    setRegenerating(true);
    onRegenerate();
    setTimeout(() => setRegenerating(false), 1000);
  }, [onRegenerate]);

  return (
    <div className="flex items-center gap-2" role="group" aria-label="反馈操作">
      <span className="text-xs text-gray-500 mr-1">此结果是否有帮助？</span>
      <button
        onClick={handlePositive}
        disabled={disabled || feedback === 'negative'}
        className={`p-1.5 rounded-md transition-all duration-200 ${
          feedback === 'positive'
            ? 'bg-green-100 text-green-600'
            : 'hover:bg-gray-100 text-gray-400 hover:text-green-500'
        }`}
        aria-label="有帮助"
        title="有帮助"
      >
        <ThumbsUp size={16} />
      </button>
      <button
        onClick={handleNegative}
        disabled={disabled || feedback === 'positive'}
        className={`p-1.5 rounded-md transition-all duration-200 ${
          feedback === 'negative'
            ? 'bg-red-100 text-red-600'
            : 'hover:bg-gray-100 text-gray-400 hover:text-red-500'
        }`}
        aria-label="无帮助"
        title="无帮助"
      >
        <ThumbsDown size={16} />
      </button>
      <div className="w-px h-5 bg-gray-200 mx-1" aria-hidden="true" />
      <button
        onClick={handleRegenerate}
        disabled={disabled || regenerating}
        className={`p-1.5 rounded-md transition-all duration-200 hover:bg-gray-100 text-gray-400 hover:text-blue-500 ${
          regenerating ? 'animate-spin' : ''
        }`}
        aria-label="重新生成"
        title="重新生成"
      >
        <RefreshCw size={16} />
      </button>
    </div>
  );
}
