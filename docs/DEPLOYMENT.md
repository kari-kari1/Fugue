# Fugue 部署指南

本指南将帮助你将 Fugue 部署到生产环境。

## 📋 目录

- [部署选项](#部署选项)
- [前置要求](#前置要求)
- [Docker 部署（推荐）](#docker-部署推荐)
- [手动部署](#手动部署)
- [云平台部署](#云平台部署)
- [生产环境配置](#生产环境配置)
- [监控和日志](#监控和日志)
- [备份和恢复](#备份和恢复)
- [性能优化](#性能优化)
- [安全加固](#安全加固)
- [故障排除](#故障排除)

## 部署选项

### 1. Docker Compose（推荐）

最简单的部署方式，适合小型到中型团队。

**优点**：
- ✅ 一键部署
- ✅ 环境隔离
- ✅ 易于升级和回滚
- ✅ 资源可控

**适用场景**：
- 小型团队（< 50人）
- 内部使用
- 开发/测试环境

### 2. Kubernetes

适合大规模部署和高可用需求。

**优点**：
- ✅ 高可用
- ✅ 自动扩缩容
- ✅ 滚动更新
- ✅ 服务发现和负载均衡

**适用场景**：
- 大型团队
- 生产环境
- 需要高可用

### 3. 云平台托管

使用云服务商的托管服务。

**优点**：
- ✅ 无需运维
- ✅ 自动备份
- ✅ 内置监控
- ✅ 按需付费

**适用场景**：
- 不想自己运维
- 预算充足
- 快速上线

## 前置要求

### 硬件要求

**最低配置**（开发/测试）：
- CPU: 2 核
- 内存: 4 GB
- 磁盘: 20 GB SSD

**推荐配置**（生产环境）：
- CPU: 4 核
- 内存: 8 GB
- 磁盘: 50 GB SSD

**高并发配置**：
- CPU: 8+ 核
- 内存: 16+ GB
- 磁盘: 100+ GB SSD

### 软件要求

- **操作系统**：Linux（推荐 Ubuntu 22.04 / Debian 12）
- **Docker**：24.0+
- **Docker Compose**：v2
- **域名**（可选）：用于生产环境
- **SSL证书**（推荐）：Let's Encrypt 免费证书

### 网络要求

**必需端口**：
- `80/443`: Web 访问
- `8000`: 后端 API（可选，通过 Nginx 代理）
- `3000`: 前端（可选，通过 Nginx 代理）
- `5432`: PostgreSQL（仅内部访问）
- `6379`: Redis（仅内部访问）

**防火墙规则**：
```bash
# 允许 HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 禁止外部访问数据库端口
sudo ufw deny 5432/tcp
sudo ufw deny 6379/tcp
```

## Docker 部署（推荐）

### 步骤 1: 准备服务器

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 将当前用户添加到 docker 组
sudo usermod -aG docker $USER

# 重新登录以使权限生效
# 或运行: newgrp docker

# 验证 Docker 安装
docker --version
docker compose version
```

### 步骤 2: 获取项目

```bash
# 克隆项目
git clone https://github.com/yourusername/fugue.git
cd fugue

# 或者上传项目文件
scp -r ./fugue user@server:/opt/
ssh user@server
cd /opt/fugue
```

### 步骤 3: 配置环境

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件
nano .env
```

**必须修改的配置**：

```bash
# 安全密钥（必须修改！）
SECRET_KEY=<使用 openssl rand -hex 32 生成>

# 数据库密码（必须修改！）
POSTGRES_PASSWORD=<强密码>

# Redis密码（必须修改！）
REDIS_PASSWORD=<强密码>

# MinIO密码（必须修改！）
MINIO_PASSWORD=<强密码>

# 环境
ENVIRONMENT=production
```

**生成安全密钥**：

```bash
# 生成 SECRET_KEY
openssl rand -hex 32

# 生成数据库密码
openssl rand -base64 32

# 生成 Redis 密码
openssl rand -base64 24
```

### 步骤 4: 启动服务

```bash
# 启动生产环境
docker compose --profile production up -d --build

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f
```

### 步骤 5: 初始化数据

```bash
# 运行数据库迁移
docker compose exec backend alembic upgrade head

# 初始化管理员账号和演示数据
docker compose exec backend python init_data.py
```

### 步骤 6: 验证部署

```bash
# 检查后端健康状态
curl http://localhost:8000/health

# 检查前端
curl http://localhost:3000

# 查看 API 文档
# 访问 http://your-server:8000/docs
```

### 步骤 7: 配置 Nginx 反向代理（推荐）

创建 Nginx 配置文件：

```bash
sudo nano /etc/nginx/sites-available/fugue
```

配置内容：

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 替换为你的域名

    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL 证书（使用 Let's Encrypt）
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # SSL 配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 前端
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # 后端 API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket（用于实时监控）
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }

    # API 文档
    location /docs {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
    }

    location /redoc {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
    }
}
```

启用配置：

```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/fugue /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

### 步骤 8: 配置 SSL 证书（推荐）

使用 Let's Encrypt 免费证书：

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx -y

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期测试
sudo certbot renew --dry-run
```

## 手动部署

如果不使用 Docker，可以手动部署。

### 步骤 1: 安装依赖

```bash
# 安装 Python
sudo apt install python3.12 python3.12-venv python3-pip -y

# 安装 Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs -y

# 安装 PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# 安装 Redis
sudo apt install redis-server -y
```

### 步骤 2: 配置数据库

```bash
# 切换到 postgres 用户
sudo -u postgres psql

# 创建数据库和用户
CREATE DATABASE fugue;
CREATE USER fugue WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE fugue TO fugue;
\q
```

### 步骤 3: 部署后端

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
nano .env  # 编辑配置

# 运行迁移
alembic upgrade head

# 启动服务（使用 Gunicorn）
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### 步骤 4: 部署前端

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 构建生产版本
npm run build

# 使用 Nginx 托管静态文件
sudo cp -r dist/* /var/www/html/
```

### 步骤 5: 配置 Systemd 服务

创建后端服务文件：

```bash
sudo nano /etc/systemd/system/fugue-backend.service
```

内容：

```ini
[Unit]
Description=Fugue Backend
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/fugue/backend
Environment="PATH=/opt/fugue/backend/venv/bin"
ExecStart=/opt/fugue/backend/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable fugue-backend
sudo systemctl start fugue-backend
sudo systemctl status fugue-backend
```

## 生产环境配置

### 环境变量配置

**必要的环境变量**：

```bash
# 安全配置
SECRET_KEY=<随机生成的强密钥>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 数据库
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/fugue
DATABASE_URL_SYNC=postgresql://user:password@localhost:5432/fugue

# Redis
REDIS_URL=redis://:password@localhost:6379/0
CELERY_BROKER_URL=redis://:password@localhost:6379/1

# 环境
ENVIRONMENT=production
DEBUG=false

# CORS（生产环境限制来源）
CORS_ORIGINS=["https://your-domain.com"]
```

### 数据库优化

**PostgreSQL 配置优化**（`/etc/postgresql/16/main/postgresql.conf`）：

```ini
# 内存配置
shared_buffers = 2GB  # 25% of RAM
effective_cache_size = 6GB  # 75% of RAM
work_mem = 16MB
maintenance_work_mem = 512MB

# 连接配置
max_connections = 200

# WAL 配置
wal_buffers = 64MB
checkpoint_completion_target = 0.9

# 查询优化
random_page_cost = 1.1  # SSD
effective_io_concurrency = 200  # SSD
```

**应用配置后重启**：

```bash
sudo systemctl restart postgresql
```

### Redis 配置优化

编辑 `/etc/redis/redis.conf`：

```ini
# 内存配置
maxmemory 2gb
maxmemory-policy allkeys-lru

# 持久化
appendonly yes
appendfsync everysec

# 安全
requirepass your_strong_password
```

重启 Redis：

```bash
sudo systemctl restart redis-server
```

## 监控和日志

### 应用监控

**健康检查端点**：

```bash
# 后端健康检查
curl http://localhost:8000/health

# 详细健康信息
curl http://localhost:8000/health/detailed
```

**Prometheus 指标**（如果启用）：

```bash
curl http://localhost:8000/metrics
```

### 日志管理

**Docker 日志**：

```bash
# 查看实时日志
docker compose logs -f backend

# 查看特定服务的日志
docker compose logs --tail=100 backend

# 日志文件位置
/var/lib/docker/containers/<container-id>/<container-id>-json.log
```

**配置日志轮转**（`/etc/docker/daemon.json`）：

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

**集中式日志（推荐）**：

使用 ELK Stack 或 Loki：

```yaml
# docker-compose.yml 添加
services:
  # ... 其他服务 ...

  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"

  promtail:
    image: grafana/promtail:latest
    volumes:
      - /var/log:/var/log
      - ./promtail-config.yml:/etc/promtail/config.yml
```

### 告警配置

使用 Prometheus Alertmanager 或 Grafana 告警：

```yaml
# alertmanager.yml
route:
  receiver: 'email-alert'
  group_by: ['alertname', 'job']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h

receivers:
  - name: 'email-alert'
    email_configs:
      - to: 'admin@your-domain.com'
        from: 'alertmanager@your-domain.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'your-email@gmail.com'
        auth_password: 'your-app-password'
```

## 备份和恢复

### 数据库备份

**自动备份脚本**：

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/opt/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/fugue_$DATE.sql.gz"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 执行备份
docker compose exec -T postgres pg_dump -U postgres fugue | gzip > $BACKUP_FILE

# 保留最近30天的备份
find $BACKUP_DIR -name "fugue_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE"
```

**添加定时任务**：

```bash
# 每天凌晨2点备份
0 2 * * * /opt/fugue/scripts/backup.sh >> /var/log/fugue-backup.log 2>&1
```

### 数据库恢复

```bash
# 停止服务
docker compose down

# 恢复数据库
gunzip < /opt/backups/postgres/fugue_20240101_020000.sql.gz | docker compose exec -T postgres psql -U postgres fugue

# 启动服务
docker compose up -d
```

### Redis 备份

```bash
# Redis 自动备份（RDB）
# 配置在 redis.conf 中
save 900 1
save 300 10
save 60 10000

# 手动触发备份
docker compose exec redis redis-cli BGSAVE

# 备份文件位置
docker compose exec redis ls /data/dump.rdb
```

### MinIO 备份

```bash
# 使用 mc 工具备份
mc alias set fugue http://localhost:9000 minioadmin minioadmin
mc mirror fugue/data /opt/backups/minio/
```

### 完整备份脚本

```bash
#!/bin/bash
# full-backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_ROOT="/opt/backups/fugue/$DATE"

mkdir -p $BACKUP_ROOT/{postgres,redis,minio}

# 备份 PostgreSQL
docker compose exec -T postgres pg_dump -U postgres fugue | gzip > $BACKUP_ROOT/postgres/fugue.sql.gz

# 备份 Redis
docker compose exec redis redis-cli BGSAVE
sleep 5
docker compose cp redis:/data/dump.rdb $BACKUP_ROOT/redis/

# 备份 MinIO
mc alias set fugue http://localhost:9000 minioadmin minioadmin
mc mirror fugue/data $BACKUP_ROOT/minio/

# 备份配置文件
cp .env $BACKUP_ROOT/
cp docker-compose.yml $BACKUP_ROOT/

# 压缩
tar -czf /opt/backups/fugue_$DATE.tar.gz -C /opt/backups/fugue $DATE
rm -rf /opt/backups/fugue/$DATE

echo "Full backup completed: /opt/backups/fugue_$DATE.tar.gz"
```

## 性能优化

### 应用层优化

**Gunicorn 配置**：

```bash
# 根据 CPU 核心数调整 worker 数量
gunicorn app.main:app \
  -w 4 \  # 通常 2 * CPU核心数 + 1
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --keep-alive 5 \
  --max-requests 1000 \
  --max-requests-jitter 50
```

**连接池配置**：

```python
# backend/app/core/database.py
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,  # 连接池大小
    max_overflow=10,  # 超出pool_size后最多可创建的连接数
    pool_timeout=30,  # 获取连接的超时时间
    pool_recycle=1800,  # 连接回收时间（秒）
    pool_pre_ping=True,  # 使用前ping一下检测连接是否有效
)
```

### Nginx 优化

```nginx
# /etc/nginx/nginx.conf

worker_processes auto;
worker_rlimit_nofile 65535;

events {
    worker_connections 4096;
    multi_accept on;
    use epoll;
}

http {
    # 开启 gzip
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # 缓存配置
    proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m max_size=10g inactive=60m use_temp_path=off;

    # 静态文件缓存
    location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 数据库查询优化

```python
# 使用索引
# backend/app/models/crew.py
class Crew(Base):
    __tablename__ = "crews"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)  # 添加索引
    name = Column(String, index=True)  # 常用查询字段添加索引
    created_at = Column(DateTime, index=True)  # 时间字段添加索引
```

```python
# 使用 selectinload 避免 N+1 查询
from sqlalchemy.orm import selectinload

async def get_crews_with_agents(db: AsyncSession, user_id: str):
    result = await db.execute(
        select(Crew)
        .where(Crew.user_id == user_id)
        .options(selectinload(Crew.agents))  # 预加载 agents
        .options(selectinload(Crew.tasks))   # 预加载 tasks
    )
    return result.scalars().all()
```

## 安全加固

### 系统安全

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 配置防火墙
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 禁止 root 登录
sudo nano /etc/ssh/sshd_config
# PermitRootLogin no

# 重启 SSH
sudo systemctl restart sshd
```

### 应用安全

**环境变量安全**：

```bash
# .env 文件权限
chmod 600 .env
chown root:root .env

# 不要提交 .env 到 Git
echo ".env" >> .gitignore
```

**Docker 安全**：

```yaml
# docker-compose.yml
services:
  backend:
    # 不要以 root 运行
    user: "1000:1000"

    # 只读文件系统（如果可能）
    read_only: true

    # 限制资源
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

    # 安全选项
    security_opt:
      - no-new-privileges:true
```

**API 安全**：

```python
# backend/app/main.py
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# CORS 配置（生产环境严格限制）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],  # 只允许你的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted Host
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["your-domain.com", "*.your-domain.com"],
)
```

**Rate Limiting**：

```python
# 使用 slowapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/v1/auth/login")
@limiter.limit("5/minute")  # 每分钟最多5次
async def login(request: Request, ...):
    ...
```

## 故障排除

### 常见问题

**1. 服务无法启动**

```bash
# 查看日志
docker compose logs backend

# 检查端口占用
sudo lsof -i :8000

# 检查数据库连接
docker compose exec backend python -c "from app.core.database import engine; print(engine)"
```

**2. 数据库连接失败**

```bash
# 检查 PostgreSQL 状态
docker compose exec postgres pg_isready

# 检查数据库是否存在
docker compose exec postgres psql -U postgres -l

# 检查连接参数
docker compose exec backend env | grep DATABASE
```

**3. 内存不足**

```bash
# 查看内存使用
docker stats

# 减少 worker 数量
# 编辑 docker-compose.yml
command: gunicorn app.main:app -w 2 -k uvicorn.workers.UvicornWorker

# 或添加 swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

**4. 磁盘空间不足**

```bash
# 查看磁盘使用
df -h

# 清理 Docker
docker system prune -a

# 清理日志
sudo journalctl --vacuum-time=7d
```

### 获取帮助

如果问题仍未解决：

1. 查看 GitHub Issues
2. 搜索错误信息
3. 提交新的 Issue（包含日志和环境信息）

---

## 更新和维护

### 更新应用

```bash
# 拉取最新代码
git pull origin main

# 重新构建并启动
docker compose --profile production up -d --build

# 运行迁移
docker compose exec backend alembic upgrade head
```

### 回滚版本

```bash
# 查看历史版本
git log --oneline

# 回滚到特定版本
git checkout <commit-hash>

# 重新部署
docker compose --profile production up -d --build
```

---

**部署完成！** 🎉

如有问题，请查看 [故障排除](#故障排除) 部分或提交 Issue。
