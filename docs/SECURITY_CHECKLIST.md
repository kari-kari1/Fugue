# Fugue 安全检查清单

本清单帮助你在部署和维护 Fugue 时确保安全性。

## 📋 目录

- [部署前安全检查](#部署前安全检查)
- [运行时安全配置](#运行时安全配置)
- [数据安全](#数据安全)
- [网络安全](#网络安全)
- [监控和审计](#监控和审计)
- [应急响应](#应急响应)
- [定期安全审查](#定期安全审查)

---

## 部署前安全检查

### 1. 环境变量安全 ✅

- [ ] **SECRET_KEY**
  - [ ] 使用强随机密钥（至少32字节）
  - [ ] 不使用默认值
  - [ ] 仅在服务器环境变量中设置，不提交到代码库
  ```bash
  # 生成安全密钥
  openssl rand -hex 32
  ```

- [ ] **数据库密码**
  - [ ] 使用强密码（至少16字符，包含大小写字母、数字、特殊字符）
  - [ ] 不使用默认密码
  - [ ] 不同环境使用不同密码

- [ ] **API密钥**
  - [ ] LLM API密钥妥善保管
  - [ ] 不在代码或配置文件中硬编码
  - [ ] 使用环境变量或密钥管理服务

- [ ] **.env文件**
  - [ ] 已添加到.gitignore
  - [ ] 文件权限设置为600
  ```bash
  chmod 600 .env
  ```

### 2. 依赖安全 ✅

- [ ] **Python依赖**
  ```bash
  # 检查已知漏洞
  pip audit
  
  # 或使用 safety
  pip install safety
  safety check
  ```

- [ ] **Node.js依赖**
  ```bash
  cd frontend
  npm audit
  npm audit fix
  ```

- [ ] **Docker镜像**
  - [ ] 使用官方镜像
  - [ ] 定期更新镜像版本
  - [ ] 扫描镜像漏洞
  ```bash
  # 使用 Trivy 扫描
  trivy image fugue-backend:latest
  ```

### 3. 配置文件安全 ✅

- [ ] **docker-compose.yml**
  - [ ] 不暴露不必要的端口
  - [ ] 使用环境变量而非硬编码密码
  - [ ] 配置健康检查

- [ ] **Nginx配置**（如使用）
  - [ ] 隐藏版本信息
  - [ ] 配置安全头
  - [ ] 限制请求大小

---

## 运行时安全配置

### 1. 认证和授权 ✅

- [ ] **JWT配置**
  - [ ] Token过期时间合理（建议24小时）
  - [ ] 使用HTTPS传输Token
  - [ ] 实现Token刷新机制
  ```python
  # backend/app/core/config.py
  ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24小时
  ALGORITHM = "HS256"
  ```

- [ ] **密码安全**
  - [ ] 使用bcrypt或argon2哈希
  - [ ] 密码强度验证
  - [ ] 登录失败限制
  ```python
  # backend/app/core/security.py
  from passlib.context import CryptContext
  pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
  ```

- [ ] **权限控制**
  - [ ] 实现基于角色的访问控制（RBAC）
  - [ ] 验证用户资源所有权
  - [ ] 限制敏感操作权限

### 2. 输入验证 ✅

- [ ] **API输入验证**
  - [ ] 使用Pydantic进行数据验证
  - [ ] 验证所有用户输入
  - [ ] 防止SQL注入（使用ORM）
  ```python
  # backend/app/schemas/crew.py
  from pydantic import BaseModel, Field
  
  class CrewCreate(BaseModel):
      name: str = Field(..., min_length=1, max_length=100)
      description: Optional[str] = Field(None, max_length=1000)
  ```

- [ ] **文件上传安全**
  - [ ] 验证文件类型
  - [ ] 限制文件大小
  - [ ] 扫描恶意内容
  - [ ] 使用安全的文件名

### 3. 错误处理 ✅

- [ ] **错误信息**
  - [ ] 生产环境不暴露详细错误
  - [ ] 记录错误日志
  - [ ] 返回通用错误消息
  ```python
  # backend/app/main.py
  @app.exception_handler(Exception)
  async def global_exception_handler(request, exc):
      logger.error(f"Unhandled exception: {exc}", exc_info=True)
      return JSONResponse(
          status_code=500,
          content={"detail": "Internal server error"}
      )
  ```

### 4. CORS配置 ✅

- [ ] **CORS策略**
  - [ ] 生产环境限制允许的源
  - [ ] 不使用通配符 `*`
  - [ ] 配置正确的HTTP方法
  ```python
  # backend/app/main.py
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["https://your-domain.com"],  # 生产环境
      allow_credentials=True,
      allow_methods=["GET", "POST", "PUT", "DELETE"],
      allow_headers=["*"],
  )
  ```

---

## 数据安全

### 1. 数据库安全 ✅

- [ ] **PostgreSQL配置**
  - [ ] 使用强密码
  - [ ] 限制远程访问
  - [ ] 启用SSL连接
  - [ ] 定期备份
  ```bash
  # PostgreSQL SSL配置
  ssl = on
  ssl_cert_file = 'server.crt'
  ssl_key_file = 'server.key'
  ```

- [ ] **数据加密**
  - [ ] 敏感字段加密存储
  - [ ] 使用加密连接
  - [ ] API密钥加密存储
  ```python
  # backend/app/core/security.py
  from cryptography.fernet import Fernet
  
  def encrypt_api_key(key: str, master_key: bytes) -> str:
      f = Fernet(master_key)
      return f.encrypt(key.encode()).decode()
  ```

### 2. 文件存储安全 ✅

- [ ] **MinIO配置**
  - [ ] 使用强密码
  - [ ] 配置访问策略
  - [ ] 启用HTTPS
  - [ ] 限制桶权限

- [ ] **文件访问**
  - [ ] 验证用户权限
  - [ ] 使用预签名URL
  - [ ] 设置过期时间

### 3. 备份安全 ✅

- [ ] **备份策略**
  - [ ] 定期自动备份
  - [ ] 备份文件加密
  - [ ] 异地存储备份
  - [ ] 定期测试恢复

```bash
# 加密备份示例
docker compose exec -T postgres pg_dump -U postgres fugue | \
  gzip | \
  gpg --encrypt --recipient your@email.com > backup.sql.gz.gpg
```

---

## 网络安全

### 1. 防火墙配置 ✅

- [ ] **端口管理**
  - [ ] 仅开放必要端口
  - [ ] 数据库端口不对外暴露
  - [ ] 使用非标准端口（可选）
  ```bash
  # UFW 防火墙配置
  ufw default deny incoming
  ufw default allow outgoing
  ufw allow ssh
  ufw allow 80/tcp
  ufw allow 443/tcp
  # 不开放 5432, 6379, 9000 等内部端口
  ufw enable
  ```

### 2. HTTPS配置 ✅

- [ ] **SSL/TLS**
  - [ ] 使用有效证书
  - [ ] 强制HTTPS重定向
  - [ ] 配置HSTS
  - [ ] 禁用弱加密套件

```nginx
# Nginx SSL配置
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;

# HSTS
add_header Strict-Transport-Security "max-age=63072000" always;
```

### 3. DDoS防护 ✅

- [ ] **限流配置**
  - [ ] API限流
  - [ ] 登录限流
  - [ ] IP限制（可选）

```python
# 使用 slowapi
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/auth/login")
@limiter.limit("5/minute")
async def login(...):
    ...
```

---

## 监控和审计

### 1. 日志记录 ✅

- [ ] **应用日志**
  - [ ] 记录所有认证事件
  - [ ] 记录敏感操作
  - [ ] 记录错误和异常
  - [ ] 日志不包含敏感信息

```python
# backend/app/core/logging.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fugue.log'),
        logging.StreamHandler()
    ]
)
```

- [ ] **访问日志**
  - [ ] 记录所有API请求
  - [ ] 记录IP地址
  - [ ] 记录用户代理

### 2. 安全监控 ✅

- [ ] **异常检测**
  - [ ] 监控失败登录尝试
  - [ ] 检测异常访问模式
  - [ ] 设置告警阈值

- [ ] **监控工具**
  - [ ] 配置Prometheus指标
  - [ ] 设置Grafana仪表板
  - [ ] 配置告警规则

```yaml
# Prometheus告警规则示例
groups:
  - name: fugue
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: High error rate detected
```

### 3. 审计日志 ✅

- [ ] **审计事件**
  - [ ] 用户登录/登出
  - [ ] 资源创建/修改/删除
  - [ ] 权限变更
  - [ ] 系统配置变更

```python
# backend/app/services/audit.py
from datetime import datetime

async def log_audit_event(
    db: AsyncSession,
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    details: dict = None
):
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        timestamp=datetime.utcnow()
    )
    db.add(audit_log)
    await db.commit()
```

---

## 应急响应

### 1. 安全事件响应流程

```
1. 检测
   - 监控告警
   - 用户报告
   - 日志分析

2. 评估
   - 确定影响范围
   - 评估严重程度
   - 收集证据

3. 响应
   - 隔离受影响系统
   - 阻止攻击继续
   - 通知相关人员

4. 恢复
   - 修复漏洞
   - 恢复服务
   - 验证修复

5. 总结
   - 事后分析
   - 更新流程
   - 改进防护
```

### 2. 常见安全事件处理

**暴力破解攻击**：
```bash
# 1. 查看攻击IP
grep "Failed password" /var/log/auth.log | awk '{print $11}' | sort | uniq -c | sort -rn

# 2. 封锁IP
sudo ufw deny from <attacker_ip>

# 3. 启用fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

**数据泄露响应**：
1. 立即修改所有相关密码
2. 撤销泄露的API密钥
3. 通知受影响的用户
4. 审计日志，确定泄露范围
5. 修复漏洞
6. 发布安全公告

### 3. 联系方式

- **安全团队邮箱**: security@fugue.com
- **紧急联系电话**: +86-xxx-xxxx-xxxx
- **GitHub Security**: 使用GitHub的私密漏洞报告功能

---

## 定期安全审查

### 每周检查 ✅

- [ ] 查看系统日志，检查异常活动
- [ ] 验证备份完整性
- [ ] 检查磁盘空间和系统资源
- [ ] 更新安全补丁

### 每月检查 ✅

- [ ] 审查用户权限，移除不必要的账号
- [ ] 轮换API密钥和密码
- [ ] 运行安全扫描工具
- [ ] 审查防火墙规则
- [ ] 测试备份恢复流程

### 每季度检查 ✅

- [ ] 完整的安全审计
- [ ] 渗透测试（可选）
- [ ] 依赖漏洞扫描
- [ ] 安全策略审查
- [ ] 员工安全培训

### 年度检查 ✅

- [ ] 全面安全评估
- [ ] 合规性审查
- [ ] 灾难恢复演练
- [ ] 安全架构审查

---

## 安全工具推荐

### 1. 漏洞扫描

```bash
# Python依赖扫描
pip install safety
safety check

# Docker镜像扫描
trivy image fugue-backend:latest

# Web应用扫描
nikto -h http://localhost:8000
```

### 2. 密钥管理

- **HashiCorp Vault**: 企业级密钥管理
- **AWS Secrets Manager**: 云原生密钥管理
- **Docker Secrets**: Docker Swarm密钥管理

### 3. 监控工具

- **Prometheus + Grafana**: 指标监控和可视化
- **ELK Stack**: 日志收集和分析
- **Sentry**: 错误追踪

---

## 安全资源

### 官方文档

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Docker Security](https://docs.docker.com/engine/security/)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/auth-pg-hba-conf.html)

### 安全最佳实践

- [CWE/SANS Top 25](https://cwe.mitre.org/top25/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

---

## 检查清单总结

### 部署前 ✅

- [ ] 所有默认密码已修改
- [ ] SECRET_KEY已设置为强随机值
- [ ] .env文件已添加到.gitignore
- [ ] 依赖漏洞已扫描和修复
- [ ] Docker镜像已扫描

### 运行时 ✅

- [ ] HTTPS已启用
- [ ] CORS已正确配置
- [ ] 输入验证已实现
- [ ] 错误处理已配置
- [ ] 限流已启用

### 数据安全 ✅

- [ ] 数据库访问受限
- [ ] 敏感数据已加密
- [ ] 备份已加密存储
- [ ] 访问控制已实现

### 监控审计 ✅

- [ ] 日志已配置
- [ ] 监控已启用
- [ ] 告警已设置
- [ ] 审计日志已记录

---

**安全是一个持续的过程，不是一次性的任务。定期审查和更新安全措施至关重要。**

如有安全问题或发现漏洞，请通过安全渠道联系我们。
