# Fugue 完整启动指南

本文档提供Fugue项目的完整启动步骤，包含Docker部署和本地开发两种方式。

---

## 📋 前置要求

### 系统要求
- **操作系统**: Windows 10/11, macOS, 或 Linux
- **内存**: 至少8GB RAM（推荐16GB）
- **磁盘空间**: 至少10GB可用空间

### 必需软件
- **Docker Desktop** >= 4.0
  - 下载：https://www.docker.com/products/docker-desktop
- **Docker Compose** >= 2.0（Docker Desktop自带）
- **Git**（用于克隆代码）

### 可选软件（本地开发需要）
- **Python** >= 3.12
- **Node.js** >= 20.x 和 npm >= 10.x
- **PostgreSQL** >= 16
- **Redis** >= 7

---

## 🚀 方式一：Docker一键部署（推荐）

这是最简单、最推荐的启动方式，适合快速体验和生产部署。

### 步骤 1: 克隆项目（如果还没有）

```bash
# 如果项目已存在，跳过此步骤
git clone <repository-url>
cd fugue
```

### 步骤 2: 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件（可选，使用默认配置即可启动）
# Windows: 使用记事本或VS Code
notepad .env

# Linux/macOS: 使用nano或vim
nano .env
```

**重要配置项（可选修改）**：

```bash
# 数据库密码（建议修改以提高安全性）
POSTGRES_PASSWORD=your_secure_password_here

# Redis密码
REDIS_PASSWORD=your_redis_password_here

# JWT密钥（生产环境必须修改！）
SECRET_KEY=your_very_long_random_secret_key_here

# MinIO密码
MINIO_PASSWORD=your_minio_password_here
```

**生成安全密钥的命令**：

```bash
# 生成JWT密钥（32字节十六进制）
openssl rand -hex 32

# 生成数据库密码（Base64编码）
openssl rand -base64 32
```

### 步骤 3: 启动所有服务

#### Windows用户

```cmd
# 使用Windows批处理脚本
docker-start.bat start
```

#### Linux/macOS用户

```bash
# 添加执行权限
chmod +x docker-start.sh

# 启动开发环境
./docker-start.sh start

# 或启动生产环境
./docker-start.sh start prod
```

#### 或者直接使用Docker Compose

```bash
# 开发环境
docker compose --profile development up -d --build

# 生产环境
docker compose --profile production up -d --build
```

### 步骤 4: 等待服务启动

启动过程大约需要2-5分钟，取决于网络速度和机器性能。

**查看启动进度**：

```bash
# 查看所有服务状态
docker compose ps

# 查看实时日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f backend
docker compose logs -f frontend
```

**预期看到的服务列表**：

```
NAME                    STATUS      PORTS
fugue-backend      running     0.0.0.0:8000->8000/tcp
fugue-frontend     running     0.0.0.0:3000->3000/tcp
fugue-postgres     running     0.0.0.0:5432->5432/tcp
fugue-redis        running     0.0.0.0:6379->6379/tcp
fugue-minio        running     0.0.0.0:9000-9001->9000-9001/tcp
```

### 步骤 5: 初始化数据库

```bash
# 运行数据库迁移
docker compose exec backend alembic upgrade head

# 初始化演示数据（演示用户和模板）
docker compose exec backend python init_data.py

# 或者初始化完整的演示环境（包含示例工作流）
docker compose exec backend python seed_demo.py
```

### 步骤 6: 验证服务

#### 检查后端健康状态

```bash
# 健康检查端点
curl http://localhost:8000/health

# 预期返回：{"status": "healthy"}
```

#### 检查前端

```bash
# 使用curl检查
curl -I http://localhost:3000

