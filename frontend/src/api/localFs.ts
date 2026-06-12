/**
 * 本地文件系统API（Tauri invoke 封装）
 *
 * 动态导入 @tauri-apps/api/core，保证在非 Tauri 环境（纯浏览器）下不会崩溃。
 */

// ============ 类型定义 ============

export interface FileMetadata {
  name: string;
  path: string;
  size: number;
  is_dir: boolean;
  mime_type: string;
  modified: string;
}

export interface DirEntry {
  name: string;
  path: string;
  is_dir: boolean;
  size: number;
}

// ============ Tauri invoke 缓存 ============

type InvokeFn = (cmd: string, args?: Record<string, unknown>) => Promise<unknown>;

let _invoke: InvokeFn | null = null;

async function getInvoke(): Promise<InvokeFn> {
  if (!_invoke) {
    const core = await import('@tauri-apps/api/core');
    _invoke = core.invoke;
  }
  return _invoke;
}

// ============ 文件操作 API ============

/**
 * 打开系统文件选择对话框，返回选中的文件路径列表
 *
 * @param filters  文件类型过滤器，如 [{ name: 'Images', extensions: ['png', 'jpg'] }]
 * @param multiple 是否允许多选，默认 true
 */
export async function pickFiles(
  filters?: Array<{ name: string; extensions: string[] }>,
  multiple = true,
): Promise<string[]> {
  const invoke = await getInvoke();
  return invoke('plugin:dialog|open', {
    options: {
      multiple,
      filters,
    },
  }) as Promise<string[]>;
}

/**
 * 获取文件元数据
 */
export async function getFileMetadata(path: string): Promise<FileMetadata> {
  const invoke = await getInvoke();
  return invoke('file_metadata', { path }) as Promise<FileMetadata>;
}

/**
 * 读取文件为文本内容
 *
 * @param path     文件路径
 * @param encoding 编码，默认 utf-8
 */
export async function readFileAsText(
  path: string,
  encoding?: string,
): Promise<string> {
  const invoke = await getInvoke();
  return invoke('read_file_as_text', {
    path,
    encoding: encoding ?? 'utf-8',
  }) as Promise<string>;
}

/**
 * 读取文件为 Base64 编码字符串
 */
export async function readFileAsBase64(path: string): Promise<string> {
  const invoke = await getInvoke();
  return invoke('read_file_as_base64', { path }) as Promise<string>;
}

/**
 * 写入文件
 *
 * @param path    文件路径
 * @param content 写入内容
 * @param append  是否追加模式，默认 false（覆盖）
 */
export async function writeFile(
  path: string,
  content: string,
  append = false,
): Promise<void> {
  const invoke = await getInvoke();
  await invoke('write_file', { path, content, append });
}

/**
 * 列出目录下的文件和子目录
 */
export async function listDirectory(path: string): Promise<DirEntry[]> {
  const invoke = await getInvoke();
  return invoke('list_directory', { path }) as Promise<DirEntry[]>;
}

/**
 * 打开系统保存对话框，将内容写入用户选择的位置
 *
 * @param content         要保存的内容
 * @param defaultFilename 默认文件名，如 'report.json'
 */
export async function saveFileDialog(
  content: string,
  defaultFilename?: string,
): Promise<void> {
  const invoke = await getInvoke();
  await invoke('save_file_dialog', {
    content,
    defaultFilename: defaultFilename ?? null,
  });
}

/**
 * 打开原生文件夹选择对话框
 */
export async function pickFolder(): Promise<string | null> {
  const invoke = await getInvoke();
  return invoke('pick_folder', {}) as Promise<string | null>;
}

// ============ 工具函数 ============

/**
 * 将字节数格式化为可读字符串（B / KB / MB / GB）
 */
export function formatFileSize(bytes: number): string {
  if (bytes < 0) return '0 B';
  if (bytes < 1024) return `${bytes} B`;

  const units = ['KB', 'MB', 'GB'];
  let value = bytes / 1024;
  let unitIndex = 0;

  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex++;
  }

  return `${value.toFixed(unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
}
