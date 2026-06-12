# 文件上传与桌面端原生文件系统能力

**日期：** 2026-06-08
**状态：** 已批准
**范围：** 工作流文件预设 + Tauri 原生文件操作 + AI 本地文件工具

---

## 1. 目标

1. 工作流设计时，用户可为任务节点预绑定本地文件，执行时自动注入到 AI prompt
2. 桌面端具备原生文件系统操作能力（读写文件、文件选择对话框、另存为）
3. AI agent 在执行任务时可读写用户本地文件（受安全沙箱约束）

## 2. 架构概览

采用 **Tauri 直接操作** 模式（方案 A）：

```
设计时：
  用户 → 原生对话框选择文件 → Tauri fs 读取 → 存入任务配置（路径+元数据）

执行时：
  Executor 读取任务 attachments → 通过 Tauri 代理读取文件内容 → 注入 prompt

AI 操作：
  AI 调用 fs_read/fs_write 工具 → 后端 HTTP 到前端 → Tauri invoke → 本地文件系统
```

## 3. Tauri 原生层

### 3.1 新增插件依赖

| 依赖 | 版本 | 用途 |
|---|---|---|
| `tauri-plugin-fs` | 2 | 文件读写、目录列举 |
| `tauri-plugin-dialog` | 2 | 原生文件/文件夹选择对话框 |

### 3.2 Tauri 命令

| 命令 | 功能 | 调用方 |
|---|---|---|
| `pick_files` | 原生文件多选对话框，返回路径列表 | 前端 UI |
| `pick_folder` | 原生文件夹选择对话框 | 前端 UI |
| `read_file_as_text` | 读取本地文件为文本（自动探测编码，支持 GBK/UTF-8/Latin-1 等） | 前端 / 后端代理 |
| `read_file_as_bytes` | 读取本地文件为 base64 | 前端（图片/PDF） |
| `write_file` | 写入内容到指定路径 | 后端代理（AI） |
| `save_file_dialog` | 另存为对话框 | 前端 UI |
| `list_directory` | 列出目录内容（名称、类型、大小） | 后端代理（AI） |
| `file_metadata` | 获取文件元数据（大小、修改时间） | 前端 UI |

### 3.3 权限配置

`capabilities/default.json` 新增：

```json
{
  "permissions": [
    "core:default",
    "shell:default",
    "dialog:default",
    "dialog:allow-open",
    "dialog:allow-save",
    "fs:default",
    "fs:allow-read",
    "fs:allow-write",
    "fs:allow-exists",
    "fs:allow-mkdir"
  ]
}
```

> **说明：** `fs:allow-read` / `fs:allow-write` 是基础权限开关，授予 WebView 文件操作能力。
> 实际路径校验由自定义 Tauri 命令的 Rust 逻辑负责（见 6.1 安全沙箱）。
> Tauri v2 的 fs 插件 scope 机制可作为补充，但此处选择在命令层统一校验以获得更灵活的控制。

## 4. 文件预设与任务集成

### 4.1 数据模型

任务配置中新增 `attachments` 字段：

```typescript
interface TaskAttachment {
  name: string;          // 文件名
  path: string;          // 本地绝对路径
  size: number;          // 文件大小 (bytes)
  mime_type: string;     // MIME 类型
  added_at: string;      // 添加时间 ISO 8601
}
```

存储在 Task 的 `config` JSON 字段中：`task.config.attachments: TaskAttachment[]`

### 4.2 前端 UI

在 `PropertyPanel.tsx` 中新增「文件附件」区域：

- 「+ 添加文件」按钮 → 调用 `pick_files` → `file_metadata` 获取文件名、大小、修改时间等元数据（不读取内容）
- 已绑定文件列表：文件名 + 类型图标 + 大小 + 删除按钮
- 支持拖拽文件到该区域添加
- 文件图标根据扩展名显示不同颜色

### 4.3 大文件策略

| 文件类型 | 大小限制 | 处理方式 |
|---|---|---|
| 文本 < 10MB | - | 读取全文注入 prompt |
| 文本 > 10MB | - | 前 100KB + 路径，AI 可用工具按行读取 |
| 图片 | < 10MB | 转 base64 注入（多模态模型） |
| PDF | < 50MB | 使用 `pdf-extract` crate 在 Rust 层提取纯文本，再按文本规则处理 |
| 其他二进制 | - | 记录路径，AI 需用工具读取 |

**编码处理：** `read_file_as_text` 使用 `chardet` / `encoding_rs` 库自动探测编码。探测策略：

1. 尝试 UTF-8 解码 — 成功则返回
2. 使用 `chardet` 检测编码（返回置信度）— 置信度 > 0.8 时采用检测结果（如 GBK、CP1252、Shift-JIS 等）
3. 置信度不足时，回退到系统默认编码（Windows: GBK/CP936，macOS/Linux: UTF-8）
4. 系统默认编码也失败时，返回明确错误：`"无法识别文件编码，请通过 encoding 参数手动指定（如 'gbk', 'utf-8'）"`

不使用 Latin-1 作为自动回退（它能解码任意字节但产生乱码）。用户可通过 `encoding` 参数显式指定编码覆盖自动探测。

**PDF 解析方案：** 使用 Rust `pdf-extract` crate（纯 Rust，约 200KB，无外部依赖），在 Tauri 命令层实现 `extract_pdf_text` 命令。该 crate 支持文本型 PDF；扫描型 PDF（纯图片）需 OCR，初期不支持，给出明确提示。

文件路径记录在 DB，执行时**实时读取**（不缓存内容到数据库）。