# 预期返回：HTTP/1.1 200 OK
```

#### 查看API文档

打开浏览器访问：http://localhost:8000/docs

### 步骤 7: 访问应用

🎉 **启动成功！** 现在可以访问：

| 服务 | 地址 | 说明 |
|------|------|------|
| **前端应用** | http://localhost:3000 | 主应用界面 |
| **后端API** | http://localhost:8000 | API服务 |
| **API文档** | http://localhost:8000/docs | Swagger UI文档 |
| **API文档** | http://localhost:8000/redoc | ReDoc文档 |
| **MinIO控制台** | http://localhost:9001 | 对象存储管理 |

### 步骤 8: 登录系统

**演示账号**：
- **邮箱**: `demo@fugue.com`
- **密码**: `Demo123456`

**管理员账号**（如果运行了seed_demo.py）：
- **邮箱**: `admin@fugue.com`
- **密码**: `Admin123456`

---

## 💻 方式二：本地开发环境

适合需要修改代码、调试功能的开发者。

### 步骤 1: 启动基础服务

首先使用Docker启动数据库等基础服务：

```bash
# 只启动数据库服务
docker compose up -d postgres redis minio

# 或者修改docker-compose.yml，注释掉backend和frontend服务
```

### 步骤 2: 配置并启动后端

```bash
# 进入后端目录
cd backend

# 创建Python虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate

# Linux/macOS:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 复制并编辑环境变量
cp .env.example .env
# 编辑.env文件，配置数据库连接等

# 运行数据库迁移
alembic upgrade head

# 初始化数据
python init_data.py

# 启动后端服务（开发模式）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**后端将在以下地址运行**：
- API服务：http://localhost:8000
- API文档：http://localhost:8000/docs

### 步骤 3: 配置并启动前端

打开新的终端窗口：

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

**前端将在以下地址运行**：
- 应用：http://localhost:5173 或 http://localhost:3000

### 步骤 4: 验证本地环境

```bash
# 检查后端
curl http://localhost:8000/health

# 检查前端
curl http://localhost:5173

# 运行测试
cd backend
pytest tests/ -v
```

---

## 🔧 常用管理命令

### Docker服务管理

```bash
# 查看服务状态
docker compose ps

# 查看所有服务日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f postgres

# 重启所有服务
docker compose restart

# 重启特定服务
docker compose restart backend

# 停止所有服务
docker compose down

# 停止并删除数据卷（⚠️ 会丢失数据！）
docker compose down -v

# 重建并重启服务
docker compose up -d --build

# 重建特定服务
docker compose up -d --build backend
```

### 使用启动脚本（推荐）

```bash
# Windows
docker-start.bat start        # 启动开发环境
docker-start.bat start prod   # 启动生产环境
docker-start.bat stop         # 停止服务
docker-start.bat restart      # 重启服务
docker-start.bat status       # 查看状态
docker-start.bat logs backend # 查看后端日志
docker-start.bat cleanup      # 清理所有数据（⚠️ 危险！）
docker-start.bat help         # 查看帮助

# Linux/macOS
./docker-start.sh start
./docker-start.sh start prod
./docker-start.sh stop
./docker-start.sh restart
./docker-start.sh status
./docker-start.sh logs backend
./docker-start.sh cleanup
./docker-start.sh help
```

### 数据库管理

```bash
# 进入PostgreSQL命令行
docker compose exec postgres psql -U postgres -d fugue

# 备份数据库
docker compose exec postgres pg_dump -U postgres fugue > backup.sql

# 恢复数据库
docker compose exec -T postgres psql -U postgres fugue < backup.sql

# 运行数据库迁移
docker compose exec backend alembic upgrade head

# 创建新的迁移
docker compose exec backend alembic revision --autogenerate -m "描述信息"

# 回滚迁移
docker compose exec backend alembic downgrade -1
```

### 查看数据

```bash
# 连接PostgreSQL
docker compose exec postgres psql -U postgres -d fugue

# 查看表
\dt

# 查看用户表
SELECT id, email, username, created_at FROM users LIMIT 10;

# 查看工作流
SELECT id, name, created_at FROM crews LIMIT 10;

# 查看执行记录
SELECT id, status, total_tokens_used, total_cost_usd FROM executions LIMIT 10;

# 退出
\q
```

