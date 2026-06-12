# Fugue Celery 集成指南

## 概述

本指南介绍如何配置和使用 Celery 作为 Fugue 的生产级任务队列系统。

## 架构

```
┌─────────────────┐     ┌─────────────┐     ┌──────────────────┐
│   FastAPI API   │────>│    Redis     │────>│  Celery Worker   │
│  (提交任务)      │     │  (消息队列)   │     │  (执行工作流)     │
└─────────────────┘     └─────────────┘     └──────────────────┘
```

## 配置

### 环境变量

在 `.env` 文件中配置以下变量：

```bash
# Redis配置
REDIS_URL=redis://localhost:6379/0

# Celery配置
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
USE_CELERY=true  # 生产环境设为true
```

### 配置说明

- **CELERY_BROKER_URL**: 消息队列地址（建议使用独立的Redis数据库）
- **CELERY_RESULT_BACKEND**: 任务结果存储地址
- **USE_CELERY**: 是否启用Celery（开发环境可设为false使用asyncio）

## 部署

### 使用 Docker Compose

```bash
# 启动所有服务
docker-compose up -d

# 仅启动必要的服务
docker-compose up -d redis postgres celery-worker

# 查看日志
docker-compose logs -f celery-worker
```

### 手动部署

```bash
# 启动 Redis
redis-server

# 启动 Celery Worker
cd backend
celery -A app.tasks.celery_app worker --loglevel=info --concurrency=4 -Q execution,default

# 启动 Celery Beat（定时任务）
celery -A app.tasks.celery_app beat --loglevel=info
```

## 任务队列

### 队列配置

- **default**: 默认队列，用于一般任务
- **execution**: 执行队列，专门用于工作流执行

### 任务类型

1. **execute_workflow**: 执行工作流
   - 最大重试次数: 3
   - 重试延迟: 60秒
   - 软超时: 30分钟
   - 硬超时: 1小时

2. **cancel_execution**: 取消执行

## API 使用

### 创建执行

```bash
curl -X POST http://localhost:8000/api/v1/executions/ \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "crew_id": "your-crew-id",
    "trigger_type": "manual",
    "inputs": {}
  }'
```

响应示例：
```json
{
  "id": "execution-id",
  "crew_id": "crew-id",
  "status": "pending",
  "celery_task_id": "celery-task-id"
}
```

### 取消执行

```bash
curl -X POST http://localhost:8000/api/v1/executions/{execution_id}/cancel \
  -H "Authorization: Bearer {token}"
```

## 监控

### Celery Flower（可选）

```bash
# 安装
pip install flower

# 启动
celery -A app.tasks.celery_app flower --port=5555

# 访问
http://localhost:5555
```

### 查看任务状态

```python
from app.tasks.celery_app import celery_app

# 获取任务信息
result = celery_app.AsyncResult(task_id)
print(result.status)  # PENDING, STARTED, SUCCESS, FAILURE
print(result.result)  # 任务结果
```

## 开发环境

### 禁用 Celery

在开发环境中，可以禁用 Celery 使用 asyncio 直接执行：

```bash
USE_CELERY=false
```

这将使用 `asyncio.create_task` 直接在后台执行任务，无需启动 Celery Worker。

### 测试

```bash
# 运行测试脚本
python test_celery.py

# 检查 Celery 配置
celery -A app.tasks.celery_app inspect conf
```

## 故障排除

### 常见问题

1. **任务不执行**
   - 检查 Redis 连接: `redis-cli ping`
   - 检查 Worker 日志: `docker-compose logs celery-worker`
   - 确认队列名称正确: `celery -A app.tasks.celery_app inspect active_queues`

2. **任务超时**
   - 调整 `task_soft_time_limit` 和 `task_time_limit`
   - 检查 LLM API 响应时间

3. **数据库连接错误**
   - 确保 Worker 能访问数据库
   - 检查数据库连接池配置

### 调试命令

```bash
# 查看活跃任务
celery -A app.tasks.celery_app inspect active

# 查看注册任务
celery -A app.tasks.celery_app inspect registered

# 查看队列长度
celery -A app.tasks.celery_app inspect reserved

# 清空队列
celery -A app.tasks.celery_app purge
```

## 性能优化

### Worker 并发数

根据 CPU 核心数调整并发数：

```bash
celery -A app.tasks.celery_app worker --concurrency=8
```

### 预取设置

```python
# celery_app.py
celery_app.conf.update(
    worker_prefetch_multiplier=1,  # 禁用预取，适合长任务
)
```

### 结果过期

```python
# 设置结果过期时间（24小时）
celery_app.conf.result_expires = 86400
```

## 生产部署建议

1. **使用独立的 Redis 实例**用于 Celery
2. **监控 Worker 进程**，确保自动重启
3. **配置日志收集**，便于问题排查
4. **设置任务超时**，防止任务无限运行
5. **使用 Flower 监控**任务执行情况
6. **定期清理结果**，避免 Redis 内存溢出

## 相关文件

- `backend/app/tasks/celery_app.py`: Celery 应用配置
- `backend/app/tasks/execution_tasks.py`: 执行任务定义
- `backend/app/models/execution.py`: 执行模型（包含 celery_task_id）
- `backend/app/api/v1/executions.py`: 执行 API
- `docker-compose.yml`: Docker 部署配置
