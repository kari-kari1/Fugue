# Fugue Week 5 设计文档

> **文档版本**：v1.0
> **创建日期**：2026-06-01
> **设计范围**：Week 5 - 模板系统 + 认证完善 + UI 打磨

---

## 一、设计概述

### 1.1 目标

Week 5 的核心目标是完善用户体验，包括：
1. **用户认证系统完善** - Token 自动刷新、弹窗提醒续期
2. **模板系统** - 预设5个高质量模板、模板市场页面
3. **UI 打磨** - Apple 风格设计、错误处理、加载状态、空状态引导
4. **响应式适配** - 移动端、平板、桌面端完整适配

### 1.2 技术约束

- 前端：React 19 + TypeScript + Vite + Tailwind CSS
- 状态管理：Zustand + TanStack Query
- 后端：FastAPI + SQLAlchemy + PostgreSQL
- 设计风格：Apple Human Interface Guidelines

---

## 二、用户认证系统完善

### 2.1 Token 刷新机制

#### 数据模型扩展

```typescript
// authStore 扩展
interface AuthState {
  user: User | null;
  token: string | null;
  tokenExpiresAt: number | null;  // Token 过期时间戳
  isAuthenticated: boolean;
  isLoading: boolean;

  // 新增方法
  refreshToken: () => Promise<void>;
  checkTokenExpiry: () => void;
  showRefreshModal: () => void;
}
```

#### 后端 API

```python
# POST /api/v1/auth/refresh
@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: CurrentUser):
    """刷新 Token"""
    access_token = create_access_token(
        data={"sub": str(current_user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }
```

#### 刷新流程

```
用户操作 → API 请求 → 响应拦截器检查 Token
                              │
                              ▼
                 ┌────────────────────────┐
                 │ Token 剩余时间 < 5分钟？│
                 └───────────┬────────────┘
                             │
           ┌─────────────────┼─────────────────┐
           ▼                                   ▼
    ┌──────────┐                        ┌──────────┐
    │ 否      │                        │ 是      │
    │ 继续请求 │                        │ 显示弹窗 │
    └──────────┘                        └────┬─────┘
                                             │
                               ┌─────────────┼─────────────┐
                               ▼                           ▼
                        ┌──────────┐                ┌──────────┐
                        │ 点击续期 │                │ 忽略     │
                        │ 获取新   │                │ 继续操作 │
                        │ Token    │                │          │
                        └──────────┘                └──────────┘
```

#### 续期弹窗组件

```tsx
const TokenRefreshModal: React.FC<{
  isOpen: boolean;
  onRefresh: () => void;
  onDismiss: () => void;
  remainingSeconds: number;
}> = ({ isOpen, onRefresh, onDismiss, remainingSeconds }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-2xl p-6 max-w-sm mx-4 shadow-xl">
        <div className="text-center">
          <div className="w-12 h-12 mx-auto mb-4 bg-yellow-100 rounded-full flex items-center justify-center">
            <Clock className="w-6 h-6 text-yellow-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            会话即将过期
          </h3>
          <p className="text-gray-600 mb-1">
            您的登录会话将在 <span className="font-bold text-yellow-600">{remainingSeconds}</span> 秒后过期
          </p>
          <p className="text-sm text-gray-500 mb-6">
            是否续期以继续使用？
          </p>
          <div className="flex gap-3">
            <button
              onClick={onDismiss}
              className="flex-1 px-4 py-2.5 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition-colors"
            >
              稍后提醒
            </button>
            <button
              onClick={onRefresh}
              className="flex-1 px-4 py-2.5 bg-blue-500 text-white rounded-xl hover:bg-blue-600 transition-colors"
            >
              立即续期
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
```

### 2.2 路由守卫增强

```tsx
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading, tokenExpiresAt } = useAuthStore();
  const [showRefreshModal, setShowRefreshModal] = useState(false);
  const [remainingSeconds, setRemainingSeconds] = useState(0);

  // 检查 Token 过期
  useEffect(() => {
    if (!tokenExpiresAt) return;

    const checkExpiry = () => {
      const now = Date.now();
      const remaining = Math.floor((tokenExpiresAt - now) / 1000);

      if (remaining <= 0) {
        // Token 已过期，跳转登录
        navigate('/login');
      } else if (remaining <= 300) {
        // 剩余5分钟，显示续期弹窗
        setRemainingSeconds(remaining);
        setShowRefreshModal(true);
      }
    };

    checkExpiry();
    const interval = setInterval(checkExpiry, 1000);

    return () => clearInterval(interval);
  }, [tokenExpiresAt]);

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <>
      {children}
      <TokenRefreshModal
        isOpen={showRefreshModal}
        onRefresh={handleRefresh}
        onDismiss={() => setShowRefreshModal(false)}
        remainingSeconds={remainingSeconds}
      />
    </>
  );
};
```

