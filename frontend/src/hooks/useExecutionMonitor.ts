import { useCallback, useState, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useWebSocket } from './useWebSocket';
import type { WebSocketMessage } from './useWebSocket';
import { useAuthStore } from '../stores/authStore';
import type { Iteration } from '../types/iteration';

export interface ExecutionEvent {
  type: string;
  timestamp: string;
  agentName: string;
  taskName: string;
  data: Record<string, any>;
}

export interface ExecutionProgress {
  completed: number;
  total: number;
  percentage: number;
}

export interface ExecutionCost {
  totalTokens: number;
  totalCost: string;
}

interface UseExecutionMonitorOptions {
  executionId: string;
  enabled?: boolean;
  isRunning?: boolean;
}

interface UseExecutionMonitorReturn {
  isConnected: boolean;
  events: ExecutionEvent[];
  progress: ExecutionProgress;
  cost: ExecutionCost;
  latestEvent: ExecutionEvent | null;
  iterations: Iteration[];
  clearEvents: () => void;
}

export function useExecutionMonitor(options: UseExecutionMonitorOptions): UseExecutionMonitorReturn {
  const { executionId, enabled = true, isRunning = true } = options;
  const { token } = useAuthStore();
  const queryClient = useQueryClient();

  const [events, setEvents] = useState<ExecutionEvent[]>([]);
  const [progress, setProgress] = useState<ExecutionProgress>({ completed: 0, total: 0, percentage: 0 });
  const [cost, setCost] = useState<ExecutionCost>({ totalTokens: 0, totalCost: '$0.00' });
  const [latestEvent, setLatestEvent] = useState<ExecutionEvent | null>(null);
  const [iterations, setIterations] = useState<Iteration[]>([]);

  // 用于去重的已处理事件ID集合
  const seenEventKeys = useRef<Set<string>>(new Set());

  const handleMessage = useCallback((message: WebSocketMessage) => {
    // 忽略心跳响应
    if (message.type === 'pong' || message.type === 'connection.established') {
      return;
    }

    // 处理历史事件初始化（重置去重集合）
    if (message.type === 'init' && Array.isArray(message.events)) {
      seenEventKeys.current.clear();
      const historicalEvents: ExecutionEvent[] = message.events.map((evt: any) => ({
        type: evt.type || '',
        timestamp: evt.timestamp || '',
        agentName: evt.agent_name || '',
        taskName: evt.task_name || '',
        data: evt.data || {},
      }));
      // 为历史事件生成去重key
      for (const evt of historicalEvents) {
        seenEventKeys.current.add(`${evt.type}|${evt.timestamp}|${evt.data?.content || ''}`);
      }
      if (historicalEvents.length > 0) {
        setEvents(historicalEvents);
        setLatestEvent(historicalEvents[historicalEvents.length - 1]);
      }
      return;
    }

    const msgData = message.data || {};
    const event: ExecutionEvent = {
      type: message.type,
      timestamp: message.timestamp || new Date().toISOString(),
      agentName: message.agent_name || '',
      taskName: message.task_name || '',
      data: msgData,
    };

    // 去重：相同 type + timestamp + content 的事件只处理一次
    const eventKey = `${event.type}|${event.timestamp}|${msgData.content || ''}`;
    if (seenEventKeys.current.has(eventKey)) {
      return; // 重复事件，跳过
    }
    seenEventKeys.current.add(eventKey);

    // 添加到事件列表
    setEvents((prev) => [...prev, event]);
    setLatestEvent(event);

    // 根据事件类型更新状态
    switch (message.type) {
      case 'system.progress':
        setProgress({
          completed: msgData.completed || 0,
          total: msgData.total || 0,
          percentage: msgData.progress || 0,
        });
        break;

      case 'system.cost_update':
        setCost({
          totalTokens: msgData.total_tokens || 0,
          totalCost: msgData.total_cost || '$0.00',
        });
        break;

      case 'crew.completed':
        setProgress((prev) => ({
          ...prev,
          completed: prev.total,
          percentage: 100,
        }));
        // crew.completed 也携带 token/cost 数据，作为兜底
        if (msgData.total_tokens != null || msgData.total_cost != null) {
          setCost({
            totalTokens: msgData.total_tokens || 0,
            totalCost: msgData.total_cost || '$0.00',
          });
        }
        break;

      case 'iteration.started':
        setIterations(prev => [...prev, {
          id: msgData.iteration_id,
          execution_id: executionId,
          iteration_number: msgData.iteration_number,
          status: 'running',
          feedback: '',
          mode: 'incremental',
          tokens_used: 0,
          cost_usd: 0,
          created_at: new Date().toISOString(),
        }]);
        break;

      case 'iteration.completed':
        // 刷新迭代列表
        queryClient.invalidateQueries({ queryKey: ['iterations', executionId] });
        break;
    }
  }, []);

  // D3: WebSocket URL 动态构建（支持环境变量配置或自动推导）
  const WS_BASE = import.meta.env.VITE_WS_URL ||
    `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`;
  const wsUrl = enabled && executionId && token
    ? `${WS_BASE}/api/v1/ws/executions/${executionId}?token=${token}`
    : '';

  const { isConnected } = useWebSocket({
    url: wsUrl,
    onMessage: handleMessage,
    enabled: enabled && !!executionId && !!token && isRunning,
    autoReconnect: isRunning,
    reconnectInterval: 3000,
    maxReconnectAttempts: isRunning ? 5 : 0,
  });

  const clearEvents = useCallback(() => {
    setEvents([]);
    setLatestEvent(null);
  }, []);

  return {
    isConnected,
    events,
    progress,
    cost,
    latestEvent,
    iterations,
    clearEvents,
  };
}
