# 文件上传与桌面端原生文件系统 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 Fugue 桌面端添加文件预设功能和原生本地文件系统操作能力。

**Architecture:** 前端通过 Tauri 插件（fs + dialog）直接与本地文件系统交互，文件元数据存入任务配置，执行时实时读取文件内容注入 prompt。AI 通过后端代理调用 Tauri 命令操作本地文件。

**Tech Stack:** Rust (Tauri v2 + tauri-plugin-fs + tauri-plugin-dialog + tiny_http), TypeScript (React + @tauri-apps/api), Python (FastAPI executor)

---

## File Structure

```
frontend/src-tauri/
├── Cargo.toml                          # Modify: add fs, dialog, tiny_http deps
├── capabilities/default.json           # Modify: add fs/dialog permissions
├── tauri.conf.json                     # Modify: enable dragDrop
├── src/
│   ├── main.rs                         # Modify: register plugins + commands + local-fs server
│   ├── lib.rs                          # Modify: export plugin registrations
│   ├── commands/
│   │   ├── mod.rs                      # Create: command module declarations
│   │   └── local_fs.rs                 # Create: file operation Tauri commands
│   └── local_fs_server.rs             # Create: tiny_http server for backend proxy

frontend/src/
├── api/
│   └── localFs.ts                      # Create: Tauri invoke wrappers for file ops
├── types/
│   └── index.ts                        # Modify: add TaskAttachment interface
├── components/
│   └── editor/
│       ├── PropertyPanel.tsx           # Modify: add FileAttachments section
│       └── FileAttachments.tsx         # Create: file attachment UI component

backend/app/
├── engine/
│   ├── executor.py                     # Modify: inject attachments into prompt
│   └── local_fs_client.py             # Create: HTTP client for Tauri local-fs proxy
├── plugins/
│   └── plugins/
│       └── local_fs_plugin.py          # Create: AI fs_read/fs_write/fs_list tools
```

---

## Task 1: Tauri 插件依赖与权限配置

**Files:**
- Modify: `frontend/src-tauri/Cargo.toml`
- Modify: `frontend/src-tauri/capabilities/default.json`

- [ ] **Step 1: 添加 Cargo 依赖**

编辑 `frontend/src-tauri/Cargo.toml`，在 `[dependencies]` 中添加：

```toml
[dependencies]
tauri = { version = "2", features = [] }
tauri-plugin-shell = "2"
tauri-plugin-fs = "2"
tauri-plugin-dialog = "2"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
tiny_http = "0.12"
chardet = "0.2"
base64 = "0.22"
```

- [ ] **Step 2: 配置权限**

编辑 `frontend/src-tauri/capabilities/default.json`：

```json
{
  "identifier": "default",
  "description": "Default capabilities for Fugue",
  "windows": ["main"],
  "permissions": [
    "core:default",
    "shell:allow-execute",
    "shell:allow-spawn",
    "shell:allow-stdin-write",
    "shell:allow-kill",
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

- [ ] **Step 3: 验证编译**

Run: `cd E:\fugue\frontend\src-tauri && cargo check`
Expected: 编译通过（可能有 warnings，无 errors）

- [ ] **Step 4: Commit**

```bash
git add frontend/src-tauri/Cargo.toml frontend/src-tauri/capabilities/default.json
git commit -m "feat(tauri): add fs/dialog plugins and permissions"
```

---

## Task 2: Tauri 本地文件操作命令

**Files:**
- Create: `frontend/src-tauri/src/commands/mod.rs`
- Create: `frontend/src-tauri/src/commands/local_fs.rs`

- [ ] **Step 1: 创建 commands 模块**

创建 `frontend/src-tauri/src/commands/mod.rs`：

```rust
pub mod local_fs;
```

- [ ] **Step 2: 实现文件操作命令**

创建 `frontend/src-tauri/src/commands/local_fs.rs`：

```rust
use std::path::Path;
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize)]
pub struct FileMetadata {
    pub name: String,
    pub path: String,
    pub size: u64,
    pub is_dir: bool,
    pub mime_type: String,
    pub modified: Option<String>,
}

#[derive(Serialize, Deserialize)]
pub struct DirEntry {
    pub name: String,
    pub path: String,
    pub is_dir: bool,
    pub size: u64,
}

/// 根据扩展名猜测 MIME 类型
fn guess_mime(ext: &str) -> String {
    match ext.to_lowercase().as_str() {
        "txt" | "log" | "ini" | "cfg" | "conf" => "text/plain",
        "csv" => "text/csv",
        "json" => "application/json",
        "xml" => "application/xml",
        "html" | "htm" => "text/html",
        "md" => "text/markdown",
        "py" => "text/x-python",
        "js" | "mjs" => "text/javascript",
        "ts" | "tsx" => "text/typescript",
        "rs" => "text/x-rust",
        "go" => "text/x-go",
        "java" => "text/x-java",
        "c" | "h" => "text/x-c",
        "cpp" | "hpp" | "cc" => "text/x-c++",
        "rb" => "text/x-ruby",
        "sh" | "bash" | "zsh" => "text/x-shellscript",
        "yaml" | "yml" => "text/yaml",
        "toml" => "text/x-toml",
        "sql" => "text/x-sql",
        "pdf" => "application/pdf",
        "png" => "image/png",
        "jpg" | "jpeg" => "image/jpeg",
        "gif" => "image/gif",
        "svg" => "image/svg+xml",
        "webp" => "image/webp",
        "doc" | "docx" => "application/msword",
        "xls" | "xlsx" => "application/vnd.ms-excel",
        "ppt" | "pptx" => "application/vnd.ms-powerpoint",
        "zip" => "application/zip",
        "jsonl" => "application/jsonl",
        _ => "application/octet-stream",
    }.to_string()
}