---

## 三、模板系统

### 3.1 数据模型

#### Template 模型

```python
# backend/app/models/template.py

from sqlalchemy import Column, String, Text, JSON, Integer, Boolean, DateTime
from sqlalchemy.sql import func
import uuid

class Template(Base):
    __tablename__ = "templates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, comment="模板名称")
    description = Column(Text, comment="模板描述")
    category = Column(String(50), comment="分类：research/code/analysis/document/literature")
    icon = Column(String(50), comment="图标标识")
    difficulty = Column(String(20), comment="难度：beginner/intermediate/advanced")

    # 模板配置（JSON格式）
    agents_config = Column(JSON, comment="Agent 配置列表")
    tasks_config = Column(JSON, comment="Task 配置列表")
    connections_config = Column(JSON, comment="连接关系")
    process_type = Column(String(20), default="sequential", comment="执行模式")

    # 元数据
    tags = Column(JSON, comment="标签列表")
    use_count = Column(Integer, default=0, comment="使用次数")
    rating = Column(Float, default=4.8, comment="评分（1-5）")
    is_builtin = Column(Boolean, default=True, comment="是否内置模板")
    user_id = Column(String(36), comment="创建者用户ID（用户自定义模板）")

    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
```

#### 预设5个模板

| ID | 名称 | 分类 | 图标 | 难度 | Agent 数量 | Task 数量 |
|----|------|------|------|------|-----------|-----------|
| 1 | 行业研究报告生成 | research | 📊 | intermediate | 2 | 3 |
| 2 | 代码审查助手 | code | 🔍 | beginner | 2 | 2 |
| 3 | 竞品分析报告 | analysis | 📈 | advanced | 3 | 4 |
| 4 | 产品需求文档 | document | 📄 | intermediate | 2 | 3 |
| 5 | 文献综述生成 | literature | 📚 | advanced | 2 | 3 |

#### 模板配置示例（行业研究报告）

```json
{
  "name": "行业研究报告生成",
  "description": "自动生成专业的行业研究报告，包含数据收集、分析和报告撰写三个阶段",
  "category": "research",
  "icon": "📊",
  "difficulty": "intermediate",
  "tags": ["研究报告", "行业分析", "数据收集"],
  "process_type": "sequential",
  "agents_config": [
    {
      "name": "行业研究员",
      "role": "资深行业研究员",
      "goal": "收集和分析目标行业的最新数据和趋势",
      "backstory": "你是一位在行业研究领域有10年经验的资深研究员，擅长数据收集和趋势分析。",
      "llm_provider": "openai",
      "llm_model": "gpt-4o",
      "tools": ["web_search", "file_read"]
    },
    {
      "name": "报告写手",
      "role": "专业技术内容写手",
      "goal": "基于研究结果撰写清晰、专业的行业研究报告",
      "backstory": "你是一位资深技术写手，擅长将复杂的数据和分析转化为通俗易懂的报告。",
      "llm_provider": "openai",
      "llm_model": "gpt-4o",
      "tools": ["file_write"]
    }
  ],
  "tasks_config": [
    {
      "name": "数据收集",
      "description": "收集目标行业的市场规模、增长趋势、主要玩家、技术发展方向等数据",
      "expected_output": "结构化的行业数据报告",
      "output_type": "text",
      "agent_index": 0
    },
    {
      "name": "数据分析",
      "description": "分析收集到的数据，提取关键洞察和趋势",
      "expected_output": "数据分析报告，包含关键指标和趋势图表",
      "output_type": "text",
      "agent_index": 0,
      "depends_on": [0]
    },
    {
      "name": "报告撰写",
      "description": "基于数据分析结果，撰写完整的行业研究报告",
      "expected_output": "一篇结构完整、数据详实的行业研究报告（2000-3000字）",
      "output_type": "text",
      "agent_index": 1,
      "depends_on": [1]
    }
  ]
}
```

### 3.2 API 设计

#### 模板 API 端点

