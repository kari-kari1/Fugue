import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { cn, formatNumber } from '../../lib/utils';
import { templatesApi } from '../../api/templates';
import type { Template } from '../../api/templates';

interface TemplateCardProps {
  template: Template;
  onClick?: (template: Template) => void;
}

const difficultyConfig: Record<string, { label: string; variant: 'success' | 'warning' | 'error' }> = {
  beginner: { label: '入门', variant: 'success' },
  intermediate: { label: '进阶', variant: 'warning' },
  advanced: { label: '高级', variant: 'error' },
};

export const TemplateCard: React.FC<TemplateCardProps> = ({ template, onClick }) => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const difficulty = difficultyConfig[template.difficulty] ?? { label: template.difficulty, variant: 'secondary' as const };
  const displayTags = template.tags.slice(0, 3);

  const handleUse = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsLoading(true);
    try {
      const result = await templatesApi.use(template.id);
      navigate(`/crew/${result.crew_id}`);
    } catch (err) {
      console.error('使用模板失败:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card
      className={cn(
        'group cursor-pointer transition-all hover:shadow-lg-var hover:border-[var(--accent-steel)]/30',
        'flex flex-col h-full'
      )}
      onClick={() => onClick?.(template)}
    >
      <div className="flex items-center gap-3 mb-3">
        <span className="text-3xl" role="img" aria-label={template.name}>
          {template.icon}
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="font-semibold text-[var(--text-base)] truncate text-primary">{template.name}</h3>
          <Badge variant={difficulty.variant} className="mt-1">
            {difficulty.label}
          </Badge>
        </div>
      </div>

      <p className="text-[var(--text-sm)] text-secondary line-clamp-2 mb-3 flex-1">
        {template.description ?? '暂无描述'}
      </p>

      {displayTags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {displayTags.map((tag) => (
            <Badge key={tag} variant="outline" className="text-[var(--text-xs)]">
              {tag}
            </Badge>
          ))}
          {template.tags.length > 3 && (
            <Badge variant="outline" className="text-[var(--text-xs)]">
              +{template.tags.length - 3}
            </Badge>
          )}
        </div>
      )}

      <div className="flex items-center justify-between pt-3 border-t border-[var(--border-subtle)]">
        <div className="flex items-center gap-3 text-[var(--text-xs)] text-secondary">
          <span title="使用次数">使用 {formatNumber(template.use_count)}</span>
          <span title="评分">评分 {template.rating.toFixed(1)}</span>
        </div>
        <Button variant="primary" size="sm" isLoading={isLoading} onClick={handleUse}>
          使用此模板
        </Button>
      </div>
    </Card>
  );
};
