use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

// ── Data types ───────────────────────────────────────────────────────────────

#[derive(Debug, Serialize, Deserialize)]
pub struct FileMetadata {
    pub name: String,
    pub path: String,
    pub size: u64,
    pub is_dir: bool,
    pub mime_type: String,
    pub modified: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DirEntry {
    pub name: String,
    pub path: String,
    pub is_dir: bool,
    pub size: u64,
    pub mime_type: String,
}

// ── Helpers ──────────────────────────────────────────────────────────────────

pub fn guess_mime(ext: &str) -> String {
    match ext.to_lowercase().as_str() {
        // Text
        "txt" => "text/plain",
        "html" | "htm" => "text/html",
        "css" => "text/css",
        "csv" => "text/csv",
        "xml" => "text/xml",
        "md" => "text/markdown",
        "log" => "text/plain",
        // Application
        "json" => "application/json",
        "js" | "mjs" => "application/javascript",
        "ts" => "application/typescript",
        "jsx" | "tsx" => "application/javascript",
        "pdf" => "application/pdf",
        "zip" => "application/zip",
        "gz" | "gzip" => "application/gzip",
        "tar" => "application/x-tar",
        "yaml" | "yml" => "application/x-yaml",
        "toml" => "application/toml",
        "xml_app" => "application/xml",
        "wasm" => "application/wasm",
        "sh" | "bash" | "bat" | "cmd" | "ps1" => "application/x-shellscript",
        "py" => "text/x-python",
        "rs" => "text/x-rust",
        "go" => "text/x-go",
        "java" => "text/x-java",
        "c" | "h" => "text/x-c",
        "cpp" | "hpp" | "cc" | "cxx" => "text/x-c++",
        "rb" => "text/x-ruby",
        "php" => "text/x-php",
        "swift" => "text/x-swift",
        "kt" | "kts" => "text/x-kotlin",
        "sql" => "text/x-sql",
        "r" => "text/x-r",
        "lua" => "text/x-lua",
        // Image
        "png" => "image/png",
        "jpg" | "jpeg" => "image/jpeg",
        "gif" => "image/gif",
        "svg" => "image/svg+xml",
        "webp" => "image/webp",
        "ico" => "image/x-icon",
        "bmp" => "image/bmp",
        "avif" => "image/avif",
        // Audio / Video
        "mp3" => "audio/mpeg",
        "wav" => "audio/wav",
        "ogg" => "audio/ogg",
        "mp4" => "video/mp4",
        "webm" => "video/webm",
        "avi" => "video/x-msvideo",
        "mov" => "video/quicktime",
        // Fonts
        "ttf" => "font/ttf",
        "otf" => "font/otf",
        "woff" => "font/woff",
        "woff2" => "font/woff2",
        // Fallback
        _ => "application/octet-stream",
    }
    .to_string()
}

fn ext_from_path(path: &str) -> String {
    Path::new(path)
        .extension()
        .and_then(|e| e.to_str())
        .unwrap_or("")
        .to_string()
}

fn format_modified(metadata: &fs::Metadata) -> Option<String> {
    metadata
        .modified()
        .ok()
        .and_then(|t| {
            let datetime: chrono::DateTime<chrono::Local> = t.into();
            Some(datetime.format("%Y-%m-%dT%H:%M:%S%:z").to_string())
        })
}

// ── Tauri commands ───────────────────────────────────────────────────────────

#[tauri::command]
pub fn file_metadata(path: String) -> Result<FileMetadata, String> {
    let p = Path::new(&path);
    let meta = fs::metadata(p).map_err(|e| format!("Failed to read metadata for '{}': {}", path, e))?;
    let name = p
        .file_name()
        .and_then(|n| n.to_str())
        .unwrap_or("")
        .to_string();
    let ext = ext_from_path(&path);
    Ok(FileMetadata {
        name,
        path: path.clone(),
        size: meta.len(),
        is_dir: meta.is_dir(),
        mime_type: guess_mime(&ext),
        modified: format_modified(&meta),
    })
}

#[tauri::command]
pub fn read_file_as_text(path: String, encoding: Option<String>) -> Result<String, String> {
    let raw = fs::read(&path)
        .map_err(|e| format!("Failed to read file '{}': {}", path, e))?;

    // If caller specified encoding, try that first
    if let Some(enc_name) = encoding {
        let label = enc_name.as_bytes();
        if let Some(enc) = encoding_rs::Encoding::for_label(label) {
            let (decoded, _, had_errors) = enc.decode(&raw);
            if !had_errors {
                return Ok(decoded.into_owned());
            }
            // fall through to auto-detect on error
        }
    }

    // Try UTF-8 first
    match std::str::from_utf8(&raw) {
        Ok(s) => return Ok(s.to_string()),
        Err(_) => {}
    }

    // Use chardet for detection
    let (detected_encoding, confidence, _) = chardet::detect(&raw);
    let enc_label = detected_encoding.as_bytes();
    if confidence > 0.8 {
        if let Some(enc) = encoding_rs::Encoding::for_label(enc_label) {
            let (decoded, _, _) = enc.decode(&raw);
            return Ok(decoded.into_owned());
        }
    }

    // Windows default: GBK
    #[cfg(target_os = "windows")]
    {
        if let Some(enc) = encoding_rs::Encoding::for_label(b"gbk") {
            let (decoded, _, _) = enc.decode(&raw);
            return Ok(decoded.into_owned());
        }
    }

    // Encoding could not be determined — return an error with guidance
    Err("无法识别文件编码，请通过 encoding 参数手动指定（如 'gbk', 'utf-8'）".to_string())
}

#[tauri::command]
pub fn read_file_as_base64(path: String) -> Result<String, String> {
    use base64::Engine;
    let raw = fs::read(&path)
        .map_err(|e| format!("Failed to read file '{}': {}", path, e))?;
    Ok(base64::engine::general_purpose::STANDARD.encode(&raw))
}

#[tauri::command]
pub fn write_file(path: String, content: String, append: Option<bool>) -> Result<(), String> {
    let p = Path::new(&path);
    // Create parent dirs if needed
    if let Some(parent) = p.parent() {
        fs::create_dir_all(parent)
            .map_err(|e| format!("Failed to create parent dirs for '{}': {}", path, e))?;
    }
    if append.unwrap_or(false) {
        use std::io::Write;
        let mut file = std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(p)
            .map_err(|e| format!("Failed to open file '{}' for append: {}", path, e))?;
        file.write_all(content.as_bytes())
            .map_err(|e| format!("Failed to append to '{}': {}", path, e))?;
    } else {
        fs::write(p, &content)
            .map_err(|e| format!("Failed to write file '{}': {}", path, e))?;
    }
    Ok(())
}

#[tauri::command]
pub fn list_directory(path: String) -> Result<Vec<DirEntry>, String> {
    let entries = fs::read_dir(&path)
        .map_err(|e| format!("Failed to read directory '{}': {}", path, e))?;
    let mut result = Vec::new();
    for entry in entries {
        let entry = entry.map_err(|e| format!("Failed to read entry in '{}': {}", path, e))?;
        let meta = entry
            .metadata()
            .map_err(|e| format!("Failed to read metadata: {}", e))?;
        let name = entry.file_name().to_string_lossy().to_string();
        let full_path = entry.path().to_string_lossy().to_string();
        let ext = ext_from_path(&full_path);
        result.push(DirEntry {
            name,
            path: full_path,
            is_dir: meta.is_dir(),
            size: meta.len(),
            mime_type: guess_mime(&ext),
        });
    }
    Ok(result)
}

#[tauri::command]
pub async fn save_file_dialog(
    app: tauri::AppHandle,
    content: String,
    default_filename: Option<String>,
) -> Result<String, String> {
    use tauri_plugin_dialog::DialogExt;

    let mut builder = app.dialog().file();
    if let Some(name) = default_filename {
        builder = builder.set_file_name(&name);
    }

    let file_path = builder
        .blocking_save_file()
        .ok_or_else(|| "Save dialog was cancelled".to_string())?;

    // Resolve the path
    let path_str = file_path.into_path()
        .map_err(|e| format!("Failed to resolve file path: {}", e))?
        .to_string_lossy()
        .to_string();

    // Create parent dirs
    let p = Path::new(&path_str);
    if let Some(parent) = p.parent() {
        fs::create_dir_all(parent)
            .map_err(|e| format!("Failed to create parent dirs: {}", e))?;
    }

    fs::write(p, &content)
        .map_err(|e| format!("Failed to write file '{}': {}", path_str, e))?;

    Ok(path_str)
}

/// 打开原生文件夹选择对话框
#[tauri::command]
pub async fn pick_folder(app: tauri::AppHandle) -> Result<Option<String>, String> {
    use tauri_plugin_dialog::DialogExt;
    let folder = app.dialog().file().blocking_pick_folder();
    match folder {
        Some(path) => Ok(Some(path.to_string())),
        None => Ok(None),
    }
}