```python
# backend/app/api/v1/templates.py

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

router = APIRouter()

@router.get("/", response_model=TemplateListResponse)
async def list_templates(
    category: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = Query("popular", regex="^(popular|newest|recommended)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: DatabaseSession = Depends(get_db)
):
    """获取模板列表"""
    query = db.query(Template)

    # 分类筛选
    if category:
        query = query.filter(Template.category == category)

    # 搜索
    if search:
        query = query.filter(
            Template.name.ilike(f"%{search}%") |
            Template.description.ilike(f"%{search}%")
        )

    # 排序
    if sort_by == "popular":
        query = query.order_by(Template.use_count.desc())
    elif sort_by == "newest":
        query = query.order_by(Template.created_at.desc())

    # 分页
    total = query.count()
    templates = query.offset((page - 1) * limit).limit(limit).all()

    return {
        "items": templates,
        "total": total,
        "page": page,
        "limit": limit
    }


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(template_id: str, db: DatabaseSession = Depends(get_db)):
    """获取模板详情"""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return template


@router.post("/{template_id}/use", response_model=CrewResponse)
async def use_template(
    template_id: str,
    current_user: CurrentUser,
    db: DatabaseSession = Depends(get_db)
):
    """使用模板创建工作流"""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    # 创建工作流
    crew = Crew(
        name=f"{template.name} (基于模板)",
        description=template.description,
        user_id=current_user.id,
        process=template.process_type,
    )
    db.add(crew)
    db.flush()

    # 创建 Agent
    agent_map = {}  # index -> agent_id
    for idx, agent_config in enumerate(template.agents_config):
        agent = Agent(
            crew_id=crew.id,
            name=agent_config["name"],
            role=agent_config["role"],
            goal=agent_config["goal"],
            backstory=agent_config["backstory"],
            llm_provider=agent_config.get("llm_provider", "openai"),
            llm_model=agent_config.get("llm_model", "gpt-4o"),
            tools_config=agent_config.get("tools", []),
        )
        db.add(agent)
        db.flush()
        agent_map[idx] = agent.id

    # 创建 Task
    task_map = {}  # index -> task_id
    for idx, task_config in enumerate(template.tasks_config):
        # 解析依赖
        context_task_ids = []
        if "depends_on" in task_config:
            for dep_idx in task_config["depends_on"]:
                if dep_idx in task_map:
                    context_task_ids.append(task_map[dep_idx])

        task = Task(
            crew_id=crew.id,
            agent_id=agent_map[task_config["agent_index"]],
            name=task_config["name"],
            description=task_config["description"],
            expected_output=task_config["expected_output"],
            output_type=task_config.get("output_type", "text"),
            context_task_ids=context_task_ids,
        )
        db.add(task)
        db.flush()
        task_map[idx] = task.id

    # 更新使用次数
    template.use_count += 1

    await db.commit()

    return crew


@router.post("/", response_model=TemplateResponse, status_code=201)
async def create_template(
    template_data: TemplateCreate,
    current_user: CurrentUser,
    db: DatabaseSession = Depends(get_db)
):
    """创建自定义模板"""
    template = Template(
        **template_data.dict(),
        user_id=current_user.id,
        is_builtin=False,
    )
    db.add(template)
    await db.commit()
    return template
```

### 3.3 前端页面

#### 模板市场页面