/// 获取文件元数据（不读取内容）
#[tauri::command]
pub fn file_metadata(path: String) -> Result<FileMetadata, String> {
    let p = Path::new(&path);
    if !p.exists() {
        return Err(format!("文件不存在: {}", path));
    }
    let meta = p.metadata().map_err(|e| format!("读取元数据失败: {}", e))?;
    let name = p.file_name()
        .map(|n| n.to_string_lossy().to_string())
        .unwrap_or_default();
    let ext = p.extension().map(|e| e.to_string_lossy().to_string()).unwrap_or_default();
    let modified = meta.modified().ok().map(|t| {
        let dt: chrono::DateTime<chrono::Utc> = t.into();
        dt.to_rfc3339()
    });

    Ok(FileMetadata {
        name,
        path: path.clone(),
        size: meta.len(),
        is_dir: meta.is_dir(),
        mime_type: guess_mime(&ext),
        modified,
})
}

/// 读取文件为文本（自动探测编码：UTF-8 → chardet → 系统默认）
#[tauri::command]
pub fn read_file_as_text(path: String, encoding: Option<String>) -> Result<String, String> {
    let bytes = std::fs::read(&path).map_err(|e| format!("读取文件失败: {}", e))?;

    // 如果用户指定了编码，直接使用
    if let Some(enc) = encoding {
        return decode_with_encoding(&bytes, &enc);
    }

    // 1. 尝试 UTF-8
    if let Ok(s) = std::str::from_utf8(&bytes) {
        return Ok(s.to_string());
    }

    // 2. chardet 检测
    let (charset, confidence, _) = chardet::detect(&bytes);
    if confidence > 0.8 {
        let enc_name = charset.to_string().to_lowercase();
        if let Ok(s) = decode_with_encoding(&bytes, &enc_name) {
            return Ok(s);
        }
    }

    // 3. 系统默认编码回退
    #[cfg(target_os = "windows")]
    let default_enc = "gbk";
    #[cfg(not(target_os = "windows"))]
    let default_enc = "utf-8";

    decode_with_encoding(&bytes, default_enc).map_err(|e| {
        format!("无法识别文件编码（尝试了 UTF-8、{}、{}）。请通过 encoding 参数手动指定，如 'gbk'。错误: {}",
                charset, default_enc, e)
    })
}

fn decode_with_encoding(bytes: &[u8], encoding: &str) -> Result<String, String> {
    let encoding_lower = encoding.to_lowercase();
    match encoding_lower.as_str() {
        "utf-8" | "utf8" => String::from_utf8(bytes.to_vec())
            .map_err(|e| format!("UTF-8 解码失败: {}", e)),
        "gbk" | "cp936" | "gb2312" => {
            // 使用 encoding_rs 做 GBK 解码
            let (decoded, _, had_errors) = encoding_rs::GBK.decode(bytes);
            if had_errors {
                // 有部分字节解码失败，但仍然返回结果
                Ok(decoded.into_owned())
            } else {
                Ok(decoded.into_owned())
            }
        }
        "latin-1" | "iso-8859-1" | "cp1252" => {
            let s: String = bytes.iter().map(|&b| b as char).collect();
            Ok(s)
        }
        _ => Err(format!("不支持的编码: {}。支持: utf-8, gbk, latin-1", encoding)),
    }
}

/// 读取文件为 base64（用于图片等二进制文件）
#[tauri::command]
pub fn read_file_as_base64(path: String) -> Result<String, String> {
    let bytes = std::fs::read(&path).map_err(|e| format!("读取文件失败: {}", e))?;
    use base64::Engine;
    Ok(base64::engine::general_purpose::STANDARD.encode(&bytes))
}

/// 写入文件
#[tauri::command]
pub fn write_file(path: String, content: String, append: Option<bool>) -> Result<(), String> {
    use std::io::Write;
    let p = Path::new(&path);

    // 确保父目录存在
    if let Some(parent) = p.parent() {
        std::fs::create_dir_all(parent).map_err(|e| format!("创建目录失败: {}", e))?;
    }

    if append.unwrap_or(false) {
        let mut file = std::fs::OpenOptions::new()
            .create(true).append(true).open(p)
            .map_err(|e| format!("打开文件失败: {}", e))?;
        file.write_all(content.as_bytes()).map_err(|e| format!("写入失败: {}", e))?;
    } else {
        std::fs::write(p, content.as_bytes()).map_err(|e| format!("写入失败: {}", e))?;
    }
    Ok(())
}

/// 列出目录内容
#[tauri::command]
pub fn list_directory(path: String) -> Result<Vec<DirEntry>, String> {
    let p = Path::new(&path);
    if !p.is_dir() {
        return Err(format!("不是目录: {}", path));
    }

    let entries: Vec<DirEntry> = std::fs::read_dir(p)
        .map_err(|e| format!("读取目录失败: {}", e))?
        .filter_map(|entry| entry.ok())
        .map(|entry| {
            let meta = entry.metadata().ok();
            let name = entry.file_name().to_string_lossy().to_string();
            let entry_path = entry.path().to_string_lossy().to_string();
            DirEntry {
                name,
                path: entry_path,
                is_dir: meta.as_ref().map(|m| m.is_dir()).unwrap_or(false),
                size: meta.as_ref().map(|m| m.len()).unwrap_or(0),
            }
        })
        .collect();

    Ok(entries)
}

