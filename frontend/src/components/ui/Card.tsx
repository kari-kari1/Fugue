/* Apple-style Card */

import React from 'react';
import { cn } from '../../lib/utils';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'glass' | 'elevated';
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  variant = 'default',
  ...props
}) => {
  const variantClasses = {
    default: 'bg-card border border-divider radius-lg shadow-sm-var',
    glass: 'bg-card/70 backdrop-blur-xl border border-white/60 radius-lg shadow-md-var',
    elevated: 'bg-card border border-divider radius-lg shadow-md-var',
  };

  return (
    <div className={cn(variantClasses[variant], 'transition-all duration-200', className)} {...props}>
      {children}
    </div>
  );
};

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ children, className = '', ...props }) => (
  <div className={cn('px-5 py-4 border-b border-divider', className)} {...props}>
    {children}
  </div>
);

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({ children, className = '', ...props }) => (
  <h3 className={cn('text-15 font-semibold text-primary tracking-[-0.01em]', className)} {...props}>
    {children}
  </h3>
);

export const CardDescription: React.FC<React.HTMLAttributes<HTMLParagraphElement>> = ({ children, className = '', ...props }) => (
  <p className={cn('text-13 text-secondary mt-1', className)} {...props}>
    {children}
  </p>
);

export const CardContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ children, className = '', ...props }) => (
  <div className={cn('p-5', className)} {...props}>
    {children}
  </div>
);

export const CardFooter: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ children, className = '', ...props }) => (
  <div className={cn('px-5 py-4 border-t border-divider flex items-center gap-3', className)} {...props}>
    {children}
  </div>
);

export default Card;