```tsx
// frontend/src/pages/Templates.tsx

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, Filter, Grid, List } from 'lucide-react';
import { templatesApi } from '../api/templates';
import { TemplateCard } from '../components/templates/TemplateCard';
import { TemplateDetailModal } from '../components/templates/TemplateDetailModal';

const CATEGORIES = [
  { id: 'all', label: '全部', icon: '🎯' },
  { id: 'research', label: '研究分析', icon: '📊' },
  { id: 'code', label: '代码开发', icon: '🔍' },
  { id: 'analysis', label: '数据分析', icon: '📈' },
  { id: 'document', label: '文档撰写', icon: '📄' },
  { id: 'literature', label: '文献研究', icon: '📚' },
];

const Templates: React.FC = () => {
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('all');
  const [sortBy, setSortBy] = useState('popular');
  const [selectedTemplate, setSelectedTemplate] = useState(null);

  const { data: templates, isLoading } = useQuery({
    queryKey: ['templates', category, search, sortBy],
    queryFn: () => templatesApi.list({
      category: category === 'all' ? undefined : category,
      search: search || undefined,
      sort_by: sortBy,
    }),
  });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部导航 */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-gray-900">模板市场</h1>
          <p className="text-gray-600 mt-1">选择一个模板快速开始</p>
        </div>
      </header>

      {/* 搜索和筛选 */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="flex flex-col md:flex-row gap-4">
          {/* 搜索框 */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="搜索模板..."
              className="w-full pl-10 pr-4 py-3 bg-white border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* 分类筛选 */}
          <div className="flex gap-2 overflow-x-auto pb-2">
            {CATEGORIES.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setCategory(cat.id)}
                className={`px-4 py-2 rounded-lg whitespace-nowrap transition-colors ${
                  category === cat.id
                    ? 'bg-blue-500 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-100'
                }`}
              >
                {cat.icon} {cat.label}
              </button>
            ))}
          </div>
        </div>

        {/* 排序选项 */}
        <div className="flex justify-end mt-4">
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm"
          >
            <option value="popular">最热门</option>
            <option value="newest">最新</option>
            <option value="recommended">推荐</option>
          </select>
        </div>

        {/* 模板网格 */}
        {isLoading ? (
          <TemplateSkeletonGrid />
        ) : templates?.items.length === 0 ? (
          <EmptyState
            icon="🔍"
            title="未找到匹配的模板"
            description="尝试使用其他关键词，或浏览所有模板"
            action={{ label: '清除搜索', onClick: () => setSearch('') }}
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mt-6">
            {templates?.items.map((template) => (
              <TemplateCard
                key={template.id}
                template={template}
                onClick={() => setSelectedTemplate(template)}
              />
            ))}
          </div>
        )}
      </div>

      {/* 模板详情弹窗 */}
      {selectedTemplate && (
        <TemplateDetailModal
          template={selectedTemplate}
          onClose={() => setSelectedTemplate(null)}
        />
      )}
    </div>
  );
};
```

#### 模板卡片组件

```tsx
// frontend/src/components/templates/TemplateCard.tsx

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Star, Users, ArrowRight } from 'lucide-react';
import { templatesApi } from '../../api/templates';
import toast from 'react-hot-toast';

interface TemplateCardProps {
  template: Template;
  onClick: () => void;
}

export const TemplateCard: React.FC<TemplateCardProps> = ({ template, onClick }) => {
  const navigate = useNavigate();

  const handleUseTemplate = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const crew = await templatesApi.use(template.id);
      toast.success('工作流创建成功');
      navigate(`/crew/${crew.id}`);
    } catch (error) {
      toast.error('创建失败');
    }
  };

  return (
    <div
      onClick={onClick}
      className="bg-white rounded-2xl shadow-md hover:shadow-lg transition-all duration-250 cursor-pointer overflow-hidden group"
    >
      {/* 卡片头部 */}
      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center text-2xl">
            {template.icon}
          </div>
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
            template.difficulty === 'beginner' ? 'bg-green-100 text-green-700' :
            template.difficulty === 'intermediate' ? 'bg-yellow-100 text-yellow-700' :
            'bg-red-100 text-red-700'
          }`}>
            {template.difficulty === 'beginner' ? '初级' :
             template.difficulty === 'intermediate' ? '中级' : '高级'}
          </span>
        </div>

        <h3 className="text-lg font-semibold text-gray-900 mb-2">{template.name}</h3>
        <p className="text-sm text-gray-600 line-clamp-2 mb-4">{template.description}</p>

        {/* 标签 */}
        <div className="flex flex-wrap gap-2 mb-4">
          {template.tags?.slice(0, 3).map((tag) => (
            <span key={tag} className="px-2 py-1 bg-gray-100 text-gray-600 rounded-md text-xs">
              {tag}
            </span>
          ))}
        </div>

        {/* 统计信息 */}
        <div className="flex items-center gap-4 text-sm text-gray-500">
          <span className="flex items-center gap-1">
            <Users className="w-4 h-4" />
            {template.use_count.toLocaleString()} 次使用
          </span>
          <span className="flex items-center gap-1">
            <Star className="w-4 h-4 text-yellow-500" />
            {template.rating || 4.8}
          </span>
        </div>
      </div>

      {/* 卡片底部 */}
      <div className="px-6 py-4 bg-gray-50 border-t border-gray-100">
        <button
          onClick={handleUseTemplate}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-500 text-white rounded-xl hover:bg-blue-600 transition-colors group-hover:bg-blue-600"
        >
          使用此模板
          <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
        </button>
      </div>
    </div>
  );
};
```

---

## 四、UI 打磨优化

### 4.1 Apple 风格设计系统

#### 设计变量

```css
/* frontend/src/styles/apple-design.css */