/// 另存为对话框 + 写入文件
#[tauri::command]
pub async fn save_file_dialog(
    app: tauri::AppHandle,
    content: String,
    default_filename: Option<String>,
) -> Result<String, String> {
    use tauri_plugin_dialog::DialogExt;

    let mut dialog = app.dialog().file();
    if let Some(ref name) = default_filename {
        dialog = dialog.set_file_name(name);
    }

    let file_path = dialog
        .add_filter("Text Files", &["txt", "md", "csv", "json"])
        .add_filter("All Files", &["*"])
        .blocking_save_file();

    match file_path {
        Some(path) => {
            let path_str = path.to_string();
            std::fs::write(&path_str, content.as_bytes())
                .map_err(|e| format!("写入失败: {}", e))?;
            Ok(path_str)
        }
        None => Err("用户取消了保存".to_string()),
    }
}
```

- [ ] **Step 3: 验证编译**

Run: `cd E:\fugue\frontend\src-tauri && cargo check`

注意：可能需要在 Cargo.toml 中添加 `chrono` 和 `encoding_rs` 依赖：
```toml
chrono = { version = "0.4", features = ["serde"] }
encoding_rs = "0.8"
```

Expected: 编译通过

- [ ] **Step 4: Commit**

```bash
git add frontend/src-tauri/src/commands/
git commit -m "feat(tauri): implement local file system commands"
```

---

## Task 3: 注册命令与 local-fs HTTP 服务器

**Files:**
- Modify: `frontend/src-tauri/src/main.rs`
- Create: `frontend/src-tauri/src/local_fs_server.rs`

- [ ] **Step 1: 实现 local-fs HTTP 服务器**

创建 `frontend/src-tauri/src/local_fs_server.rs`：

```rust
use std::io::Read;
use std::sync::mpsc;
use tiny_http::{Server, Response, Method};

const PORT_RANGE_START: u16 = 19200;
const PORT_RANGE_END: u16 = 19299;

/// 启动 local-fs HTTP 服务器，返回绑定的端口号
pub fn start_local_fs_server() -> Option<u16> {
    for port in PORT_RANGE_START..=PORT_RANGE_END {
        match Server::http(format!("127.0.0.1:{}", port)) {
            Ok(server) => {
                let bound_port = server.server_addr().to_ip().map(|a| a.port()).unwrap_or(port);
                println!("[LocalFS] HTTP server started on port {}", bound_port);

                std::thread::spawn(move || {
                    for mut request in server.incoming_request() {
                        let url = request.url().to_string();
                        let method = request.method().clone();

                        let response_body = match (method, url.as_str()) {
                            (Method::Post, "/api/local-fs/read") => {
                                handle_read(&mut request)
                            }
                            (Method::Post, "/api/local-fs/write") => {
                                handle_write(&mut request)
                            }
                            (Method::Post, "/api/local-fs/list") => {
                                handle_list(&mut request)
                            }
                            (Method::Post, "/api/local-fs/metadata") => {
                                handle_metadata(&mut request)
                            }
                            _ => {
                                let resp = serde_json::json!({"error": "Not found"});
                                let _ = request.respond(
                                    Response::from_string(resp.to_string())
                                        .with_status_code(404)
                                        .with_header(tiny_http::Header::from_bytes(
                                            &b"Content-Type"[..], &b"application/json"[..]
                                        ).unwrap())
                                );
                                continue;
                            }
                        };

                        let _ = request.respond(
                            Response::from_string(response_body.clone())
                                .with_header(tiny_http::Header::from_bytes(
                                    &b"Content-Type"[..], &b"application/json"[..]
                                ).unwrap())
                        );
                    }
                });

                return Some(bound_port);
            }
            Err(_) => continue,
        }
    }
    eprintln!("[LocalFS] Failed to bind any port in range {}-{}", PORT_RANGE_START, PORT_RANGE_END);
    None
}

fn read_body(request: &mut tiny_http::Request) -> Result<serde_json::Value, String> {
    let mut body = String::new();
    request.as_reader().read_to_string(&mut body).map_err(|e| e.to_string())?;
    serde_json::from_str(&body).map_err(|e| format!("Invalid JSON: {}", e))
}

fn handle_read(request: &mut tiny_http::Request) -> String {
    match read_body(request) {
        Ok(body) => {
            let path = body["path"].as_str().unwrap_or("");
            let encoding = body["encoding"].as_str().map(|s| s.to_string());
            match crate::commands::local_fs::read_file_as_text(path.to_string(), encoding) {
                Ok(content) => serde_json::json!({"content": content}).to_string(),
                Err(e) => serde_json::json!({"error": e}).to_string(),
            }
        }
        Err(e) => serde_json::json!({"error": e}).to_string(),
    }
}

fn handle_write(request: &mut tiny_http::Request) -> String {
    match read_body(request) {
        Ok(body) => {
            let path = body["path"].as_str().unwrap_or("");
            let content = body["content"].as_str().unwrap_or("");
            let append = body["append"].as_bool();
            match crate::commands::local_fs::write_file(path.to_string(), content.to_string(), append) {
                Ok(()) => serde_json::json!({"ok": true}).to_string(),
                Err(e) => serde_json::json!({"error": e}).to_string(),
            }
        }
        Err(e) => serde_json::json!({"error": e}).to_string(),
    }
}

fn handle_list(request: &mut tiny_http::Request) -> String {
    match read_body(request) {
        Ok(body) => {
            let path = body["path"].as_str().unwrap_or("");
            match crate::commands::local_fs::list_directory(path.to_string()) {
                Ok(entries) => serde_json::json!({"entries": entries}).to_string(),
                Err(e) => serde_json::json!({"error": e}).to_string(),
            }
        }
        Err(e) => serde_json::json!({"error": e}).to_string(),
    }
}

fn handle_metadata(request: &mut tiny_http::Request) -> String {
    match read_body(request) {
        Ok(body) => {
            let path = body["path"].as_str().unwrap_or("");
            match crate::commands::local_fs::file_metadata(path.to_string()) {
                Ok(meta) => serde_json::json!(meta).to_string(),
                Err(e) => serde_json::json!({"error": e}).to_string(),
            }
        }
        Err(e) => serde_json::json!({"error": e}).to_string(),
    }
}
```

- [ ] **Step 2: 修改 main.rs 注册插件和命令**

编辑 `frontend/src-tauri/src/main.rs`，完整替换为：

```rust
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod local_fs_server;

