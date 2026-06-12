# Fugue 前端 E2E 测试

## 概述

使用 Playwright 实现的端到端测试，覆盖 Phase 1 核心功能。

## 测试覆盖范围

### 1. 用户认证 (auth.spec.ts)
- 注册新用户
- 登录已有用户
- 未登录时重定向到登录页

### 2. 工作流管理 (workflow.spec.ts)
- 创建新工作流
- 查看工作流列表
- 编辑工作流

### 3. 画布编辑器 (editor.spec.ts)
- 显示画布工具栏
- 添加 Agent 节点
- 添加 Task 节点
- 选择节点显示属性面板
- DAG 校验显示状态

### 4. 执行监控 (execution.spec.ts)
- 显示执行历史
- 执行详情页显示状态
- 执行详情显示时间线
- WebSocket 连接状态显示

## 运行测试

```bash
# 安装依赖
npm install

# 安装浏览器
npx playwright install chromium

# 运行所有测试
npm run test:e2e

# 运行特定测试文件
npx playwright test auth.spec.ts

# 带 UI 运行
npm run test:e2e:ui

# 有头模式运行
npm run test:e2e:headed
```

## 测试结构

```
e2e/
├── auth.spec.ts        # 用户认证测试
├── workflow.spec.ts    # 工作流管理测试
├── editor.spec.ts      # 画布编辑器测试
├── execution.spec.ts   # 执行监控测试
└── README.md           # 本文档
```

## 注意事项

1. 测试需要后端服务运行（Docker Compose）
2. 测试会自动启动前端开发服务器
3. 测试使用临时用户账号，不会影响生产数据

## Phase 1 E2E 测试完成度

| 功能模块 | 测试用例数 | 状态 |
|---------|-----------|------|
| 用户认证 | 3 | ✅ 已实现 |
| 工作流管理 | 3 | ✅ 已实现 |
| 画布编辑器 | 5 | ✅ 已实现 |
| 执行监控 | 4 | ✅ 已实现 |
| **总计** | **15** | ✅ |