:root {
  /* 颜色系统 */
  --color-primary: #007AFF;
  --color-secondary: #5856D6;
  --color-success: #34C759;
  --color-warning: #FF9500;
  --color-danger: #FF3B30;

  /* 背景色 */
  --bg-primary: #FFFFFF;
  --bg-secondary: #F2F2F7;
  --bg-tertiary: #E5E5EA;

  /* 文字颜色 */
  --text-primary: #1C1C1E;
  --text-secondary: #8E8E93;
  --text-tertiary: #AEAEB2;

  /* 间距系统 */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;

  /* 圆角 */
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 20px;
  --radius-full: 9999px;

  /* 阴影 */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);

  /* 动画 */
  --transition-fast: 150ms ease;
  --transition-normal: 250ms ease;
  --transition-slow: 350ms ease;
}
```

#### 基础组件

```tsx
// frontend/src/components/ui/AppleButton.tsx

import React from 'react';
import { Loader2 } from 'lucide-react';

interface AppleButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export const AppleButton: React.FC<AppleButtonProps> = ({
  variant = 'primary',
  size = 'md',
  isLoading = false,
  children,
  className = '',
  disabled,
  ...props
}) => {
  const baseClasses = "inline-flex items-center justify-center font-medium rounded-xl transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2";

  const variantClasses = {
    primary: "bg-[#007AFF] text-white hover:bg-[#0056CC] shadow-md hover:shadow-lg focus:ring-blue-500",
    secondary: "bg-[#F2F2F7] text-[#1C1C1E] hover:bg-[#E5E5EA] focus:ring-gray-500",
    ghost: "bg-transparent text-[#007AFF] hover:bg-[#F2F2F7] focus:ring-blue-500",
    danger: "bg-[#FF3B30] text-white hover:bg-[#D63027] shadow-md hover:shadow-lg focus:ring-red-500",
  };

  const sizeClasses = {
    sm: "px-3 py-1.5 text-sm",
    md: "px-4 py-2.5 text-sm",
    lg: "px-6 py-3 text-base",
  };

  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className} ${
        disabled || isLoading ? 'opacity-50 cursor-not-allowed' : ''
      }`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
      {children}
    </button>
  );
};
```

```tsx
// frontend/src/components/ui/AppleCard.tsx

import React from 'react';

interface AppleCardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
}

export const AppleCard: React.FC<AppleCardProps> = ({
  children,
  className = '',
  hover = true,
}) => {
  return (
    <div className={`
      bg-white rounded-2xl shadow-md
      ${hover ? 'hover:shadow-lg transition-shadow duration-250' : ''}
      overflow-hidden ${className}
    `}>
      {children}
    </div>
  );
};

export const AppleCardHeader: React.FC<{
  children: React.ReactNode;
  className?: string;
}> = ({ children, className = '' }) => (
  <div className={`px-6 py-4 border-b border-gray-100 ${className}`}>
    {children}
  </div>
);

export const AppleCardContent: React.FC<{
  children: React.ReactNode;
  className?: string;
}> = ({ children, className = '' }) => (
  <div className={`px-6 py-4 ${className}`}>
    {children}
  </div>
);

export const AppleCardFooter: React.FC<{
  children: React.ReactNode;
  className?: string;
}> = ({ children, className = '' }) => (
  <div className={`px-6 py-4 bg-gray-50 border-t border-gray-100 ${className}`}>
    {children}
  </div>
);
```

### 4.2 错误处理优化

#### 全局错误边界

```tsx
// frontend/src/components/ErrorBoundary.tsx

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-[#F2F2F7]">
          <div className="bg-white rounded-2xl p-8 max-w-md mx-4 shadow-lg text-center">
            <div className="w-16 h-16 mx-auto mb-4 bg-red-100 rounded-full flex items-center justify-center">
              <AlertCircle className="w-8 h-8 text-red-500" />
            </div>
            <h2 className="text-xl font-semibold text-[#1C1C1E] mb-2">
              出现了一些问题
            </h2>
            <p className="text-[#8E8E93] mb-6">
              {this.state.error?.message || '请稍后重试'}
            </p>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="inline-flex items-center gap-2 px-6 py-3 bg-[#007AFF] text-white rounded-xl hover:bg-[#0056CC] transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              重试
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
```

