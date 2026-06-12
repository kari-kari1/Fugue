import React from 'react';
import { motion } from 'framer-motion';
import { buttonTap, buttonHover, buttonTransition } from '../../lib/motion-variants';

interface SpringButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  children: React.ReactNode;
}

const variantStyles: Record<string, string> = {
  primary: 'bg-accent text-white hover:brightness-110',
  secondary: 'bg-white text-primary shadow-resting hover:shadow-raised border border-separator',
  ghost: 'bg-transparent text-secondary hover:text-primary hover:bg-gray-100',
  danger: 'bg-destructive text-white hover:brightness-110',
};

const sizeStyles: Record<string, string> = {
  sm: 'h-8 px-3 text-footnote',
  md: 'h-9 px-4 text-footnote',
  lg: 'h-11 px-6 text-body',
};

export const SpringButton: React.FC<SpringButtonProps> = ({
  variant = 'primary',
  size = 'md',
  loading = false,
  children,
  className = '',
  disabled,
  ...props
}) => (
  <motion.button
    whileTap={!disabled && !loading ? buttonTap : undefined}
    whileHover={!disabled && !loading ? buttonHover : undefined}
    transition={buttonTransition}
    className={`
      inline-flex items-center justify-center gap-2
      font-regular cursor-pointer select-none
      transition-colors duration-base
      disabled:opacity-40 disabled:cursor-not-allowed
      ${variantStyles[variant]}
      ${sizeStyles[size]}
      ${variant === 'primary' || variant === 'danger' ? 'rounded-pill' : 'rounded-sm'}
      ${className}
    `}
    disabled={disabled || loading}
    {...(props as object)}
  >
    {loading && (
      <motion.span
        animate={{ rotate: 360 }}
        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
        className="inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full"
      />
    )}
    {children}
  </motion.button>
);
