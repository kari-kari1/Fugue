import React from 'react';
import { GripVertical, Sparkles, ArrowRight, GitFork, Split, Network, RefreshCw, Link2, Play, Radio, GitBranch } from 'lucide-react';
import { getAgentIcon, getTaskIcon, getConditionIcon, getLoopIcon, getReviewIcon } from '../../lib/utils';

interface DraggableNodeProps {
  type: string;
  label: string;
  description: string;
  icon: React.ReactNode;
  accentColor: 'primary' | 'success' | 'pink' | 'amber' | 'blue' | 'purple' | 'green';
}

const ACCENT_COLORS: Record<string, string> = {
  primary: 'var(--accent)',
  pink: 'var(--pink)',
  success: 'var(--success)',
  amber: '#F59E0B',
  blue: '#3B82F6',
  purple: '#8B5CF6',
  green: '#10B981',
};

const DraggableNode: React.FC<DraggableNodeProps> = ({ type, label, description, icon, accentColor }) => {
  const accentVar = ACCENT_COLORS[accentColor] || 'var(--accent)';

  const onMouseDown = (event: React.MouseEvent) => {
    event.preventDefault();

    // 创建拖拽预览元素（ghost）
    const ghost = document.createElement('div');
    ghost.textContent = label;
    const borderColor = ACCENT_COLORS[accentColor] || '#0071E3';
    ghost.style.cssText = `
      position: fixed;
      left: ${event.clientX - 40}px;
      top: ${event.clientY - 16}px;
      padding: 8px 16px;
      border-radius: 8px;
      background: white;
      color: #1D1D1F;
      font-size: 13px;
      font-weight: 500;
      box-shadow: 0 8px 24px rgba(0,0,0,0.18);
      border: 2px solid ${borderColor};
      pointer-events: none;
      z-index: 99999;
      opacity: 0.92;
      transition: none;
    `;
    document.body.appendChild(ghost);
    document.body.style.cursor = 'grabbing';

    // 存储拖拽状态
    (window as any).__dragState = {
      type,
      startX: event.clientX,
      startY: event.clientY,
      ghost,
    };

    const onMouseMove = (e: MouseEvent) => {
      ghost.style.left = `${e.clientX - 40}px`;
      ghost.style.top = `${e.clientY - 16}px`;
    };

    const onMouseUp = (e: MouseEvent) => {
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
      document.body.style.cursor = '';
      ghost.remove();
      (window as any).__dragState = null;

      // 检查是否在画布内释放
      const flowEl = document.querySelector('.react-flow');
      if (!flowEl) return;
      const rect = flowEl.getBoundingClientRect();
      if (e.clientX < rect.left || e.clientX > rect.right || e.clientY < rect.top || e.clientY > rect.bottom) return;

      // 通过自定义事件通知 Editor 创建节点
      window.dispatchEvent(new CustomEvent('toolbar-drop', {
        detail: { type, clientX: e.clientX, clientY: e.clientY },
      }));
    };

    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  };

  return (
    <div
      onMouseDown={onMouseDown}
      className="group relative flex items-center gap-3 px-3.5 py-3 cursor-grab active:cursor-grabbing active:scale-[0.98] transition-all duration-150 ease-[cubic-bezier(0.25,0.1,0.25,1)] hover:bg-[rgba(0,0,0,0.03)] select-none"
      style={{
        background: 'rgba(0,0,0,0.02)',
        border: '0.5px solid rgba(0,0,0,0.06)',
        borderRadius: 'var(--radius-md)',
      }}
    >
      <div className="absolute left-2.5 top-1/2 -translate-y-1/2 w-[3px] h-[3px] rounded-full"
        style={{ backgroundColor: accentVar }} />

      <div className="flex-shrink-0 ml-1.5" style={{ color: accentVar }}>
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-13 font-medium" style={{ color: 'var(--text-primary)' }}>{label}</div>
        <div className="text-xs mt-0.5" style={{ color: 'var(--text-secondary)' }}>{description}</div>
      </div>
      <GripVertical className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" style={{ color: 'var(--text-tertiary)' }} />
    </div>
  );
};

