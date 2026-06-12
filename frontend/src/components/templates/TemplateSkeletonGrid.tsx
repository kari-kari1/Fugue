/* 模板骨架屏网格 - Apple Design System */

import React from 'react';
import { Skeleton } from '../ui/Skeleton';
import { Card } from '../ui/Card';

interface TemplateSkeletonGridProps {
  count?: number;
}

const SkeletonCard: React.FC = () => (
  <Card className="flex flex-col h-full">
    {/* 头部：图标 + 名称 */}
    <div className="flex items-center gap-3 mb-3">
      <Skeleton className="h-10 w-10 rounded-full" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-4 w-2/3" />
        <Skeleton className="h-3 w-12 rounded-full" />
      </div>
    </div>

    {/* 描述 */}
    <div className="space-y-2 mb-3 flex-1">
      <Skeleton className="h-3 w-full" />
      <Skeleton className="h-3 w-4/5" />
    </div>

    {/* 标签 */}
    <div className="flex gap-1 mb-3">
      <Skeleton className="h-5 w-14 rounded-full" />
      <Skeleton className="h-5 w-16 rounded-full" />
      <Skeleton className="h-5 w-12 rounded-full" />
    </div>

    {/* 底部 */}
    <div className="flex items-center justify-between pt-3 border-t border-[var(--border-subtle)]">
      <Skeleton className="h-3 w-20" />
      <Skeleton className="h-8 w-20 radius-md" />
    </div>
  </Card>
);

export const TemplateSkeletonGrid: React.FC<TemplateSkeletonGridProps> = ({
  count = 6,
}) => (
  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
    {Array.from({ length: count }).map((_, i) => (
      <SkeletonCard key={i} />
    ))}
  </div>
);