#### API 错误拦截器

```typescript
// frontend/src/api/client.ts

import axios from 'axios';
import toast from 'react-hot-toast';

const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
});

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const { response, message } = error;

    if (!response) {
      // 网络错误
      toast.error('网络连接失败，请检查网络');
      return Promise.reject(error);
    }

    const { status, data } = response;

    switch (status) {
      case 401:
        // 认证错误 - 由 authStore 处理
        break;
      case 403:
        toast.error('没有权限执行此操作');
        break;
      case 404:
        toast.error('请求的资源不存在');
        break;
      case 422:
        // 验证错误
        const validationErrors = data.detail;
        if (Array.isArray(validationErrors)) {
          validationErrors.forEach((err) => {
            toast.error(`${err.loc[1]}: ${err.msg}`);
          });
        } else {
          toast.error(data.detail || '请求参数错误');
        }
        break;
      case 429:
        toast.error('请求过于频繁，请稍后重试');
        break;
      case 500:
        toast.error('服务器错误，请稍后重试');
        break;
      default:
        toast.error(data.detail || '请求失败');
    }

    return Promise.reject(error);
  }
);

export default apiClient;
```

### 4.3 加载状态优化

#### 骨架屏组件

```tsx
// frontend/src/components/ui/Skeleton.tsx

import React from 'react';

interface SkeletonProps {
  className?: string;
  count?: number;
}

export const Skeleton: React.FC<SkeletonProps> = ({ className = '', count = 1 }) => {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className={`animate-pulse bg-gray-200 rounded ${className}`}
        />
      ))}
    </>
  );
};

// Dashboard 骨架屏
export const DashboardSkeleton: React.FC = () => (
  <div className="min-h-screen bg-gray-50">
    {/* 顶部导航骨架 */}
    <header className="bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="flex justify-between items-center">
          <Skeleton className="h-8 w-32" />
          <Skeleton className="h-8 w-24" />
        </div>
      </div>
    </header>

    <main className="max-w-7xl mx-auto px-4 py-8">
      {/* 标题骨架 */}
      <div className="flex justify-between items-center mb-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-10 w-32" />
      </div>

      {/* 卡片网格骨架 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="bg-white rounded-2xl shadow-md p-6">
            <Skeleton className="h-6 w-3/4 mb-4" />
            <Skeleton className="h-4 w-full mb-2" />
            <Skeleton className="h-4 w-2/3 mb-4" />
            <div className="flex gap-2">
              <Skeleton className="h-8 w-20" />
              <Skeleton className="h-8 w-20" />
            </div>
          </div>
        ))}
      </div>
    </main>
  </div>
);

// 模板卡片骨架
export const TemplateCardSkeleton: React.FC = () => (
  <div className="bg-white rounded-2xl shadow-md p-6">
    <div className="flex items-start justify-between mb-4">
      <Skeleton className="w-12 h-12 rounded-xl" />
      <Skeleton className="h-6 w-16 rounded-full" />
    </div>
    <Skeleton className="h-6 w-3/4 mb-2" />
    <Skeleton className="h-4 w-full mb-4" />
    <div className="flex gap-2 mb-4">
      <Skeleton className="h-6 w-16 rounded-md" />
      <Skeleton className="h-6 w-16 rounded-md" />
    </div>
    <Skeleton className="h-4 w-24 mb-4" />
    <Skeleton className="h-10 w-full rounded-xl" />
  </div>
);

export const TemplateSkeletonGrid: React.FC = () => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mt-6">
    {Array.from({ length: 8 }).map((_, i) => (
      <TemplateCardSkeleton key={i} />
    ))}
  </div>
);
```

### 4.4 空状态组件

```tsx
// frontend/src/components/ui/EmptyState.tsx

import React from 'react';
import { AppleButton } from './AppleButton';

interface EmptyStateProps {
  icon: string;
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
      <div className="text-6xl mb-6">{icon}</div>
      <h3 className="text-xl font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600 text-center max-w-md mb-8">{description}</p>
      <div className="flex gap-3">
        {action && (
          <AppleButton onClick={action.onClick}>
            {action.label}
          </AppleButton>
        )}
        {secondaryAction && (
          <AppleButton variant="secondary" onClick={secondaryAction.onClick}>
            {secondaryAction.label}
          </AppleButton>
        )}
      </div>
    </div>
  );
};
```

---

## 五、响应式适配

### 5.1 断点系统

