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

const MotionComponents = {
  h1: motion.h1,
  h2: motion.h2,
  h3: motion.h3,
  p: motion.p,
  span: motion.span,
  div: motion.div,
} as const;

export const TextReveal: React.FC<TextRevealProps> = ({
  children,
  as = 'h1',
  className = '',
  style,
  delay = 0,
}) => {
  const Component = MotionComponents[as] || MotionComponents.h1;

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