**文件失效处理：** 执行时若附件文件不存在（已被移动/删除），prompt 中注入明确的错误提示，告知用户在任务节点中重新绑定文件。不在运行时自动搜索/猜测文件位置。

## 5. 执行引擎改动

### 5.1 Executor 注入附件

在 `executor.py` 的 `_execute_task` 方法中：

```python
MAX_FULL_INJECT = 10 * 1024 * 1024  # 10MB — 与 4.3 大文件策略一致
TRUNCATE_PREVIEW = 100 * 1024        # 100KB — 超限时截断预览

async def _inject_attachments(self, task, messages):
    attachments = task.config.get("attachments", [])
    if not attachments:
        return messages

    file_contents = []
    for att in attachments:
        try:
            content = await self._read_file_via_tauri(att["path"])
            if len(content) > MAX_FULL_INJECT:
                content = content[:TRUNCATE_PREVIEW] + \
                    f"\n... [文件过大已截断，仅显示前 100KB，共 {att['size']} 字节。" \
                    f"AI 可使用 fs_read 工具按行读取指定范围]"
            file_contents.append(f"[附件: {att['name']}]\n```\n{content}\n```")
        except FileNotFoundError:
            file_contents.append(
                f"[附件: {att['name']}] 读取失败: 文件不存在，可能已被移动或删除。"
                f"请在任务节点中重新绑定文件。原路径: {att['path']}"
            )
        except Exception as e:
            file_contents.append(f"[附件: {att['name']}] 读取失败: {e}")

    messages.insert(0, {
        "role": "system",
        "content": "以下是用户提供的参考文件：\n\n" + "\n\n".join(file_contents)
    })
    return messages
```

### 5.2 后端 ↔ Tauri 通信

后端（Python sidecar）无法直接调用 Tauri 命令，通过 HTTP 代理：

**开发模式（Vite）：**
```
后端 → HTTP POST localhost:1420/api/local-fs/read
     → Vite middleware 拦截
     → 转换为 Tauri invoke("read_file_as_text", { path })
     → 返回结果
```

**生产模式（打包 .exe）：**
Vite middleware 不存在。Rust 侧在启动 sidecar 之前，额外启动一个轻量 HTTP server（使用 `tiny_http` crate，约 50KB），专门处理 `/api/local-fs/*` 请求。

```
Tauri 启动 → 启动 local-fs HTTP server（见下方端口选择策略）
           → 设置环境变量 LOCAL_FS_PORT=xxxxx
           → 启动 sidecar（继承环境变量）
后端 → HTTP POST localhost:xxxxx/api/local-fs/read → Rust 处理 → 返回
```

**端口选择与健壮性：**
- 端口范围：`19200-19299`（避免与常用服务冲突）
- 启动重试：绑定失败时自动尝试下一个端口，最多重试 20 次
- 全部失败时：向用户弹出错误通知，`LOCAL_FS_PORT=0` 传给 sidecar
- Sidecar 感知：后端启动时读取 `LOCAL_FS_PORT`，若为 0 或连接失败，禁用本地文件操作功能并日志告警，不影响其他功能
- Sidecar 重连：首次连接失败后，每 3 秒重试一次，最多 5 次（等待 Tauri server 就绪）

前端 dev 模式通过 Vite proxy 代理到同一后端。

## 6. AI 本地文件操作工具

通过插件系统注册，AI 在执行任务时可调用：

| 工具名 | 功能 | 权限 | 实现 |
|---|---|---|---|
| `fs_read` | 读取文件内容（支持 offset/limit 行范围） | safe | 后端 → Tauri 代理 |
| `fs_write` | 写入/追加文件 | restricted | 后端 → Tauri 代理 |
| `fs_list` | 列出目录内容 | safe | 后端 → Tauri 代理 |
| `fs_save_as` | 弹出另存为对话框 | restricted | 后端 → Tauri 代理 |

### 6.1 安全沙箱

**默认允许读取：**
- 用户桌面 (`~/Desktop`)
- 用户文档 (`~/Documents`)
- 用户下载 (`~/Downloads`)
- 工作流附件所在目录

**默认允许写入：**
- `~/Fugue/output/`（自动创建）
- 用户通过 `save_file_dialog` 明确选择的路径

**禁止访问：**
- 系统目录 (`C:\Windows`, `/etc`, `/usr` 等)
- 其他用户目录
- 应用安装目录

路径校验在 Rust 层的 Tauri 命令中执行，白名单可由用户在设置中自定义。

## 7. 实施阶段

### Phase 1：Tauri 基础设施
- 引入 `tauri-plugin-fs` + `tauri-plugin-dialog`
- 实现所有 Tauri 命令
- 配置 capabilities 权限
- 前端封装 Tauri API 调用层

### Phase 2：文件预设功能
- PropertyPanel 新增附件 UI
- 任务配置 schema 扩展
- 文件选择、预览、删除交互

### Phase 3：执行引擎集成
- Executor 注入附件内容到 prompt
- Vite middleware 实现后端 ↔ Tauri 代理
- 大文件处理逻辑

### Phase 4：AI 文件操作工具
- 注册 `fs_read` / `fs_write` / `fs_list` / `fs_save_as` 工具
- Rust 层安全沙箱
- 设置页增加文件访问白名单配置

## 8. 不做的事情

- 不实现文件版本管理
- 不实现文件同步/冲突检测
- 不实现云存储集成（MinIO 桌面端模式不使用）
- 不在数据库中缓存文件内容（实时读取）
