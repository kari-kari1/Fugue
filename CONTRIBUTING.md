# 贡献指南

感谢你对 Fugue 项目的关注！我们欢迎各种形式的贡献，包括但不限于：

- 🐛 报告 Bug
- 💡 提出新功能建议
- 📝 改进文档
- 🔧 提交代码修复
- ✨ 开发新功能
- 🧪 编写测试
- 🌍 翻译和本地化

## 📋 目录

- [开始之前](#开始之前)
- [开发环境搭建](#开发环境搭建)
- [贡献流程](#贡献流程)
- [代码规范](#代码规范)
- [提交规范](#提交规范)
- [Pull Request 规范](#pull-request-规范)
- [报告 Bug](#报告-bug)
- [请求新功能](#请求新功能)
- [社区行为准则](#社区行为准则)

## 开始之前

### 了解项目

在开始贡献之前，建议你：

1. 阅读 [README.md](README.md) 了解项目概况
2. 阅读 [项目计划书](项目计划书_Fugue.md) 了解功能规划
3. 查看 [快速开始指南](docs/QUICK_START.md) 体验产品
4. 浏览 [现有 Issues](https://github.com/yourusername/fugue/issues) 了解待解决的问题

### 选择贡献方式

根据你的兴趣和技能，可以选择：

- **Good First Issues**：适合新贡献者的简单任务
- **Bug Reports**：帮助我们发现问题
- **Documentation**：改进文档和教程
- **Features**：开发新功能
- **Tests**：增加测试覆盖率

## 开发环境搭建

### 前置要求

- Python 3.12+
- Node.js 20+
- Docker 和 Docker Compose
- Git

### 搭建步骤

1. **Fork 项目**

   点击项目右上角的 "Fork" 按钮，将项目复制到你的 GitHub 账号。

2. **克隆到本地**

   ```bash
   git clone https://github.com/YOUR_USERNAME/fugue.git
   cd fugue
   ```

3. **添加上游仓库**

   ```bash
   git remote add upstream https://github.com/ORIGINAL_USERNAME/fugue.git
   ```

4. **启动开发环境**

   ```bash
   # 使用Docker启动（推荐）
   ./docker-start.sh start

   # 或者本地启动
   # 参考 README.md 的本地开发部分
   ```

5. **创建开发分支**

   ```bash
   git checkout -b feature/your-feature-name
   ```

## 贡献流程

### 1. 选择或创建 Issue

- 查看 [Issues](https://github.com/yourusername/fugue/issues) 寻找感兴趣的任务
- 如果没有相关 Issue，先创建一个描述你的想法
- 等待维护者确认后再开始编码

### 2. 开发

```bash
# 确保在最新的main分支
git checkout main
git pull upstream main

# 创建特性分支
git checkout -b feature/your-feature

# 进行开发...
# 编写代码
# 编写测试
# 更新文档（如需要）
```

### 3. 测试

```bash
# 运行所有测试
./run_tests.sh

# 或者分别运行
cd backend && pytest tests/ -v
cd frontend && npm run test
```

确保所有测试通过，没有引入新的问题。

### 4. 代码检查

```bash
# 后端
cd backend
ruff check .
mypy app/

# 前端
cd frontend
npm run lint
```

### 5. 提交

```bash
# 添加修改的文件
git add <changed-files>

# 提交（遵循提交规范）
git commit -m "feat: add amazing feature"

# 推送到你的 Fork
git push origin feature/your-feature
```

### 6. 创建 Pull Request

1. 访问你的 Fork 页面
2. 点击 "Compare & pull request"
3. 填写 PR 模板（见下方规范）
4. 等待代码审查
5. 根据反馈修改代码
6. 维护者合并后完成！

## 代码规范

### Python（后端）

- 遵循 [PEP 8](https://peps.python.org/pep-0008/) 规范
- 使用类型注解（Type Hints）
- 使用 `ruff` 进行代码格式化和检查
- 使用 `mypy` 进行类型检查

```bash
# 格式化代码
ruff format .

# 检查代码
ruff check .

# 类型检查
mypy app/
```

### TypeScript（前端）

- 遵循项目 ESLint 配置
- 使用 TypeScript 严格模式
- 组件使用函数式组件 + Hooks
- 使用 Prettier 格式化代码

```bash
# 检查代码
npm run lint

# 格式化代码
npm run format
```

### 通用规范

- 变量和函数命名清晰有意义
- 避免魔法数字，使用常量
- 复杂逻辑添加注释
- 保持函数简短，单一职责

## 提交规范

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

### 提交格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 类型（Type）

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式调整（不影响逻辑）
- `refactor`: 代码重构
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建/工具链更新
- `ci`: CI/CD 配置
- `revert`: 回滚提交

### 示例

```bash
# 新功能
git commit -m "feat(templates): add template marketplace"

# Bug 修复
git commit -m "fix(auth): resolve token refresh issue"

# 文档
git commit -m "docs(readme): update installation guide"

# 重构
git commit -m "refactor(api): simplify error handling"

# 测试
git commit -m "test(executions): add execution lifecycle tests"
```

### Scope（可选）

- `api`: API 相关
- `auth`: 认证系统
- `crews`: 工作流管理
- `agents`: Agent 管理
- `tasks`: 任务管理
- `executions`: 执行引擎
- `templates`: 模板系统
- `ui`: 前端 UI
- `docs`: 文档
- `config`: 配置

## Pull Request 规范

### PR 标题

遵循提交规范格式：

```
feat(templates): add template marketplace
```

### PR 描述模板

```markdown
## 描述

简要描述这个 PR 做了什么。

## 变更类型

- [ ] 新功能 (feature)
- [ ] Bug 修复 (bugfix)
- [ ] 文档更新 (documentation)
- [ ] 代码重构 (refactor)
- [ ] 测试 (tests)
- [ ] 其他 (other)

## 相关 Issue

Closes #123
Fixes #456

## 测试

描述你如何测试了这些更改：

- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 手动测试通过

## 截图（如适用）

如果更改了 UI，请提供截图。

## 检查清单

- [ ] 我的代码遵循项目的代码规范
- [ ] 我已经进行了自我审查
- [ ] 我已经添加了必要的注释
- [ ] 我已经更新了相关文档
- [ ] 我的更改不会产生新的警告
- [ ] 我已经添加了证明我的修复有效或我的功能可以工作的测试
- [ ] 新的和现有的单元测试在我的更改下都能通过
```

### PR 最佳实践

1. **保持 PR 小而专注**：一个 PR 只做一件事
2. **提供清晰的描述**：说明为什么做这个更改
3. **添加测试**：新功能必须有测试
4. **更新文档**：如果更改了公共 API
5. **响应审查**：及时回复审查意见

## 报告 Bug

### 使用 Issue 模板

我们提供了 Bug 报告模板，请使用它来报告问题。

### Bug 报告应包含

1. **清晰的标题**：简要描述问题
2. **环境信息**：
   - 操作系统
   - Python 版本
   - Node.js 版本
   - Docker 版本
3. **重现步骤**：详细的步骤列表
4. **期望行为**：你期望发生什么
5. **实际行为**：实际发生了什么
6. **截图/日志**：如果适用
7. **可能的原因**：如果你有猜测

### 示例

```markdown
**标题**: 创建工作流时出现 500 错误

**环境**:
- OS: Windows 11
- Python: 3.12.0
- Node: 20.10.0
- Docker: 24.0.7

**重现步骤**:
1. 登录应用
2. 点击"新建工作流"
3. 输入工作流名称
4. 点击"创建"
5. 看到 500 错误

**期望行为**: 工作流应该创建成功

**实际行为**: 显示 500 Internal Server Error

**日志**:
```
ERROR: ...
```
```

## 请求新功能

### 使用 Feature Request 模板

在创建 Feature Request 之前：

1. 搜索现有 Issue，避免重复
2. 考虑这个功能是否符合项目愿景
3. 准备好详细说明使用场景

### Feature Request 应包含

1. **问题描述**：这个功能解决什么问题？
2. **解决方案**：你希望如何实现？
3. **替代方案**：考虑过其他方案吗？
4. **使用场景**：谁会使用这个功能？
5. **附加信息**：截图、参考链接等

## 社区行为准则

### 我们的承诺

为了营造一个开放和友好的环境，我们作为贡献者和维护者承诺：

- 使用友好和包容的语言
- 尊重不同的观点和经验
- 优雅地接受建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表示同情

### 不可接受的行为

- 使用性暗示的语言或图像
- 恶意评论、人身攻击或政治攻击
- 公开或私下骚扰
- 未经许可发布他人的私人信息
- 其他在专业环境中被合理认为不当的行为

## 问题？

如果你有任何问题，可以：

1. 查看 [FAQ](docs/QUICK_START.md#-常见问题)
2. 搜索 [GitHub Issues](https://github.com/yourusername/fugue/issues)
3. 创建新的 Issue
4. 联系维护者

---

**感谢你的贡献！** 🙏

每一个贡献都让 Fugue 变得更好。