---

## 🧪 运行测试

### 后端测试

```bash
# 进入后端目录
cd backend

# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_auth.py -v

# 运行带覆盖率的测试
pytest tests/ -v --cov=app --cov-report=html

# 运行WebSocket测试
python tests/test_websocket.py
```

### 前端测试

```bash
# 进入前端目录
cd frontend

# 运行测试
npm run test

# 运行带覆盖率的测试
npm run test:coverage
```

### 端到端测试

```bash
# 确保服务已启动
# 运行E2E测试
python tests/e2e_test.py
```

---

## 🔍 故障排除

### 问题1: 端口被占用

**错误信息**：
```
Error: Bind for 0.0.0.0:8000 failed: port is already allocated
```

**解决方案**：

```bash
# 查看端口占用情况
# Windows
netstat -ano | findstr :8000
netstat -ano | findstr :3000
netstat -ano | findstr :5432

# Linux/macOS
lsof -i :8000
lsof -i :3000
lsof -i :5432

# 停止占用端口的进程
# Windows: 使用任务管理器或
taskkill /PID <PID> /F

# Linux/macOS
kill -9 <PID>

# 或者修改docker-compose.yml中的端口映射
# 例如：将 "8000:8000" 改为 "8001:8000"
```

### 问题2: Docker服务启动失败

**检查Docker状态**：

```bash
# 检查Docker是否运行
docker --version
docker compose version

# 检查Docker服务状态
docker info

# 查看详细错误日志
docker compose logs backend
```

**常见解决方案**：

```bash
# 1. 重启Docker Desktop
# Windows: 右键系统托盘Docker图标 -> Restart
# macOS: 点击菜单栏Docker图标 -> Restart

# 2. 清理Docker缓存
docker system prune -a

# 3. 重新构建
docker compose down
docker compose up -d --build
```

### 问题3: 数据库连接失败

**错误信息**：
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**解决方案**：

```bash
# 1. 检查PostgreSQL服务是否运行
docker compose ps postgres

# 2. 查看PostgreSQL日志
docker compose logs postgres

# 3. 检查数据库是否创建
docker compose exec postgres psql -U postgres -l

# 4. 手动创建数据库（如果不存在）
docker compose exec postgres psql -U postgres -c "CREATE DATABASE fugue;"

# 5. 检查环境变量配置
cat .env | grep DATABASE_URL
```

### 问题4: 前端无法连接后端

**检查项**：

```bash
# 1. 确认后端是否运行
curl http://localhost:8000/health

# 2. 检查CORS配置
# 查看backend/.env中的CORS_ORIGINS设置

# 3. 检查浏览器控制台错误
# 打开浏览器开发者工具（F12）查看Console和Network标签页

# 4. 检查API URL配置
cat frontend/src/api/client.ts
```

### 问题5: 依赖安装失败

**Python依赖**：

```bash
# 升级pip
pip install --upgrade pip

# 使用国内镜像（如果网络慢）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或使用阿里云镜像
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

**Node.js依赖**：

```bash
# 清理缓存
npm cache clean --force

# 删除node_modules重新安装
rm -rf node_modules package-lock.json
npm install

# 使用国内镜像
npm config set registry https://registry.npmmirror.com
npm install
```

### 问题6: 数据库迁移失败

**解决方案**：

```bash
# 查看当前迁移状态
docker compose exec backend alembic current

# 查看迁移历史
docker compose exec backend alembic history

# 如果迁移失败，重置数据库
docker compose exec postgres psql -U postgres -c "DROP DATABASE IF EXISTS fugue;"
docker compose exec postgres psql -U postgres -c "CREATE DATABASE fugue;"

# 重新运行迁移
docker compose exec backend alembic upgrade head

