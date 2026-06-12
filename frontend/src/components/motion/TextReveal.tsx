import React from 'react';
import { motion } from 'framer-motion';
import { textRevealVariants, springReveal } from '../../lib/motion-variants';

interface TextRevealProps {
  children: React.ReactNode;
  as?: 'h1' | 'h2' | 'h3' | 'p' | 'span' | 'div';
  className?: string;
  style?: React.CSSProperties;
  delay?: number;
}

export const TextReveal: React.FC<TextRevealProps> = ({
  children,
  as = 'h1',
  className = '',
  style,
  delay = 0,
}) => {
  const Component = motion.create(as);

  return (
    <Component
      variants={textRevealVariants}
      initial="hidden"
      animate="visible"
      transition={{ ...springReveal, delay }}
      className={className}
      style={{ display: 'block', overflow: 'hidden', ...style }}
    >
      {children}
    </Component>
  );
};
