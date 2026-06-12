import React from 'react';
import { motion } from 'framer-motion';
import { staggerContainer, staggerItem } from '../../lib/motion-variants';

interface StaggerListProps {
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}

export const StaggerList: React.FC<StaggerListProps> = ({ children, className = '', style }) => (
  <motion.div
    variants={staggerContainer}
    initial="hidden"
    animate="visible"
    className={className}
    style={style}
  >
    {children}
  </motion.div>
);

interface StaggerItemProps {
  children: React.ReactNode;
  className?: string;
}

export const StaggerItem: React.FC<StaggerItemProps> = ({ children, className = '' }) => (
  <motion.div variants={staggerItem} className={className}>
    {children}
  </motion.div>
);
