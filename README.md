# Fugue - 多智能体协作工作流平台

[![CI](https://github.com/yourusername/fugue/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/fugue/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 🚀 面向开发者和高级用户的开源多智能体协作编排平台

## 📖 项目简介

Fugue 让你能够通过可视化拖拽的方式，快速构建、调试和部署多Agent协作工作流。

### 核心特性

- 🎨 **可视化DAG编辑器** - 拖拽式设计Agent和Task
- 🤖 **多Agent协作** - 支持Sequential、Parallel、Hierarchical执行模式
- 🔌 **多模型支持** - OpenAI、Anthropic、Google、Ollama等
- 📊 **实时监控** - WebSocket实时推送Agent思考过程
- 🔐 **安全沙箱** - Docker容器隔离执行自定义代码
- 🚀 **一键部署** - Docker Compose一键启动

## 🛠️ 技术栈

### 前端
- React 19 + TypeScript
- Vite 6
- ReactFlow 12（可视化画布）
- Zustand 5（状态管理）
- TanStack Query（数据获取）
- Tailwind CSS 4

### 后端
- Python 3.12+
- FastAPI 0.115+
- SQLAlchemy 2.0 + Alembic
- Celery + Redis（异步任务）
- CrewAI / LangGraph（Agent框架）

### 基础设施
- PostgreSQL 16
- Redis 7
- MinIO（对象存储）
- Docker + Docker Compose

---

## 🚀 快速开始

### 方式一：一键启动（推荐）

**前置要求：**
- Docker 24+
- Docker Compose v2

**Windows用户：**

```cmd
docker-start.bat start
```

**Linux/macOS用户：**

```bash
chmod +x docker-start.sh
./docker-start.sh start
```

脚本会自动：
1. 检查Docker环境
2. 创建配置文件
3. 启动所有服务
4. 运行数据库迁移
5. 初始化演示数据
6. 显示访问信息

**服务访问地址：**

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端应用 | http://localhost:3000 | React应用 |
| 后端API | http://localhost:8000 | FastAPI服务 |
| API文档 | http://localhost:8000/docs | Swagger UI |
| MinIO控制台 | http://localhost:9001 | 对象存储管理 |

**演示账号：**
- 邮箱：demo@fugue.com
- 密码：Demo123456

**其他常用命令：**

```bash
# 查看服务状态
docker-start.bat status  # Windows
./docker-start.sh status # Linux/macOS

# 查看日志
docker-start.bat logs backend
./docker-start.sh logs backend

# 停止服务
docker-start.bat stop
./docker-start.sh stop

# 查看帮助
docker-start.bat help
./docker-start.sh help
```

---

### 方式二：手动Docker Compose

如果需要更多控制，可以直接使用Docker Compose命令：

```bash
# 1. 复制环境变量配置
cp .env.example .env

# 2. 启动所有服务（开发模式）
docker compose --profile development up -d --build

# 3. 运行数据库迁移
docker compose exec backend alembic upgrade head

# 4. 初始化演示数据
docker compose exec backend python init_data.py

# 5. 查看服务状态
docker compose ps

# 6. 查看日志（可选）
docker compose logs -f backend
```

**停止服务：**

```bash
docker compose down
```

**清除所有数据（谨慎使用）：**

```bash
docker compose down -v  # 删除所有数据卷
```

---

### 方式二：本地开发环境

**前置要求：**
- Python 3.12+
- Node.js 20+ 和 npm
- PostgreSQL 16
- Redis 7

#### 步骤1：启动数据库服务

确保PostgreSQL和Redis已启动运行。

**创建数据库：**

```bash
# 使用psql连接PostgreSQL
psql -U postgres

# 创建数据库
CREATE DATABASE fugue;

# 退出
\q
```

#### 步骤2：启动后端

```bash
# 进入后端目录
cd backend

# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 复制环境变量配置
cp .env.example .env

# 运行数据库迁移
alembic upgrade head
# 如果迁移失败，先创建迁移：
# alembic revision --autogenerate -m "Initial migration"
# alembic upgrade head

# 启动后端服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端启动成功后，访问 http://localhost:8000/docs 查看API文档。

#### 步骤3：启动前端

打开新的终端窗口：

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端启动成功后，访问 http://localhost:3000

---

### 方式三：使用启动脚本

**Windows：**

```cmd
start-dev.bat
```

**Linux/macOS：**

```bash
chmod +x start-dev.sh
./start-dev.sh
```

脚本会自动引导你完成启动过程。

---

## 📁 项目结构

```
fugue/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── api/               # API路由
│   │   │   └── v1/           # API v1版本
│   │   │       ├── auth.py   # 认证接口
│   │   │       ├── crews.py  # 工作流接口
│   │   │       ├── agents.py # 智能体接口
│   │   │       ├── tasks.py  # 任务接口
│   │   │       └── executions.py # 执行接口
│   │   ├── core/              # 核心模块
│   │   │   ├── config.py    # 配置管理
│   │   │   ├── database.py  # 数据库连接
│   │   │   └── security.py  # 认证安全
│   │   ├── models/            # SQLAlchemy模型
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # 业务逻辑
│   │   ├── engine/            # 执行引擎
│   │   └── main.py           # FastAPI入口
│   ├── alembic/               # 数据库迁移
│   ├── tests/                 # 测试
│   ├── requirements.txt       # Python依赖
│   └── Dockerfile
│
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── api/              # API客户端
│   │   ├── components/       # React组件
│   │   │   ├── ui/          # 基础UI组件
│   │   │   ├── nodes/       # ReactFlow节点
│   │   │   └── panels/      # 面板组件
│   │   ├── pages/            # 页面组件
│   │   ├── stores/           # Zustand状态
│   │   ├── types/            # TypeScript类型
│   │   ├── hooks/            # 自定义Hooks
│   │   ├── lib/              # 工具函数
│   │   └── App.tsx           # 应用入口
│   ├── package.json
│   └── Dockerfile
│
├── docker-compose.yml          # Docker编排
├── .github/workflows/         # CI/CD
├── start-dev.bat              # Windows启动脚本
├── start-dev.sh               # Linux/macOS启动脚本
└── README.md
```

---

## 🔧 环境变量配置

### 后端环境变量 (backend/.env)

```env
# 应用配置
APP_NAME=Fugue
APP_VERSION=0.1.0
DEBUG=true

# 数据库
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/fugue
DATABASE_URL_SYNC=postgresql+psycopg2://postgres:postgres@localhost:5432/fugue

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT密钥（请在生产环境修改）
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]

# LLM API Keys（可选）
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=
```

---

## 📚 API文档

启动后端服务后，访问以下地址查看API文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 主要API端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/auth/register` | POST | 用户注册 |
| `/api/v1/auth/login` | POST | 用户登录 |
| `/api/v1/crews/` | GET/POST | 工作流列表/创建 |
| `/api/v1/crews/{id}` | GET/PUT/DELETE | 工作流详情/更新/删除 |
| `/api/v1/agents/` | POST | 创建智能体 |
| `/api/v1/agents/{id}` | GET/PUT/DELETE | 智能体操作 |
| `/api/v1/tasks/` | POST | 创建任务 |
| `/api/v1/tasks/{id}` | GET/PUT/DELETE | 任务操作 |
| `/api/v1/executions/` | GET/POST | 执行记录/启动执行 |

---

## 🧪 开发指南

### 运行测试

**快速测试（推荐）：**

```bash
# 运行完整测试套件
chmod +x run_tests.sh
./run_tests.sh
```

**单独运行测试：**

```bash
# 后端单元测试
cd backend
pytest tests/ -v

# 后端测试（带覆盖率）
pytest tests/ -v --cov=app --cov-report=html

# 端到端测试（需要服务运行）
python tests/e2e_test.py

# 前端测试
cd frontend
npm run test
```

### 代码质量检查

```bash
# 后端Lint和类型检查
cd backend
ruff check .
mypy app/

# 前端Lint
cd frontend
npm run lint
```

### 数据库迁移

```bash
cd backend

# 创建新迁移
alembic revision --autogenerate -m "描述信息"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1

# 查看迁移历史
alembic history
```

### 测试覆盖的功能

我们的测试套件覆盖了以下核心功能：

- ✅ **认证系统** - 注册、登录、Token管理
- ✅ **工作流管理** - CRUD操作、级联删除
- ✅ **Agent管理** - 创建、更新、删除、工具配置
- ✅ **任务管理** - 依赖关系、输出类型、验证规则
- ✅ **执行引擎** - 生命周期、并发执行、取消
- ✅ **模板系统** - 预设模板、自定义模板、使用统计
- ✅ **DAG校验** - 环检测、结构验证、就绪检查
- ✅ **边界条件** - 错误处理、并发访问、资源清理

---

## 🐛 常见问题

### 1. PostgreSQL连接失败

确保PostgreSQL服务已启动，并检查：
- 数据库`fugue`是否已创建
- 用户名密码是否正确（默认：postgres/postgres）
- 端口5432是否被占用

### 2. Redis连接失败

确保Redis服务已启动，默认端口6379。

### 3. 前端启动报错

```bash
# 清除node_modules重新安装
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### 4. 后端依赖安装失败

```bash
# 升级pip
pip install --upgrade pip

# 使用国内镜像（可选）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 5. Alembic迁移失败

```bash
# 重置数据库
psql -U postgres -c "DROP DATABASE IF EXISTS fugue;"
psql -U postgres -c "CREATE DATABASE fugue;"
alembic upgrade head
```

---

## 📋 开发路线图

### Phase 1: MVP（Week 1-6）- 进行中

- [x] **Week 1**: 项目搭建 + 数据库设计 ✅
- [x] **Week 2**: ReactFlow画布集成 ✅
- [x] **Week 3**: CrewAI集成 + 顺序执行 ✅
- [x] **Week 4**: 并行执行 + DAG调度 ✅
- [x] **Week 5**: 模板系统 + 用户认证 ✅
- [x] **Week 6**: 集成测试 + 部署准备 ✅

### Phase 2: 进阶能力（Week 7-14）- 计划中

- [ ] **Week 7-8**: 高级编排能力（条件分支、循环、子工作流）
- [ ] **Week 9-10**: 记忆与知识库（短期/长期记忆、RAG）
- [ ] **Week 11-12**: 多模型协作（智能路由、成本控制）
- [ ] **Week 13-14**: MCP集成 + 打磨

### Phase 3: 生态建设（Month 3-6）- 未来规划

- [ ] 插件SDK
- [ ] 模板市场
- [ ] API发布和Webhook
- [ ] 团队协作

---

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 📧 联系方式

- 项目主页: https://github.com/yourusername/fugue
- 问题反馈: https://github.com/yourusername/fugue/issues

---

## 🙏 致谢

感谢以下开源项目：
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [ReactFlow](https://reactflow.dev/)
- [CrewAI](https://www.crewai.com/)
- [LangChain](https://www.langchain.com/)
