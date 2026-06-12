import React from 'react';
import { Button } from './Button';
import { Layers } from 'lucide-react';

interface EmptyStateProps {
  icon?: string;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  secondaryAction?: {
    label: string;
    onClick: () => void;
  };
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action,
  secondaryAction,
}) => {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      <div className="w-16 h-16 radius-lg bg-[var(--accent-steel-dim)] border border-[var(--accent-steel)]/15 flex items-center justify-center mb-6">
        {icon ? (
          <span className="text-2xl">{icon}</span>
        ) : (
          <Layers className="w-7 h-7 text-[var(--accent-steel)]" />
        )}
      </div>
      <h3 className="text-[var(--text-xl)] font-semibold text-primary mb-2">{title}</h3>
      <p className="text-secondary text-center max-w-md mb-8">{description}</p>
      <div className="flex gap-3">
        {action && (
          <Button variant="primary" onClick={action.onClick}>
            {action.label}
          </Button>
        )}
        {secondaryAction && (
          <Button variant="secondary" onClick={secondaryAction.onClick}>
            {secondaryAction.label}
          </Button>
        )}
      </div>
    </div>
  );
};