const NodeToolbar: React.FC = () => {
  return (
    <div
      className="w-60 flex flex-col h-full z-10 m-3"
      style={{
        background: 'rgba(255,255,255,0.70)',
        backdropFilter: 'blur(40px)',
        WebkitBackdropFilter: 'blur(40px)',
        border: '1px solid rgba(0,0,0,0.05)',
        borderRadius: 'var(--radius-xl)',
        boxShadow: 'var(--shadow-sm)',
      }}
    >
      <div className="px-4 py-4" style={{ borderBottom: '0.5px solid var(--separator)' }}>
        <div className="flex items-center gap-2 mb-0.5">
          <Sparkles className="w-4 h-4" style={{ color: 'var(--accent)' }} />
          <h3 className="font-semibold text-13" style={{ color: 'var(--text-primary)' }}>节点库</h3>
        </div>
        <p className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>拖拽节点到画布创建</p>
      </div>

      <div className="flex-1 px-3 py-4 space-y-4 overflow-y-auto">
        <div>
          <h4 className="text-11 font-semibold uppercase tracking-wider mb-2.5 px-1"
            style={{ color: '#86868B', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase' as const }}>
            智能体
          </h4>
          <DraggableNode type="agent" label="Agent" description="AI执行单元" icon={getAgentIcon('default')} accentColor="primary" />
        </div>

        <div>
          <h4 className="text-11 font-semibold uppercase tracking-wider mb-2.5 px-1"
            style={{ color: '#86868B', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase' as const }}>
            任务
          </h4>
          <DraggableNode type="task" label="Task" description="具体执行任务" icon={getTaskIcon()} accentColor="success" />
        </div>

        <div>
          <h4 className="text-11 font-semibold uppercase tracking-wider mb-2.5 px-1"
            style={{ color: '#86868B', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase' as const }}>
            流程控制
          </h4>
          <DraggableNode type="condition" label="Condition" description="条件分支判断" icon={getConditionIcon()} accentColor="primary" />
          <div className="mt-1.5">
            <DraggableNode type="loop" label="Loop" description="循环迭代执行" icon={getLoopIcon()} accentColor="primary" />
          </div>
          <div className="mt-1.5">
            <DraggableNode type="humanReview" label="Human Review" description="人工审核暂停" icon={getReviewIcon()} accentColor="pink" />
          </div>
        </div>

        <div>
          <h4 className="text-11 font-semibold uppercase tracking-wider mb-2.5 px-1"
            style={{ color: '#86868B', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase' as const }}>
            工作流模式
          </h4>
          <DraggableNode type="prompt_chain" label="Prompt Chain" description="串行链式执行" icon={<Link2 size={15} />} accentColor="pink" />
          <div className="mt-1.5">
            <DraggableNode type="router" label="Router" description="条件路由分支" icon={<GitFork size={15} />} accentColor="amber" />
          </div>
          <div className="mt-1.5">
            <DraggableNode type="parallel_flow" label="Parallel" description="并行分段/投票" icon={<Split size={15} />} accentColor="blue" />
          </div>
          <div className="mt-1.5">
            <DraggableNode type="orchestrator" label="Orchestrator" description="编排者-工人模式" icon={<Network size={15} />} accentColor="purple" />
          </div>
          <div className="mt-1.5">
            <DraggableNode type="evaluator" label="Evaluator" description="评估-优化循环" icon={<RefreshCw size={15} />} accentColor="green" />
          </div>
        </div>

        <div>
          <h4 className="text-11 font-semibold uppercase tracking-wider mb-2.5 px-1"
            style={{ color: '#86868B', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase' as const }}>
            事件流
          </h4>
          <DraggableNode type="start" label="@start" description="启动事件触发" icon={<Play size={15} />} accentColor="blue" />
          <div className="mt-1.5">
            <DraggableNode type="listen" label="@listen" description="监听事件响应" icon={<Radio size={15} />} accentColor="purple" />
          </div>
          <div className="mt-1.5">
            <DraggableNode type="router_event" label="@router" description="条件事件路由" icon={<GitBranch size={15} />} accentColor="amber" />
          </div>
        </div>

        <div className="pt-2 px-1">
          <h4 className="text-11 font-semibold uppercase tracking-wider mb-3"
            style={{ color: '#86868B', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase' as const }}>
            快速上手
          </h4>
          <div className="space-y-2.5">
            {['拖拽节点到画布', '从底部Handle连线', '点击节点配置属性'].map((step, i) => (
              <div key={i} className="flex items-start gap-2.5 text-xs">
                <div
                  className="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 mt-px"
                  style={{
                    background: 'rgba(0,0,0,0.03)',
                    border: '0.5px solid rgba(0,0,0,0.06)',
                  }}
                >
                  <span className="text-11 font-semibold" style={{ color: 'var(--text-secondary)' }}>{i + 1}</span>
                </div>
                <span style={{ color: 'var(--text-secondary)' }}>{step}</span>
              </div>
            ))}
          </div>

          <div className="mt-5 pt-4" style={{ borderTop: '0.5px solid rgba(0,0,0,0.06)' }}>
            <h4 className="text-11 font-semibold uppercase tracking-[0.05em] mb-3"
              style={{ color: '#86868B', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase' as const }}>
              连线类型
            </h4>
            <div className="space-y-2.5">
              <div className="flex items-center gap-2 text-xs">
                <ArrowRight className="w-3.5 h-3.5 flex-shrink-0" style={{ color: '#0071E3' }} />
                <span style={{ color: 'var(--text-secondary)' }}>
                  <span className="font-medium" style={{ color: '#1D1D1F' }}>Agent → Task</span> 指定执行者
                </span>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <ArrowRight className="w-3.5 h-3.5 flex-shrink-0" style={{ color: '#34C759' }} />
                <span style={{ color: 'var(--text-secondary)' }}>
                  <span className="font-medium" style={{ color: '#1D1D1F' }}>Task → Task</span> 依赖顺序
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="px-4 py-3" style={{ borderTop: '0.5px solid rgba(0,0,0,0.06)' }}>
        <p className="text-11 text-center" style={{ color: 'var(--text-secondary)' }}>
          按 <kbd
            className="px-1.5 py-0.5 rounded text-11"
            style={{
              background: 'rgba(0,0,0,0.03)',
              color: '#6E6E73',
              border: '0.5px solid rgba(0,0,0,0.06)',
            }}
          >Del</kbd> 删除选中节点
        </p>
      </div>
    </div>
  );
};

export default NodeToolbar;
