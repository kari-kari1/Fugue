import React, { useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { cn, formatNumber, getAgentIcon } from '../../lib/utils';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { templatesApi } from '../../api/templates';
import type { Template, AgentConfig, TaskConfig } from '../../api/templates';

interface TemplateDetailModalProps {
  template: Template | null;
  open: boolean;
  onClose: () => void;
}

const difficultyConfig: Record<string, { label: string; variant: 'success' | 'warning' | 'error' }> = {
  beginner: { label: '入门', variant: 'success' },
  intermediate: { label: '进阶', variant: 'warning' },
  advanced: { label: '高级', variant: 'error' },
};

const processTypeLabels: Record<string, string> = {
  sequential: '顺序执行',
  hierarchical: '层级执行',
};

const AgentNodePreview: React.FC<{ agent: AgentConfig }> = ({ agent }) => (
  <div className="flex items-center gap-2 bg-white/[0.03] radius-md p-2 border border-[var(--border-subtle)]">
    <div className="w-8 h-8 flex items-center justify-center radius-sm bg-white/[0.05]">
      {getAgentIcon(agent.role || '')}
    </div>
    <div className="min-w-0">
      <p className="font-medium truncate text-primary text-[var(--text-sm)]">{agent.name}</p>
      <p className="text-[var(--text-xs)] text-tertiary truncate">{agent.role}</p>
    </div>
  </div>
);

const TaskNodePreview: React.FC<{ task: TaskConfig; index: number }> = ({ task, index }) => (
  <div className="flex items-start gap-2 bg-white/[0.03] radius-md p-2 border border-[var(--border-subtle)]">
    <span className="text-tertiary text-[var(--text-xs)] font-mono mt-0.5">T{index + 1}</span>
    <div className="min-w-0">
      <p className="font-medium truncate text-primary text-[var(--text-sm)]">{task.name}</p>
      {task.depends_on.length > 0 && (
        <p className="text-[var(--text-xs)] text-tertiary">
          依赖: {task.depends_on.map((d) => `T${d + 1}`).join(', ')}
        </p>
      )}
    </div>
  </div>
);

export const TemplateDetailModal: React.FC<TemplateDetailModalProps> = ({
  template,
  open,
  onClose,
}) => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = React.useState(false);

  const handleUse = async () => {
    if (!template) return;
    setIsLoading(true);
    try {
      const result = await templatesApi.use(template.id);
      onClose();
      navigate(`/crew/${result.crew_id}`);
    } catch (err) {
      console.error('使用模板失败:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    },
    [onClose],
  );

  useEffect(() => {
    if (open) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [open, handleKeyDown]);

  if (!open || !template) return null;

  const difficulty = difficultyConfig[template.difficulty] ?? {
    label: template.difficulty,
    variant: 'secondary' as const,
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-label={template.name}>
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      <div
        className={cn(
          'relative w-full max-w-2xl max-h-[85vh] overflow-y-auto',
          'glass radius-xl shadow-2xl',
          'animate-scale-in'
        )}
      >
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 radius-md hover:bg-white/[0.06] transition-colors text-tertiary hover:text-primary"
          aria-label="关闭"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        </button>

        <div className="p-6 space-y-5">
          <div className="flex items-start gap-4 pr-8">
            <span className="text-4xl" role="img" aria-label={template.name}>{template.icon}</span>
            <div className="flex-1 min-w-0">
              <h2 className="text-[var(--text-xl)] font-bold text-primary">{template.name}</h2>
              <p className="text-secondary mt-1">{template.description ?? '暂无描述'}</p>
              <div className="flex flex-wrap items-center gap-2 mt-3">
                <Badge variant={difficulty.variant}>{difficulty.label}</Badge>
                <span className="text-[var(--text-sm)] text-secondary">
                  {processTypeLabels[template.process_type] ?? template.process_type}
                </span>
                <span className="text-[var(--text-sm)] text-secondary">
                  使用 {formatNumber(template.use_count)} 次
                </span>
                <span className="text-[var(--text-sm)] text-secondary">
                  评分 {template.rating.toFixed(1)}
                </span>
              </div>
            </div>
          </div>

          {template.tags.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {template.tags.map((tag) => <Badge key={tag} variant="outline">{tag}</Badge>)}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h3 className="text-[var(--text-sm)] font-semibold mb-2 text-primary">
                Agents ({template.agents_config.length})
              </h3>
              <div className="space-y-2">
                {template.agents_config.map((agent, i) => <AgentNodePreview key={i} agent={agent} />)}
                {template.agents_config.length === 0 && <p className="text-[var(--text-sm)] text-tertiary">无</p>}
              </div>
            </div>
            <div>
              <h3 className="text-[var(--text-sm)] font-semibold mb-2 text-primary">
                Tasks ({template.tasks_config.length})
              </h3>
              <div className="space-y-2">
                {template.tasks_config.map((task, i) => <TaskNodePreview key={i} task={task} index={i} />)}
                {template.tasks_config.length === 0 && <p className="text-[var(--text-sm)] text-tertiary">无</p>}
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-2 border-t border-[var(--border-subtle)]">
            <Button variant="outline" onClick={onClose}>取消</Button>
            <Button variant="primary" isLoading={isLoading} onClick={handleUse}>使用此模板</Button>
          </div>
        </div>
      </div>
    </div>
  );
};