```typescript
// frontend/src/lib/responsive.ts

export const breakpoints = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
};

// 媒体查询 hooks
import { useState, useEffect } from 'react';

export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const media = window.matchMedia(query);
    if (media.matches !== matches) {
      setMatches(media.matches);
    }
    const listener = () => setMatches(media.matches);
    media.addEventListener('change', listener);
    return () => media.removeEventListener('change', listener);
  }, [matches, query]);

  return matches;
}

export function useIsMobile(): boolean {
  return useMediaQuery('(max-width: 767px)');
}

export function useIsTablet(): boolean {
  return useMediaQuery('(min-width: 768px) and (max-width: 1023px)');
}

export function useIsDesktop(): boolean {
  return useMediaQuery('(min-width: 1024px)');
}
```

### 5.2 响应式布局示例

```tsx
// frontend/src/pages/Dashboard.tsx (响应式版本)

const Dashboard: React.FC = () => {
  const isMobile = useIsMobile();
  const isTablet = useIsTablet();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部导航 - 移动端简化 */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-xl font-bold text-gray-900">Fugue</h1>
            {isMobile ? (
              <MobileMenu />
            ) : (
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-600">欢迎，{user?.username}</span>
                <Button variant="ghost" size="sm" onClick={() => navigate('/settings')}>
                  设置
                </Button>
                <Button variant="ghost" size="sm" onClick={handleLogout}>
                  退出
                </Button>
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* 标题区域 */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
          <h2 className="text-2xl font-bold text-gray-900">我的工作流</h2>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => navigate('/templates')}>
              浏览模板
            </Button>
            <Button onClick={() => createMutation.mutate()}>
              新建工作流
            </Button>
          </div>
        </div>

        {/* 卡片网格 - 响应式列数 */}
        <div className={`grid gap-6 ${
          isMobile ? 'grid-cols-1' :
          isTablet ? 'grid-cols-2' :
          'grid-cols-3'
        }`}>
          {crews?.map((crew) => (
            <CrewCard key={crew.id} crew={crew} />
          ))}
        </div>
      </main>
    </div>
  );
};
```

### 5.3 移动端菜单组件

```tsx
// frontend/src/components/layout/MobileMenu.tsx

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Menu, X, Home, FileText, Play, Settings, LogOut } from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';

export const MobileMenu: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const navigate = useNavigate();
  const { logout } = useAuthStore();

  const menuItems = [
    { icon: Home, label: '首页', path: '/' },
    { icon: FileText, label: '模板市场', path: '/templates' },
    { icon: Settings, label: '设置', path: '/settings' },
  ];

  const handleNavigate = (path: string) => {
    navigate(path);
    setIsOpen(false);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
      >
        {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
      </button>

      {isOpen && (
        <>
          {/* 遮罩层 */}
          <div
            className="fixed inset-0 bg-black/50 z-40"
            onClick={() => setIsOpen(false)}
          />

          {/* 菜单面板 */}
          <div className="fixed right-0 top-0 bottom-0 w-64 bg-white shadow-xl z-50 animate-slide-in-right">
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-gray-900">菜单</span>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-1 hover:bg-gray-100 rounded"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            <nav className="p-4">
              {menuItems.map((item) => (
                <button
                  key={item.path}
                  onClick={() => handleNavigate(item.path)}
                  className="w-full flex items-center gap-3 px-4 py-3 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors mb-1"
                >
                  <item.icon className="w-5 h-5" />
                  {item.label}
                </button>
              ))}

              <hr className="my-4" />

              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-3 px-4 py-3 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              >
                <LogOut className="w-5 h-5" />
                退出登录
              </button>
            </nav>
          </div>
        </>
      )}
    </div>
  );
};
```

---

## 六、测试策略

### 6.1 测试覆盖目标

| 测试类型 | 覆盖率目标 | 测试数量 |
|---------|-----------|---------|
| 单元测试 | > 80% | 100+ |
| 集成测试 | > 70% | 30-50 |
| E2E 测试 | 核心流程 100% | 5-10 |

### 6.2 关键测试用例

#### 认证系统测试

```typescript
describe('认证系统', () => {
  describe('Token 刷新', () => {
    it('应该在Token即将过期时显示续期弹窗');
    it('应该在用户点击续期后获取新Token');
    it('应该在用户忽略续期后继续当前操作');
    it('应该在Token完全过期后跳转登录页');
  });

  describe('路由守卫', () => {
    it('应该允许已认证用户访问受保护路由');
    it('应该重定向未认证用户到登录页');
    it('应该在编辑器页面提示保存草稿');
  });
});
```

