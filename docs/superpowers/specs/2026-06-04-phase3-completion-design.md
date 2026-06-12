# Phase 3 功能补全设计文档

> **日期**: 2026-06-04
> **状态**: 已批准
> **范围**: Webhook持久化、定时任务持久化、TODO逻辑补全、Plugin市场API

---

## 一、设计决策汇总

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 实现优先级 | 4个任务并行完成 | 全面补齐Phase 3功能 |
| 前端设计风格 | 混合布局（统计卡片+数据表格） | 平衡视觉和信息密度 |
| 数据库持久化 | 独立模型表 | 结构清晰，易于扩展 |
| TODO补全策略 | 完整实现 | 生产级质量 |
| Plugin市场API | 全部功能 | 完整生态建设 |
| 实现方案 | 分阶段实现 | 风险可控，每阶段可验证 |

---

## 二、数据库模型设计

### 2.1 Webhook模型 (webhooks表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| user_id | UUID FK | 关联用户 |
| url | String | 回调URL |
| events | JSON | 订阅事件列表 |
| secret_hash | String | 签名密钥哈希 |
| is_active | Boolean | 是否启用 |
| failure_count | Integer | 连续失败次数 |
| last_triggered_at | DateTime | 最后触发时间 |
| created_at | DateTime | 创建时间 |

### 2.2 定时任务模型 (scheduled_tasks表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| user_id | UUID FK | 关联用户 |
| crew_id | UUID FK | 关联工作流 |
| cron_expression | String | Cron表达式 |
| timezone | String | 时区 |
| inputs | JSON | 执行输入 |
| is_active | Boolean | 是否启用 |
| last_run_at | DateTime | 上次执行时间 |
| next_run_at | DateTime | 下次执行时间 |
| run_count | Integer | 执行次数 |
| failure_count | Integer | 失败次数 |

### 2.3 Plugin评论模型 (plugin_reviews表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| plugin_id | UUID FK | 关联插件 |
| user_id | UUID FK | 评论用户 |
| rating | Integer | 评分 1-5 |
| comment | Text | 评论内容 |
| created_at | DateTime | 评论时间 |

---

## 三、TODO逻辑补全设计

### 3.1 速率限制检查 (published.py)

**实现方案**: Redis滑动窗口算法

```python
async def check_rate_limit(api_key, db):
    limit = api_key.rate_limit  # 默认60次/分钟
    key = f"rate_limit:{api_key.id}"
    now = time.time()
    window_start = now - 60

    pipe = redis.pipeline()
    pipe.zremrangebyscore(key, 0, window_start)
    pipe.zadd(key, {str(now): now})
    pipe.zcard(key)
    pipe.expire(key, 60)
    _, _, count, _ = await pipe.execute()

    if count > limit:
        raise HTTPException(429, "Rate limit exceeded")
```

### 3.2 异步启动执行 (published.py)

**实现方案**: Celery任务队列

```python
# app/tasks/execution_tasks.py
@celery_app.task(bind=True, max_retries=3)
def execute_workflow_task(self, execution_id: str):
    """异步执行工作流"""
    try:
        engine = ExecutionEngine()
        asyncio.run(engine.execute(execution_id))
    except Exception as exc:
        self.retry(exc=exc, countdown=60)

# published.py 中调用
execute_workflow_task.delay(str(execution.id))
```

### 3.3 定时任务执行 (scheduler_service.py)

**实现方案**: 与API执行共用Celery Task

```python
async def _execute_task(self, task: ScheduledTask):
    """执行定时任务"""
    # 1. 创建执行记录
    execution = Execution(
        crew_id=task.crew_id,
        user_id=task.user_id,
        status=ExecutionStatus.PENDING,
        trigger_type="scheduled",
    )
    db.add(execution)
    await db.commit()

    # 2. 通过Celery触发异步执行
    execute_workflow_task.delay(str(execution.id))

    # 3. 更新任务状态
    task.mark_executed(success=True)
    await db.commit()
```

---

## 四、前端页面设计

