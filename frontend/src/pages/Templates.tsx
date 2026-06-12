/* 模板市场 - Apple Clean Style */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Search, Plus, BookOpen, LayoutTemplate, Star, Users, FileText, ShoppingCart, Code, Palette, Sparkles } from 'lucide-react';
import toast from 'react-hot-toast';

import { Button } from '../components/ui/Button';
import { Card, CardContent } from '../components/ui/Card';
import { Skeleton } from '../components/ui/Skeleton';
import { templatesApi, type Template } from '../api/templates';

const categories = [
  { id: 'all', label: '全部', icon: <LayoutTemplate className="w-4 h-4" /> },
  { id: 'content', label: '内容创作', icon: <FileText className="w-4 h-4" /> },
  { id: 'ecommerce', label: '电商运营', icon: <ShoppingCart className="w-4 h-4" /> },
  { id: 'development', label: '开发辅助', icon: <Code className="w-4 h-4" /> },
  { id: 'design', label: '设计创意', icon: <Palette className="w-4 h-4" /> },
  { id: 'general', label: '通用办公', icon: <Sparkles className="w-4 h-4" /> },
];

const Templates: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [activeCategory, setActiveCategory] = useState('all');

  const { data: templatesResponse, isLoading } = useQuery({
    queryKey: ['templates'],
    queryFn: () => templatesApi.list(),
  });

  const useTemplate = useMutation({
    mutationFn: (templateId: string) => templatesApi.use(templateId),
    onSuccess: (result) => {
      toast.success('模板导入成功');
      queryClient.invalidateQueries({ queryKey: ['crews'] });
      navigate(`/crew/${result.crew_id}`);
    },
    onError: () => toast.error('导入模板失败'),
  });

  const templates = templatesResponse?.items || [];
  const filtered = templates.filter((t) => {
    const matchSearch = !search || t.name.toLowerCase().includes(search.toLowerCase()) || t.description?.toLowerCase().includes(search.toLowerCase());
    const matchCategory = activeCategory === 'all' || t.category === activeCategory;
    return matchSearch && matchCategory;
  });

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg-page)' }}>
      <header style={{
        background: 'var(--bg-nav)',
        WebkitBackdropFilter: 'saturate(180%) blur(20px)',
        backdropFilter: 'saturate(180%) blur(20px)',
        borderBottom: '0.5px solid var(--separator)',
        padding: '0 var(--side-padding)',
      }}>
        <div className="max-w-[980px] mx-auto flex items-center gap-4" style={{ height: 'var(--nav-height)' }}>
          <Button variant="ghost" size="sm" onClick={() => navigate('/')}>
            <ArrowLeft className="w-4 h-4 mr-1" /> 返回
          </Button>
          <h1 className="text-21 font-semibold text-primary">模板市场</h1>
        </div>
      </header>

      <main className="max-w-[1200px] mx-auto px-8 py-8">
        {/* Search + Categories */}
        <div className="mb-8 space-y-4">
          <div className="relative max-w-lg">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-tertiary" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="搜索模板..."
              className="w-full pl-10 pr-4 py-3 radius-lg bg-secondary border border-divider text-sm text-primary placeholder:text-tertiary outline-none focus:border-apple-blue focus:ring-2 focus:ring-[var(--accent-primary-dim)] transition-all"
            />
          </div>

          <div className="flex gap-2 flex-wrap">
            {categories.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setActiveCategory(cat.id)}
                className={`flex items-center gap-1.5 px-4 py-2 rounded-full text-13 font-medium transition-all ${
                  activeCategory === cat.id
                    ? 'bg-[var(--accent-primary)] text-white'
                    : 'bg-secondary text-secondary border border-divider hover:bg-white'
                }`}
              >
                {cat.icon}
                {cat.label}
              </button>
            ))}
          </div>
        </div>

        {/* Loading */}
        {isLoading && (
          <div className="grid grid-cols-3 gap-5">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="bg-white border border-divider radius-lg p-5 space-y-3">
                <Skeleton className="h-5 w-3/4 bg-secondary" />
                <Skeleton className="h-4 w-full bg-secondary" />
                <Skeleton className="h-4 w-1/2 bg-secondary" />
                <div className="flex gap-2 pt-2">
                  <Skeleton className="h-8 w-20 rounded-full bg-secondary" />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Templates Grid */}
        {filtered && (
          <div className="grid grid-cols-3 gap-5">
            {filtered.map((template) => (
              <TemplateCard
                key={template.id}
                template={template}
                onUse={() => useTemplate.mutate(template.id)}
                isLoading={useTemplate.isPending}
              />
            ))}
          </div>
        )}

        {filtered && filtered.length === 0 && !isLoading && (
          <div className="flex flex-col items-center justify-center py-20">
            <BookOpen className="w-12 h-12 text-tertiary mb-4" />
            <p className="text-secondary text-sm">没有找到匹配的模板</p>
          </div>
        )}
      </main>
    </div>
  );
};

const TemplateCard: React.FC<{
  template: Template;
  onUse: () => void;
  isLoading: boolean;
}> = ({ template, onUse, isLoading }) => {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <Card
      className="transition-all duration-250 cursor-pointer"
      style={{
        boxShadow: isHovered ? '0 8px 24px rgba(0,0,0,0.08)' : '0 1px 3px rgba(0,0,0,0.04)',
        transform: isHovered ? 'translateY(-2px)' : undefined,
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-3 mb-3">
          <h3 className="text-15 font-semibold text-primary leading-snug">{template.name}</h3>
          {template.category && (
            <span className="shrink-0 px-2.5 py-0.5 rounded-full text-11 font-medium bg-secondary text-secondary border border-divider">
              {template.category}
            </span>
          )}
        </div>
        <p className="text-13 text-secondary leading-relaxed line-clamp-2 mb-4">{template.description}</p>

        <div className="flex items-center gap-4 text-xs text-tertiary mb-4">
          <span className="flex items-center gap-1"><Users className="w-3 h-3" /> {template.agents_config?.length || 0} Agents</span>
          <span className="flex items-center gap-1"><Star className="w-3 h-3" /> {template.tasks_config?.length || 0} Tasks</span>
        </div>

        <Button size="sm" className="w-full" onClick={onUse} disabled={isLoading}>
          <Plus className="w-3.5 h-3.5 mr-1.5" />
          {isLoading ? '导入中...' : '使用模板'}
        </Button>
      </CardContent>
    </Card>
  );
};

export default Templates;
