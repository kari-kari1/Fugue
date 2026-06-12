# Fugue 快速开始指南

欢迎使用 Fugue！本指南将帮助你在5分钟内启动并运行 Fugue。

## 📋 前置要求

在开始之前，请确保你的系统满足以下要求：

### 必需软件

- **Docker** 24.0 或更高版本
- **Docker Compose** v2
- **Git**（用于克隆项目）

### 可选软件（本地开发需要）

- **Python** 3.12+
- **Node.js** 20+ 和 npm
- **PostgreSQL** 16
- **Redis** 7

## 🚀 5分钟快速启动

### 步骤 1: 获取项目

```bash
# 克隆项目（如果使用Git）
git clone https://github.com/yourusername/fugue.git
cd fugue

# 或者直接进入项目目录
cd E:\fugue
```

### 步骤 2: 一键启动

**Windows 用户：**

```cmd
docker-start.bat start
```

**Linux/macOS 用户：**

```bash
chmod +x docker-start.sh
./docker-start.sh start
```

启动过程大约需要2-3分钟，脚本会：
- ✅ 检查 Docker 环境
- ✅ 创建配置文件
- ✅ 拉取并启动所有服务
- ✅ 运行数据库迁移
- ✅ 初始化演示数据

### 步骤 3: 访问应用

启动完成后，你会看到类似这样的输出：

```
================================
📊 服务状态
================================
NAME                    STATUS      PORTS
fugue-backend      running     0.0.0.0:8000->8000/tcp
fugue-frontend     running     0.0.0.0:3000->3000/tcp
fugue-postgres     running     0.0.0.0:5432->5432/tcp
fugue-redis        running     0.0.0.0:6379->6379/tcp
fugue-minio        running     0.0.0.0:9000-9001->9000-9001/tcp

================================
🌐 访问地址
================================
前端界面: http://localhost:3000
后端API: http://localhost:8000
API文档: http://localhost:8000/docs
MinIO控制台: http://localhost:9001

================================
📝 演示账号
================================
邮箱: demo@fugue.com
密码: Demo123456
```

### 步骤 4: 登录并探索

1. **打开浏览器**，访问 http://localhost:3000
2. **使用演示账号登录**：
   - 邮箱：`demo@fugue.com`
   - 密码：`Demo123456`
3. **探索功能**：
   - 查看工作流列表
   - 创建新的工作流
   - 浏览模板市场
   - 运行一个工作流

## 🎯 第一个工作流

让我们创建你的第一个多Agent工作流：

### 方法一：使用模板（推荐）

1. 登录后，点击 **"浏览模板"**
2. 选择 **"行业研究报告生成"** 模板
3. 点击 **"使用此模板"**
4. 系统会自动创建一个包含2个Agent和3个Task的工作流
5. 点击 **"运行"** 开始执行
6. 在执行监控页面观察Agent的实时思考过程

### 方法二：从零创建

1. 登录后，点击 **"新建工作流"**
2. 在画布中拖拽创建：
   - 2个 **Agent节点**（研究员、写手）
   - 2个 **Task节点**（数据收集、报告撰写）
3. 配置每个Agent的：
   - 名称和角色
   - 使用的LLM模型
   - 可用工具
4. 配置每个Task的：
   - 任务描述
   - 期望输出
   - 执行的Agent
5. 连接Task节点建立依赖关系
6. 点击 **"运行"** 执行

## 🔧 常用操作

### 查看日志

```bash
# 查看后端日志
docker-start.bat logs backend
./docker-start.sh logs backend

# 查看所有服务日志
docker compose logs -f
```

### 停止服务

```bash
docker-start.bat stop
./docker-start.sh stop
```

### 重启服务

```bash
docker-start.bat restart
./docker-start.sh restart
```

### 更新代码后重建

```bash
docker-start.bat rebuild
./docker-start.sh rebuild
```

## ❓ 常见问题

### Q: 启动失败怎么办？

**A:** 按以下步骤排查：

1. 检查 Docker 是否运行：
   ```bash
   docker --version
   docker compose version
   ```

2. 检查端口是否被占用：
   ```bash
   # Windows
   netstat -ano | findstr :8000
   netstat -ano | findstr :3000

   # Linux/macOS
   lsof -i :8000
   lsof -i :3000
   ```

3. 查看详细日志：
   ```bash
   docker compose logs backend
   ```

4. 尝试清理并重新启动：
   ```bash
   docker-start.bat cleanup
   docker-start.bat start
   ```

### Q: 忘记了演示账号密码？

**A:** 默认凭证：
- 邮箱：`demo@fugue.com`
- 密码：`Demo123456`

### Q: 如何配置自己的LLM API Key？

**A:** 两种方式：

1. **通过界面配置**（推荐）：
   - 登录后进入"设置"页面
   - 找到"API密钥"配置
   - 添加你的OpenAI/Anthropic/Google API Key

2. **通过环境变量**：
   - 编辑 `.env` 文件
   - 添加：
     ```
     OPENAI_API_KEY=sk-your-key-here
     ANTHROPIC_API_KEY=sk-ant-your-key-here
     ```
   - 重启服务

### Q: 如何查看API文档？

**A:** 访问以下地址：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Q: 数据存储在哪里？

**A:** 
- **PostgreSQL**：存储用户、工作流、Agent、Task等结构化数据
- **Redis**：缓存和Celery任务队列
- **MinIO**：文件存储（上传的文档、生成的报告）

数据卷位置：
```bash
# 查看数据卷
docker volume ls | grep fugue

# 数据卷位置（Linux）
/var/lib/docker/volumes/fugue_postgres_data/
/var/lib/docker/volumes/fugue_redis_data/
/var/lib/docker/volumes/fugue_minio_data/
```

## 📚 下一步

现在你已经成功启动了 Fugue，可以继续：

1. 📖 阅读 [项目计划书](../项目计划书_Fugue.md) 了解完整的功能规划
2. 🔍 探索 [API文档](http://localhost:8000/docs) 了解所有可用接口
3. 🧪 运行测试套件验证安装：
   ```bash
   ./run_tests.sh
   ```
4. 💡 查看 `docs/superpowers/` 目录了解开发规范
5. 🤝 参与贡献：阅读 [CONTRIBUTING.md](../CONTRIBUTING.md)

## 🆘 获取帮助

如果遇到问题：

1. 查看 [常见问题](#-常见问题) 部分
2. 搜索 [GitHub Issues](https://github.com/yourusername/fugue/issues)
3. 提交新的 Issue 描述你的问题
4. 加入社区讨论

---

**祝你使用愉快！** 🎉

如有任何问题或建议，欢迎反馈。