# 初始化数据
docker compose exec backend python init_data.py
```

### 问题7: WebSocket连接失败

**检查项**：

```bash
# 1. 检查后端WebSocket端点
curl http://localhost:8000/api/v1/ws/ws/stats

# 2. 查看浏览器控制台WebSocket错误
# 打开浏览器开发者工具 -> Network -> WS标签页

# 3. 检查防火墙设置
# 确保WebSocket端口（通常是8000）没有被阻止
```

---

## 📊 验证清单

启动完成后，按此清单验证所有功能：

### 基础服务 ✅

- [ ] PostgreSQL运行正常 (`docker compose ps postgres`)
- [ ] Redis运行正常 (`docker compose ps redis`)
- [ ] MinIO运行正常 (`docker compose ps minio`)

### 后端服务 ✅

- [ ] 后端服务运行正常 (`docker compose ps backend`)
- [ ] 健康检查通过 (`curl http://localhost:8000/health`)
- [ ] API文档可访问 (`http://localhost:8000/docs`)
- [ ] 数据库迁移完成 (`docker compose exec backend alembic current`)

### 前端服务 ✅

- [ ] 前端服务运行正常 (`docker compose ps frontend`)
- [ ] 前端页面可访问 (`http://localhost:3000`)
- [ ] 可以正常登录
- [ ] 页面样式正常显示

### 功能验证 ✅

- [ ] 用户注册功能正常
- [ ] 用户登录功能正常
- [ ] 可以创建新工作流
- [ ] 可以添加Agent和Task
- [ ] 可以运行工作流
- [ ] 实时监控显示正常
- [ ] Dashboard统计数据正确

---

## 🎯 快速启动命令汇总

### 最快启动（3条命令）

```bash
# 1. 配置环境
cp .env.example .env

# 2. 启动所有服务
docker compose --profile development up -d --build

# 3. 初始化数据
docker compose exec backend alembic upgrade head && \
docker compose exec backend python init_data.py
```

### 使用启动脚本（1条命令）

```bash
# Windows
docker-start.bat start

# Linux/macOS
./docker-start.sh start
```

### 访问应用

打开浏览器访问：**http://localhost:3000**

登录账号：
- 邮箱：`demo@fugue.com`
- 密码：`Demo123456`

---

## 📚 相关文档

- [README.md](README.md) - 项目概述
- [QUICK_START.md](docs/QUICK_START.md) - 快速开始指南
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) - 部署指南
- [DEMO_GUIDE.md](docs/DEMO_GUIDE.md) - 演示指南
- [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - 故障排除

---

## 💡 提示和最佳实践

### 开发环境建议

1. **使用Docker Desktop** - 最简单的方式，避免环境配置问题
2. **定期备份数据** - 使用 `docker compose exec postgres pg_dump` 备份数据库
3. **查看日志** - 遇到问题首先查看 `docker compose logs`
4. **使用启动脚本** - `docker-start.sh` 或 `docker-start.bat` 简化操作

### 生产环境建议

1. **修改默认密码** - 必须修改所有默认密码
2. **配置HTTPS** - 使用Nginx反向代理并配置SSL证书
3. **定期更新** - 定期更新依赖和Docker镜像
4. **监控服务** - 配置Prometheus和Grafana监控
5. **备份策略** - 配置自动备份和异地存储

### 性能优化

1. **资源限制** - 在docker-compose.yml中配置CPU和内存限制
2. **日志管理** - 配置日志轮转，避免磁盘空间耗尽
3. **缓存配置** - 合理配置Redis缓存策略
4. **数据库优化** - 定期优化数据库索引和查询

---

## 🆘 获取帮助

如果遇到问题：

1. **查看日志** - `docker compose logs -f`
2. **检查文档** - 阅读上述相关文档
3. **搜索Issues** - 在GitHub搜索类似问题
4. **提交Issue** - 描述问题并提供日志信息
5. **社区支持** - 加入社区讨论

---

**祝你使用愉快！** 🎉

如有任何问题，请查阅文档或提交Issue反馈。