#### 模板系统测试

```typescript
describe('模板系统', () => {
  describe('模板浏览', () => {
    it('应该显示所有内置模板');
    it('应该支持按分类筛选');
    it('应该支持关键词搜索');
    it('应该支持按热度排序');
  });

  describe('模板使用', () => {
    it('应该一键创建基于模板的工作流');
    it('应该正确填充Agent和Task配置');
    it('应该正确建立依赖关系');
  });

  describe('自定义模板', () => {
    it('应该支持从工作流保存为模板');
    it('应该支持编辑自定义模板');
    it('应该支持删除自定义模板');
  });
});
```

#### UI 组件测试

```typescript
describe('UI 组件', () => {
  describe('空状态', () => {
    it('Dashboard空状态应该显示引导卡片');
    it('模板市场空状态应该显示搜索建议');
    it('执行历史空状态应该显示创建提示');
  });

  describe('加载状态', () => {
    it('应该显示骨架屏加载动画');
    it('应该在数据加载完成后隐藏骨架屏');
  });

  describe('错误状态', () => {
    it('应该显示友好的错误提示');
    it('应该提供重试按钮');
  });
});
```

### 6.3 性能指标

| 指标 | 目标值 | 测量方式 |
|------|--------|---------|
| 首屏加载时间 | < 2秒 | Lighthouse |
| 交互响应时间 | < 100ms | Performance API |
| API 响应时间 | < 500ms | 后端日志 |
| Bundle 大小 | < 500KB | Webpack Analyzer |
| Lighthouse 分数 | > 90 | Lighthouse CI |

---

## 七、实施计划

### 7.1 开发顺序

**第1阶段：认证系统完善（1-2天）**
- 后端：Token 刷新 API
- 前端：authStore 扩展 + 续期弹窗
- 前端：路由守卫增强
- 测试：认证流程测试

**第2阶段：模板系统（3-4天）**
- 后端：Template 模型 + 迁移脚本
- 后端：模板 CRUD API
- 后端：预设5个模板数据
- 前端：模板市场页面
- 前端：模板卡片组件
- 前端：模板详情弹窗
- 测试：模板功能测试

**第3阶段：UI 打磨（2-3天）**
- 设计系统：Apple 风格组件库
- 错误处理：全局错误边界 + API 拦截器
- 加载状态：骨架屏组件
- 空状态：引导组件
- 响应式：移动端适配
- 测试：UI 组件测试

**第4阶段：测试验证（1天）**
- E2E 测试
- 性能测试
- 跨浏览器测试
- 响应式测试

### 7.2 交付物

- ✅ 完善的用户认证系统（Token 刷新 + 弹窗提醒）
- ✅ 模板系统（5个预设模板 + 模板市场页面）
- ✅ Apple 风格 UI 组件库
- ✅ 错误处理和加载状态优化
- ✅ 空状态引导页面
- ✅ 响应式适配（移动端、平板、桌面端）
- ✅ 测试用例和文档

---

## 八、附录

### 8.1 相关文件

**后端文件**：
- `backend/app/models/template.py` - Template 模型
- `backend/app/api/v1/templates.py` - 模板 API
- `backend/app/schemas/template.py` - 模板 Schema
- `backend/alembic/versions/add_templates_table.py` - 迁移脚本

**前端文件**：
- `frontend/src/pages/Templates.tsx` - 模板市场页面
- `frontend/src/components/templates/TemplateCard.tsx` - 模板卡片
- `frontend/src/components/templates/TemplateDetailModal.tsx` - 模板详情弹窗
- `frontend/src/components/ui/AppleButton.tsx` - Apple 风格按钮
- `frontend/src/components/ui/AppleCard.tsx` - Apple 风格卡片
- `frontend/src/components/ui/Skeleton.tsx` - 骨架屏组件
- `frontend/src/components/ui/EmptyState.tsx` - 空状态组件
- `frontend/src/stores/authStore.ts` - 认证状态管理（扩展）
- `frontend/src/stores/templateStore.ts` - 模板状态管理

### 8.2 依赖包

**前端新增依赖**：
```json
{
  "framer-motion": "^11.0.0"  // 动画库
}
```

**后端无需新增依赖**

---

*文档完成时间：2026-06-01*
*文档版本：v1.0*