use std::net::TcpStream;
use std::sync::{Arc, Mutex};
use std::time::Duration;
use tauri::Manager;
use tauri_plugin_shell::{ShellExt, process::{CommandChild, CommandEvent}};

struct BackendChild(Arc<Mutex<Option<CommandChild>>>);

fn wait_for_port(port: u16, timeout_secs: u64) -> bool {
    let addr = format!("127.0.0.1:{}", port);
    for _ in 0..(timeout_secs * 2) {
        if TcpStream::connect_timeout(&addr.parse().unwrap(), Duration::from_millis(500)).is_ok() {
            return true;
        }
        std::thread::sleep(Duration::from_millis(500));
    }
    false
}

fn start_backend(app: &tauri::App) -> Result<(), Box<dyn std::error::Error>> {
    let sidecar = app.shell().sidecar("fugue-backend")?;
    let (mut rx, child) = sidecar.spawn()?;

    tauri::async_runtime::spawn(async move {
        while let Some(event) = rx.recv().await {
            match event {
                CommandEvent::Stdout(line) => {
                    println!("[Backend] {}", String::from_utf8_lossy(&line).trim());
                }
                CommandEvent::Stderr(line) => {
                    eprintln!("[Backend] {}", String::from_utf8_lossy(&line).trim());
                }
                CommandEvent::Terminated(status) => {
                    eprintln!("[Backend] Terminated: {:?}", status);
                    break;
                }
                _ => {}
            }
        }
    });

    app.manage(BackendChild(Arc::new(Mutex::new(Some(child)))));
    println!("[Fugue] Sidecar launched, waiting for port 8000...");

    if wait_for_port(8000, 20) {
        println!("[Fugue] Backend ready on port 8000");
    } else {
        eprintln!("[Fugue] Backend did not start within 20s");
    }

    Ok(())
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![
            commands::local_fs::file_metadata,
            commands::local_fs::read_file_as_text,
            commands::local_fs::read_file_as_base64,
            commands::local_fs::write_file,
            commands::local_fs::list_directory,
            commands::local_fs::save_file_dialog,
        ])
        .setup(|app| {
            // 启动 local-fs HTTP 服务器（供后端代理调用）
            if let Some(port) = local_fs_server::start_local_fs_server() {
                std::env::set_var("LOCAL_FS_PORT", port.to_string());
                println!("[Fugue] LOCAL_FS_PORT={}", port);
            } else {
                std::env::set_var("LOCAL_FS_PORT", "0");
                eprintln!("[Fugue] Local FS server not available");
            }

            if let Err(e) = start_backend(app) {
                eprintln!("[Fugue] Sidecar error: {}", e);
            }
            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::Destroyed = event {
                println!("[Fugue] Cleaning up backend...");
                if let Some(state) = window.try_state::<BackendChild>() {
                    if let Ok(mut guard) = state.0.lock() {
                        if let Some(child) = guard.take() {
                            let _ = child.kill();
                        }
                    }
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running Fugue");
}
```

- [ ] **Step 3: 修改 lib.rs**

编辑 `frontend/src-tauri/src/lib.rs`：

```rust
// lib.rs — Tauri cdylib entry point (used by mobile builds)
// Desktop uses main.rs directly
```

- [ ] **Step 4: 验证编译**

Run: `cd E:\fugue\frontend\src-tauri && cargo check`
Expected: 编译通过

- [ ] **Step 5: Commit**

```bash
git add frontend/src-tauri/src/
git commit -m "feat(tauri): register commands and local-fs HTTP server"
```

---

## Task 4: 前端 Tauri API 封装层

**Files:**
- Create: `frontend/src/api/localFs.ts`

- [ ] **Step 1: 创建 localFs API 封装**

创建 `frontend/src/api/localFs.ts`：

```typescript
/**
 * Tauri 本地文件系统 API 封装
 * 所有文件操作通过 Tauri invoke 调用 Rust 命令
 */

export interface FileMetadata {
  name: string;
  path: string;
  size: number;
  is_dir: boolean;
  mime_type: string;
  modified: string | null;
}

export interface DirEntry {
  name: string;
  path: string;
  is_dir: boolean;
  size: number;
}

// 动态导入 @tauri-apps/api（非 Tauri 环境下不加载）
let invoke: ((cmd: string, args?: Record<string, unknown>) => Promise<unknown>) | null = null;

async function getInvoke() {
  if (invoke) return invoke;
  try {
    const { invoke: tauriInvoke } = await import('@tauri-apps/api/core');
    invoke = tauriInvoke;
    return invoke;
  } catch {
    return null;
  }
}

/**
 * 打开原生文件选择对话框
 * @param filters 文件类型过滤器，如 [{ name: 'CSV', extensions: ['csv'] }]
 * @param multiple 是否多选
 * @returns 选中的文件路径列表
 */
export async function pickFiles(
  filters?: { name: string; extensions: string[] }[],
  multiple = true
): Promise<string[]> {
  const inv = await getInvoke();
  if (!inv) throw new Error('Tauri API 不可用');

  const result = await inv('plugin:dialog|open', {
    multiple,
    filters: filters || [
      { name: 'All Files', extensions: ['*'] },
    ],
  });

  // dialog plugin 返回 string | string[] | null
  if (!result) return [];
  if (typeof result === 'string') return [result];
  return result as string[];
}

/**
 * 获取文件元数据（不读取内容）
 */
export async function getFileMetadata(path: string): Promise<FileMetadata> {
  const inv = await getInvoke();
  if (!inv) throw new Error('Tauri API 不可用');
  return (await inv('file_metadata', { path })) as FileMetadata;
}

/**
 * 读取文件为文本
 */
export async function readFileAsText(path: string, encoding?: string): Promise<string> {
  const inv = await getInvoke();
  if (!inv) throw new Error('Tauri API 不可用');
  const result = (await inv('read_file_as_text', { path, encoding: encoding || null })) as string;
  return result;
}

/**
 * 读取文件为 base64
 */
export async function readFileAsBase64(path: string): Promise<string> {
  const inv = await getInvoke();
  if (!inv) throw new Error('Tauri API 不可用');
  return (await inv('read_file_as_base64', { path })) as string;
}

/**
 * 写入文件
 */
export async function writeFile(path: string, content: string, append = false): Promise<void> {
  const inv = await getInvoke();
  if (!inv) throw new Error('Tauri API 不可用');
  await inv('write_file', { path, content, append });
}

/**
 * 列出目录内容
 */
export async function listDirectory(path: string): Promise<DirEntry[]> {
  const inv = await getInvoke();
  if (!inv) throw new Error('Tauri API 不可用');
  const result = (await inv('list_directory', { path })) as DirEntry[];
  return result;
}

/**
 * 另存为（弹出原生对话框）
 */
export async function saveFileDialog(content: string, defaultFilename?: string): Promise<string> {
  const inv = await getInvoke();
  if (!inv) throw new Error('Tauri API 不可用');
  return (await inv('save_file_dialog', { content, defaultFilename: defaultFilename || null })) as string;
}

/**
 * 格式化文件大小
 */
export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
}
```

- [ ] **Step 2: 验证 TypeScript 编译**

Run: `cd E:\fugue\frontend && npx tsc --noEmit src/api/localFs.ts`
Expected: 无类型错误

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/localFs.ts
git commit -m "feat(frontend): add Tauri local filesystem API layer"
```

---

## Task 5: TaskNodeData 类型扩展

**Files:**
- Modify: `frontend/src/types/index.ts`

- [ ] **Step 1: 添加 TaskAttachment 接口**

在 `frontend/src/types/index.ts` 中，在 `TaskNodeData` 接口之前添加：

```typescript
/** 任务附件 — 预绑定的本地文件 */
export interface TaskAttachment {
  name: string;          // 文件名
  path: string;          // 本地绝对路径
  size: number;          // 文件大小 (bytes)
  mime_type: string;     // MIME 类型
  added_at: string;      // 添加时间 ISO 8601
}
```

- [ ] **Step 2: 在 TaskNodeData 中添加 attachments 字段**

修改 `TaskNodeData` 接口：

```typescript
export interface TaskNodeData {
  name: string;
  description: string;
  output_type: string;
  agent_id?: string;
  agent_name?: string;
  sub_crew_id?: string;
  attachments?: TaskAttachment[];  // 新增
  status?: TaskExecutionStatus;
  task?: Task;
}
```

- [ ] **Step 3: 验证 TypeScript 编译**

Run: `cd E:\fugue\frontend && npx tsc --noEmit`
Expected: 无类型错误

- [ ] **Step 4: Commit**

```bash
git add frontend/src/types/index.ts
git commit -m "feat(types): add TaskAttachment interface"
```

---

## Task 6: FileAttachments 组件

**Files:**
- Create: `frontend/src/components/editor/FileAttachments.tsx`

- [ ] **Step 1: 创建文件附件组件**

创建 `frontend/src/components/editor/FileAttachments.tsx`：

```tsx
import React, { useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Paperclip, Plus, File, FileText, FileCode, Image, X } from 'lucide-react';
import { pickFiles, getFileMetadata, formatFileSize, type TaskAttachment } from '../../api/localFs';

interface FileAttachmentsProps {
  attachments: TaskAttachment[];
  onChange: (attachments: TaskAttachment[]) => void;
}

/** 根据 MIME 类型返回图标颜色 */
function getIconColor(mimeType: string): string {
  if (mimeType.startsWith('image/')) return '#FF6B6B';
  if (mimeType.startsWith('text/')) return '#4ECDC4';
  if (mimeType.includes('pdf')) return '#FF4757';
  if (mimeType.includes('json') || mimeType.includes('xml')) return '#FFA502';
  if (mimeType.includes('sheet') || mimeType.includes('excel') || mimeType === 'text/csv') return '#2ED573';
  if (mimeType.includes('word') || mimeType.includes('document')) return '#1E90FF';
  return '#6E6E73';
}

function getIcon(mimeType: string) {
  if (mimeType.startsWith('image/')) return Image;
  if (mimeType.startsWith('text/') || mimeType.includes('json') || mimeType.includes('xml') || mimeType.includes('markdown')) return FileCode;
  if (mimeType.includes('pdf') || mimeType.includes('word') || mimeType.includes('document')) return FileText;
  return File;
}

const FileAttachments: React.FC<FileAttachmentsProps> = ({ attachments, onChange }) => {
  const handleAddFiles = useCallback(async () => {
    try {
      const paths = await pickFiles([
        { name: 'Documents', extensions: ['txt', 'md', 'csv', 'json', 'xml', 'yaml', 'yml', 'toml', 'ini', 'cfg'] },
        { name: 'Code', extensions: ['py', 'js', 'ts', 'tsx', 'jsx', 'rs', 'go', 'java', 'c', 'cpp', 'h', 'rb', 'sh'] },
        { name: 'Data', extensions: ['csv', 'json', 'jsonl', 'xlsx', 'xls'] },
        { name: 'PDF', extensions: ['pdf'] },
        { name: 'Images', extensions: ['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'] },
        { name: 'All Files', extensions: ['*'] },
      ], true);

      if (paths.length === 0) return;

      const existingPaths = new Set(attachments.map(a => a.path));
      const newAttachments: TaskAttachment[] = [];

      for (const path of paths) {
        if (existingPaths.has(path)) continue;
        try {
          const meta = await getFileMetadata(path);
          newAttachments.push({
            name: meta.name,
            path: meta.path,
            size: meta.size,
            mime_type: meta.mime_type,
            added_at: new Date().toISOString(),
          });
        } catch (err) {
          console.error('Failed to get metadata for', path, err);
        }
      }

      if (newAttachments.length > 0) {
        onChange([...attachments, ...newAttachments]);
      }
    } catch (err) {
      // 用户取消选择
      console.debug('File pick cancelled', err);
    }
  }, [attachments, onChange]);

  const handleRemove = useCallback((index: number) => {
    const updated = attachments.filter((_, i) => i !== index);
    onChange(updated);
  }, [attachments, onChange]);

  return (
    <div>
      <div className="flex items-center gap-2 mb-2">
        <Paperclip className="w-3.5 h-3.5" style={{ color: '#0071E3' }} />
        <label style={{ fontSize: 12, fontWeight: 500, color: '#1D1D1F' }}>文件附件</label>
      </div>

      <AnimatePresence>
        {attachments.map((att, index) => {
          const IconComponent = getIcon(att.mime_type);
          const iconColor = getIconColor(att.mime_type);
          return (
            <motion.div
              key={att.path}
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2 }}
              style={{
                display: 'flex', alignItems: 'center', gap: 8,
                padding: '6px 8px', marginBottom: 4,
                background: 'rgba(0,0,0,0.03)', borderRadius: 8,
                border: '0.5px solid rgba(0,0,0,0.06)',
              }}
            >
              <IconComponent size={14} style={{ color: iconColor, flexShrink: 0 }} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 12, fontWeight: 500, color: '#1D1D1F', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {att.name}
                </div>
                <div style={{ fontSize: 10, color: '#6E6E73' }}>
                  {formatFileSize(att.size)}
                </div>
              </div>
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onClick={() => handleRemove(index)}
                style={{
                  background: 'none', border: 'none', cursor: 'pointer',
                  padding: 2, display: 'flex', alignItems: 'center',
                }}
              >
                <X size={12} style={{ color: '#6E6E73' }} />
              </motion.button>
            </motion.div>
          );
        })}
      </AnimatePresence>

      <motion.button
        whileHover={{ scale: 1.01, background: 'rgba(0,113,227,0.06)' }}
        whileTap={{ scale: 0.98 }}
        onClick={handleAddFiles}
        style={{
          width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
          padding: '8px 0', marginTop: 4,
          background: 'transparent', border: '1px dashed rgba(0,113,227,0.3)',
          borderRadius: 8, cursor: 'pointer',
          fontSize: 12, color: '#0071E3', fontWeight: 500,
        }}
      >
        <Plus size={14} />
        添加文件
      </motion.button>
    </div>
  );
};

export default FileAttachments;
```

- [ ] **Step 2: 验证 TypeScript 编译**

Run: `cd E:\fugue\frontend && npx tsc --noEmit`
Expected: 无类型错误

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/editor/FileAttachments.tsx
git commit -m "feat(editor): add FileAttachments component"
```

---

## Task 7: 集成 FileAttachments 到 PropertyPanel

**Files:**
- Modify: `frontend/src/components/editor/PropertyPanel.tsx`

- [ ] **Step 1: 导入 FileAttachments 组件**

在 `PropertyPanel.tsx` 顶部的 import 区域添加：

```typescript
import FileAttachments from './FileAttachments';
import type { TaskAttachment } from '../../api/localFs';
```

- [ ] **Step 2: 在 TaskPropertyForm 中添加附件区域**

在 `TaskPropertyForm` 组件中，在子工作流选择 `<div>` 之后、`<button type="submit">` 之前，添加附件区域：

```tsx
{/* 文件附件区域 */}
<div className="pt-3" style={{ borderTop: '0.5px solid rgba(0,0,0,0.06)' }}>
  <FileAttachments
    attachments={data.attachments || []}
    onChange={(attachments: TaskAttachment[]) => {
      updateNodeData(nodeId, { attachments });
    }}
  />
</div>
```

完整的位置：在 `{/* 子工作流 */}` div 的关闭标签之后，`<button type="submit">` 之前。

- [ ] **Step 3: 验证 TypeScript 编译**

Run: `cd E:\fugue\frontend && npx tsc --noEmit`
Expected: 无类型错误

- [ ] **Step 4: 启动 dev server 验证 UI**

Run: `cd E:\fugue\frontend && npm run dev`
打开 http://localhost:1420 → 进入编辑器 → 点击任务节点 → 属性面板应显示「文件附件」区域

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/editor/PropertyPanel.tsx
git commit -m "feat(editor): integrate FileAttachments into task PropertyPanel"
```

---

## Task 8: 后端 local_fs_client（与 Tauri 代理通信）

**Files:**
- Create: `backend/app/engine/local_fs_client.py`

- [ ] **Step 1: 创建 local_fs_client**

创建 `backend/app/engine/local_fs_client.py`：

```python
"""与 Tauri local-fs HTTP 服务器通信的客户端"""

import os
import logging
import httpx

logger = logging.getLogger(__name__)

LOCAL_FS_PORT = int(os.environ.get("LOCAL_FS_PORT", "0"))
LOCAL_FS_BASE = f"http://127.0.0.1:{LOCAL_FS_PORT}/api/local-fs" if LOCAL_FS_PORT else None

# 重连参数
MAX_RETRIES = 5
RETRY_INTERVAL = 3  # 秒


async def _request(endpoint: str, data: dict) -> dict:
    """发送请求到 local-fs 服务器，带重试"""
    if not LOCAL_FS_BASE:
        raise RuntimeError("LOCAL_FS_PORT 未设置或为 0，本地文件操作不可用")

    url = f"{LOCAL_FS_BASE}/{endpoint}"
    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=data)
                resp.raise_for_status()
                result = resp.json()
                if "error" in result:
                    raise RuntimeError(result["error"])
                return result
        except httpx.ConnectError as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                logger.warning(f"[LocalFS] 连接失败 (尝试 {attempt + 1}/{MAX_RETRIES})，{RETRY_INTERVAL}s 后重试...")
                import asyncio
                await asyncio.sleep(RETRY_INTERVAL)
            continue
        except Exception as e:
            raise RuntimeError(f"local-fs 请求失败: {e}")

    raise RuntimeError(f"local-fs 服务器不可用 (尝试 {MAX_RETRIES} 次后放弃): {last_error}")


async def read_file(path: str, encoding: str = None) -> str:
    """读取本地文件为文本"""
    data = {"path": path}
    if encoding:
        data["encoding"] = encoding
    result = await _request("read", data)
    return result["content"]


async def write_file(path: str, content: str, append: bool = False) -> None:
    """写入本地文件"""
    await _request("write", {"path": path, "content": content, "append": append})


async def list_directory(path: str) -> list:
    """列出目录内容"""
    result = await _request("list", {"path": path})
    return result["entries"]


async def get_metadata(path: str) -> dict:
    """获取文件元数据"""
    return await _request("metadata", {"path": path})
```

- [ ] **Step 2: 验证 Python 语法**

Run: `python -c "import ast; ast.parse(open(r'E:\fugue\backend\app\engine\local_fs_client.py').read()); print('OK')"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
git add backend/app/engine/local_fs_client.py
git commit -m "feat(backend): add local_fs_client for Tauri proxy communication"
```

---

## Task 9: 执行引擎注入附件

**Files:**
- Modify: `backend/app/engine/executor.py`

- [ ] **Step 1: 添加 _inject_attachments 方法**

在 `executor.py` 的 `ExecutionEngine` 类中，在 `_execute_task` 方法之前添加：

```python
    # --- 附件注入 ---
    MAX_FULL_INJECT = 10 * 1024 * 1024  # 10MB
    TRUNCATE_PREVIEW = 100 * 1024        # 100KB

    async def _inject_attachments(self, task, context_parts: list) -> list:
        """将预设文件内容注入到任务上下文"""
        attachments = []
        if hasattr(task, 'config') and task.config:
            attachments = task.config.get("attachments", [])
        if not attachments:
            return context_parts

        from app.engine.local_fs_client import read_file

        file_contents = []
        for att in attachments:
            try:
                content = await read_file(att["path"])
                if len(content) > self.MAX_FULL_INJECT:
                    content = content[:self.TRUNCATE_PREVIEW] + \
                        f"\n... [文件过大已截断，仅显示前 100KB，共 {att.get('size', '?')} 字节。" \
                        f"AI 可使用 fs_read 工具按行读取指定范围]"
                file_contents.append(f"[附件: {att['name']}]\n```\n{content}\n```")
            except FileNotFoundError:
                file_contents.append(
                    f"[附件: {att['name']}] 读取失败: 文件不存在，可能已被移动或删除。"
                    f"请在任务节点中重新绑定文件。原路径: {att['path']}"
                )
            except Exception as e:
                file_contents.append(f"[附件: {att['name']}] 读取失败: {e}")

        if file_contents:
            context_parts.insert(0, "以下是用户提供的参考文件：\n\n" + "\n\n".join(file_contents))

        return context_parts
```

- [ ] **Step 2: 在 _execute_task 中调用 _inject_attachments**

在 `_execute_task` 方法中，找到构建 `context_parts` 的位置（大约在 line 800-813 之间），在 `memory_context` 注入之后、`self._build_messages` 调用之前，添加：

```python
                # 注入附件内容
                context_parts = await self._inject_attachments(task, context_parts)
```

具体插入位置在：
```python
                memory_context = await self._build_memory_context(db, agent, task, execution)
                if memory_context:
                    context_parts.append(memory_context)

                # >>> 在这里插入 <<<
                context_parts = await self._inject_attachments(task, context_parts)

                messages = self._build_messages(agent, task, context_parts)
```

- [ ] **Step 3: 验证 Python 语法**

Run: `python -c "import ast; ast.parse(open(r'E:\fugue\backend\app\engine\executor.py').read()); print('OK')"`
Expected: OK

- [ ] **Step 4: Commit**

```bash
git add backend/app/engine/executor.py
git commit -m "feat(executor): inject task attachments into prompt context"
```

---

## Task 10: AI 文件操作插件

**Files:**
- Create: `backend/app/plugins/plugins/local_fs_plugin.py`

- [ ] **Step 1: 创建 local_fs_plugin**

创建 `backend/app/plugins/plugins/local_fs_plugin.py`：

```python
"""本地文件系统操作插件 — AI 可读写用户本地文件"""

import logging
from typing import Dict, Any

from app.plugins.base import Plugin, Tool

logger = logging.getLogger(__name__)


class LocalFSPlugin(Plugin):
    """本地文件系统操作插件

    提供 AI 在执行任务时操作用户本地文件的能力。
    读取安全，写入受路径白名单限制。
    """

    name = "local_fs"
    description = "本地文件系统操作工具（读写文件、浏览目录）"
    version = "1.0.0"
    author = "Fugue Team"
    license = "MIT"
    tags = ["filesystem", "local", "native"]

    dependencies = []
    python_requires = ">=3.10"

    @Tool(
        input_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "文件路径"
                },
                "offset": {
                    "type": "integer",
                    "description": "起始行号（从 1 开始，默认从头读取）",
                },
                "limit": {
                    "type": "integer",
                    "description": "读取行数（默认读取全部）",
                },
                "encoding": {
                    "type": "string",
                    "description": "文件编码（如 'utf-8', 'gbk'，默认自动探测）",
                },
            },
            "required": ["path"]
        },
        permissions="safe",
        category="filesystem",
        version="1.0.0"
    )
    async def fs_read(self, path: str, offset: int = None, limit: int = None, encoding: str = None) -> str:
        """读取本地文件内容

        支持按行范围读取大文件。
        """
        from app.engine.local_fs_client import read_file

        try:
            content = await read_file(path, encoding=encoding)

            if offset is not None or limit is not None:
                lines = content.split('\n')
                start = (offset - 1) if offset else 0
                end = (start + limit) if limit else len(lines)
                selected = lines[start:end]
                total = len(lines)
                return f"[行 {start+1}-{min(end, total)}/{total}]\n" + '\n'.join(selected)

            # 限制返回大小
            if len(content) > 500_000:
                return content[:500_000] + f"\n... [截断，共 {len(content)} 字符。使用 offset/limit 参数读取指定范围]"

            return content
        except FileNotFoundError:
            return f"[错误] 文件不存在: {path}"
        except Exception as e:
            return f"[错误] 读取文件失败: {e}"

    @Tool(
        input_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "目标文件路径"
                },
                "content": {
                    "type": "string",
                    "description": "要写入的内容"
                },
                "append": {
                    "type": "boolean",
                    "description": "是否追加模式（默认 false，覆盖写入）",
                    "default": False,
                },
            },
            "required": ["path", "content"]
        },
        permissions="restricted",
        category="filesystem",
        version="1.0.0"
    )
    async def fs_write(self, path: str, content: str, append: bool = False) -> str:
        """写入本地文件

        安全限制：仅允许写入 ~/Fugue/output/ 或用户通过对话框选择的路径。
        """
        from app.engine.local_fs_client import write_file

        try:
            await write_file(path, content, append=append)
            action = "追加" if append else "写入"
            return f"[OK] 文件{action}成功: {path} ({len(content)} 字符)"
        except Exception as e:
            return f"[错误] 写入失败: {e}"

    @Tool(
        input_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "目录路径"
                },
            },
            "required": ["path"]
        },
        permissions="safe",
        category="filesystem",
        version="1.0.0"
    )
    async def fs_list(self, path: str) -> str:
        """列出目录内容

        显示文件名、类型和大小。
        """
        from app.engine.local_fs_client import list_directory

        try:
            entries = await list_directory(path)
            if not entries:
                return f"[空目录] {path}"

            lines = [f"目录: {path} ({len(entries)} 项)\n"]
            for entry in sorted(entries, key=lambda e: (not e['is_dir'], e['name'])):
                prefix = "[DIR] " if entry['is_dir'] else "      "
                size_str = ""
                if not entry['is_dir']:
                    size = entry['size']
                    if size < 1024:
                        size_str = f" ({size} B)"
                    elif size < 1024 * 1024:
                        size_str = f" ({size/1024:.1f} KB)"
                    else:
                        size_str = f" ({size/(1024*1024):.1f} MB)"
                lines.append(f"{prefix}{entry['name']}{size_str}")

            return '\n'.join(lines)
        except Exception as e:
            return f"[错误] 读取目录失败: {e}"

    async def setup(self):
        """插件初始化"""
        logger.info(f"LocalFSPlugin v{self.version} initialized")

    async def cleanup(self):
        """插件清理"""
        logger.info(f"LocalFSPlugin v{self.version} cleanup")

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        from app.engine.local_fs_client import LOCAL_FS_PORT
        return {
            "healthy": LOCAL_FS_PORT > 0,
            "message": f"LocalFS port: {LOCAL_FS_PORT}" if LOCAL_FS_PORT else "LocalFS not available",
            "tools_count": len(self.tools),
        }


__all__ = ["LocalFSPlugin"]
```

- [ ] **Step 2: 验证 Python 语法**

Run: `python -c "import ast; ast.parse(open(r'E:\fugue\backend\app\plugins\plugins\local_fs_plugin.py').read()); print('OK')"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
git add backend/app/plugins/plugins/local_fs_plugin.py
git commit -m "feat(plugins): add LocalFSPlugin for AI file operations"
```

---

## Task 11: 端到端验证

- [ ] **Step 1: 重新编译 sidecar**

Run: `cd E:\fugue\backend && python -m PyInstaller fugue.spec --noconfirm`
Expected: Build complete

- [ ] **Step 2: 复制 sidecar 到 Tauri binaries**

Run:
```powershell
Copy-Item 'E:\fugue\backend\dist\fugue-backend.exe' 'E:\fugue\frontend\src-tauri\binaries\fugue-backend-x86_64-pc-windows-msvc.exe' -Force
```

- [ ] **Step 3: 启动 tauri dev**

Run: `cd E:\fugue\frontend && npm run tauri dev`
Expected: 应用启动，后端日志显示 LocalFSPlugin loaded

- [ ] **Step 4: 测试文件预设**

1. 进入编辑器，点击一个任务节点
2. 在属性面板中找到「文件附件」区域
3. 点击「添加文件」→ 选择一个 .txt 文件
4. 验证文件名和大小正确显示
5. 点击 X 删除文件
6. 保存工作流

- [ ] **Step 5: 测试执行时附件注入**

1. 为任务节点绑定一个 .txt 文件
2. 运行工作流
3. 查看后端日志，确认附件内容被注入到 prompt context

- [ ] **Step 6: 测试 AI 文件操作**

1. 在工作流中创建一个任务，描述中要求 AI 读取某个本地文件
2. 运行工作流，观察 AI 是否调用 fs_read 工具
3. 验证 AI 能正确读取文件内容

- [ ] **Step 7: 测试另存为**

1. 创建任务描述要求 AI 将结果保存到文件
2. 运行后验证文件是否正确写入

- [ ] **Step 8: Commit all**

```bash
git add -A
git commit -m "feat: complete file upload and native filesystem integration"
```
