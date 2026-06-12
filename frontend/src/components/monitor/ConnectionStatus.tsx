import React from 'react';

interface ConnectionStatusProps {
  isConnected: boolean;
  reconnectCount?: number;
  className?: string;
}

export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({
  isConnected,
  reconnectCount = 0,
  className = '',
}) => {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div
        className={`w-2 h-2 rounded-full transition-colors ${
          isConnected ? 'bg-green-500' : 'bg-red-500'
        }`}
      />
      <span className="text-sm text-gray-600">
        {isConnected ? '已连接' : '未连接'}
      </span>
      {reconnectCount > 0 && (
        <span className="text-xs text-gray-400">
          (重连 {reconnectCount} 次)
        </span>
      )}
    </div>
  );
};