### 4.1 页面结构

采用混合布局：顶部统计卡片 + 下方数据表格

#### Webhook管理页面 (/webhooks)
- **统计卡片**: Webhook总数、活跃数、禁用数
- **数据表格**: URL、订阅事件、状态、操作（测试/删除）
- **操作按钮**: 创建Webhook

#### 定时任务页面 (/schedules)
- **统计卡片**: 任务总数、运行中、总执行次数
- **数据表格**: 工作流名称、Cron表达式、下次运行、操作（暂停/删除）
- **操作按钮**: 创建定时任务

#### API发布页面 (/published)
- **统计卡片**: 已发布API、总调用次数、API Key数量
- **数据表格**: 名称、Endpoint、调用次数、操作（文档/取消发布）
- **操作按钮**: 发布新API、管理API Key

### 4.2 路由配置

```tsx
<Route path="/webhooks" element={<WebhooksPage />} />
<Route path="/schedules" element={<SchedulesPage />} />
<Route path="/published" element={<PublishedPage />} />
```

### 4.3 API客户端文件

- `frontend/src/api/webhooks.ts` - Webhook API封装
- `frontend/src/api/schedules.ts` - 定时任务API封装
- `frontend/src/api/published.ts` - API发布API封装

---

## 五、Plugin市场API设计

### 5.1 API端点列表

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /plugins/marketplace/publish | 发布插件到市场 |
| GET | /plugins/marketplace/list | 获取市场插件列表 |
| GET | /plugins/marketplace/{id} | 获取插件详情 |
| PUT | /plugins/marketplace/{id} | 更新插件信息 |
| DELETE | /plugins/marketplace/{id} | 删除插件 |
| POST | /plugins/marketplace/{id}/install | 安装插件 |
| POST | /plugins/marketplace/{id}/uninstall | 卸载插件 |
| GET | /plugins/marketplace/installed | 获取已安装插件 |
| POST | /plugins/marketplace/{id}/rate | 评分插件 |
| GET | /plugins/marketplace/{id}/reviews | 获取评论列表 |
| POST | /plugins/marketplace/{id}/reviews | 添加评论 |

### 5.2 安装流程

1. 检查插件是否存在且已发布
2. 检查用户是否已安装
3. 下载插件包（或记录安装关系）
4. 调用 PluginLoader 加载插件
5. 返回安装结果

### 5.3 新增模型

- **plugin_reviews表**: 存储用户评分和评论
- **plugin_installations表**: 记录用户安装关系（可选，或使用现有字段）

---

## 六、实现计划

### Phase 1: 后端持久化 + TODO补全

1. 创建Alembic迁移脚本
2. 实现Webhook模型和服务重构
3. 实现定时任务模型和服务重构
4. 补全速率限制逻辑
5. 补全异步执行逻辑
6. 补全定时任务执行逻辑
7. 运行测试验证

### Phase 2: 前端页面

1. 创建3个API客户端文件
2. 实现Webhook管理页面
3. 实现定时任务管理页面
4. 实现API发布管理页面
5. 注册路由
6. 测试页面功能

### Phase 3: Plugin市场API

1. 创建plugin_reviews模型
2. 实现发布/更新/删除API
3. 实现安装/卸载API
4. 实现评分/评论API
5. 运行测试验证

---

## 七、验收标准

- [ ] Webhook配置重启后不丢失
- [ ] 定时任务配置重启后不丢失
- [ ] API执行受速率限制保护
- [ ] 定时任务能自动触发执行
- [ ] 3个前端页面可正常访问和操作
- [ ] Plugin市场支持发布、安装、评分、评论
- [ ] 所有新功能有对应的测试用例

---

## 八、技术风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| Celery集成复杂 | 中 | 参考现有执行引擎实现 |
| Redis滑动窗口精度 | 低 | 使用Sorted Set确保精确 |
| 前端组件复用性 | 低 | 参考现有页面结构 |
| Plugin安装安全性 | 高 | 沙箱隔离，权限检查 |
