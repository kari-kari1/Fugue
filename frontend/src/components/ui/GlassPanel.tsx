/* Apple-style Glass Panel — 替代所有手动 inline glass 样式 */

import React from 'react';
import { cn } from '../../lib/utils';

interface GlassPanelProps extends React.HTMLAttributes<HTMLDivElement> {
  /** 毛玻璃材质层次 */
  material?: 'ultra-thin' | 'thin' | 'regular' | 'thick' | 'liquid';
  /** 圆角大小 */
  radius?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'pill';
  /** 是否添加描边阴影替代 border */
  stroke?: boolean;
}

const materialStyles = {
  'ultra-thin': 'bg-[var(--glass-ultra-thin)] backdrop-blur-[20px] backdrop-saturate-180',
  'thin':       'bg-[var(--glass-thin)] backdrop-blur-[20px] backdrop-saturate-180',
  'regular':    'bg-[var(--glass-regular)] backdrop-blur-[20px] backdrop-saturate-180',
  'thick':      'bg-[var(--glass-thick)] backdrop-blur-[20px] backdrop-saturate-180',
  'liquid':     'backdrop-blur-[40px] backdrop-saturate-[1.8]',
};

const radiusStyles = {
  sm:   'rounded-[var(--radius-sm)]',
  md:   'rounded-[var(--radius-md)]',
  lg:   'rounded-[var(--radius-lg)]',
  xl:   'rounded-[var(--radius-xl)]',
  '2xl':'rounded-[var(--radius-2xl)]',
  pill: 'rounded-[var(--radius-pill)]',
};

export const GlassPanel: React.FC<GlassPanelProps> = ({
  children,
  material = 'liquid',
  radius = 'xl',
  stroke = true,
  className = '',
  style,
  ...props
}) => {
  const baseStyle: React.CSSProperties = material === 'liquid' ? {
    background: 'var(--liquid-glass-bg)',
    backdropFilter: 'var(--liquid-glass-blur)',
    WebkitBackdropFilter: 'var(--liquid-glass-blur)',
    border: 'var(--liquid-glass-border)',
    boxShadow: 'var(--liquid-glass-shadow)',
    ...style,
  } : {
    boxShadow: stroke ? 'var(--shadow-resting), var(--shadow-stroke)' : 'var(--shadow-resting)',
    ...style,
  };

  return (
    <div
      className={cn(
        materialStyles[material],
        radiusStyles[radius],
        'transition-all duration-200',
        className,
      )}
      style={baseStyle}
      {...props}
    >
      {children}
    </div>
  );
};

export default GlassPanel;
