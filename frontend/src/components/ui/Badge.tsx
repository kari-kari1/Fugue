import React from 'react';
import { cn } from '../../lib/utils';

interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'secondary' | 'outline' | 'success' | 'warning' | 'error' | 'cyan' | 'violet';
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  className,
  ...props
}) => {
  const variants = {
    default: 'bg-secondary text-secondary border-divider',
    secondary: 'bg-card text-primary border-divider',
    outline: 'border border-divider text-primary bg-transparent',
    success: 'bg-accent-green-dim text-accent-green border-green-15',
    warning: 'bg-accent-amber-dim text-accent-amber border-amber-15',
    error: 'bg-accent-red-dim text-accent-red border-red-dim',
    cyan: 'bg-accent-cyan-dim text-accent-cyan border-cyan-15',
    violet: 'bg-accent-secondary-dim text-accent-secondary border-purple-15',
  };

  return (
    <div className={cn('inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors', variants[variant], className)} {...props}>
      {children}
    </div>
  );
};

export default Badge;
