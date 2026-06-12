import React, { useCallback, useEffect, useState } from 'react';
import { pickFiles, getFileMetadata, formatFileSize } from '../../api/localFs';
import type { TaskAttachment } from '../../types';
import { Paperclip, Plus, File, FileText, FileCode, Image, X, FolderOpen } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { getCurrentWebview } from '@tauri-apps/api/webview';

interface FileAttachmentsProps {
  attachments: TaskAttachment[];
  onChange: (attachments: TaskAttachment[]) => void;
}

/** 根据 MIME 类型返回对应图标及颜色 */
function getFileIcon(mimeType: string): { Icon: React.FC<{ className?: string }>; color: string } {
  if (mimeType.startsWith('image/')) return { Icon: Image, color: '#FF3B30' };
  if (mimeType === 'application/pdf') return { Icon: FileText, color: '#FF3B30' };
  if (
    mimeType.startsWith('text/') ||
    mimeType === 'application/json' ||
    mimeType === 'application/xml'
  )
    return { Icon: FileText, color: '#30B0C7' };
  if (
    mimeType.includes('javascript') ||
    mimeType.includes('typescript') ||
    mimeType.includes('python') ||
    mimeType.includes('java') ||
    mimeType.includes('c++') ||
    mimeType.includes('c#') ||
    mimeType.includes('html') ||
    mimeType.includes('css')
  )
    return { Icon: FileCode, color: '#FF9500' };
  if (
    mimeType.includes('csv') ||
    mimeType.includes('excel') ||
    mimeType.includes('spreadsheet') ||
    mimeType.includes('sqlite')
  )
    return { Icon: File, color: '#34C759' };
  return { Icon: File, color: '#8E8E93' };
}

const FileAttachments: React.FC<FileAttachmentsProps> = ({ attachments, onChange }) => {
  const [isDragOver, setIsDragOver] = useState(false);

  // Tauri v2 drag-drop: listen for native file paths
  useEffect(() => {
    const unlistenPromise = getCurrentWebview().onDragDropEvent((event) => {
      if (event.payload.type === 'over') {
        setIsDragOver(true);
      } else if (event.payload.type === 'drop') {
        setIsDragOver(false);
        const droppedPaths = event.payload.paths;
        if (!droppedPaths || droppedPaths.length === 0) return;
        // Process dropped files asynchronously
        (async () => {
          const existingPaths = new Set(attachments.map((a) => a.path));
          const newAttachments: TaskAttachment[] = [];
          for (const filePath of droppedPaths) {
            if (existingPaths.has(filePath)) continue;
            try {
              const meta = await getFileMetadata(filePath);
              if (meta.is_dir) continue;
              newAttachments.push({
                name: meta.name,
                path: meta.path,
                size: meta.size,
                mime_type: meta.mime_type,
                added_at: new Date().toISOString(),
              });
            } catch {
              // skip files that can't be read
            }
          }
          if (newAttachments.length > 0) {
            onChange([...attachments, ...newAttachments]);
          }
        })();
      } else if (event.payload.type === 'leave') {
        setIsDragOver(false);
      }
    });
    return () => {
      unlistenPromise.then((fn) => fn());
    };
  }, [attachments, onChange]);

  const handleAdd = useCallback(async () => {
    try {
      const paths = await pickFiles([
        { name: 'Documents', extensions: ['txt', 'md', 'pdf', 'doc', 'docx'] },
        { name: 'Code', extensions: ['js', 'ts', 'py', 'java', 'cpp', 'c', 'h', 'rs', 'go'] },
        { name: 'Data', extensions: ['json', 'csv', 'xml', 'yaml', 'yml', 'toml'] },
        { name: 'Images', extensions: ['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'] },
        { name: 'All Files', extensions: ['*'] },
      ]);
      if (!paths || paths.length === 0) return;

      const existingPaths = new Set(attachments.map((a) => a.path));
      const newAttachments: TaskAttachment[] = [];

      for (const filePath of paths) {
        if (existingPaths.has(filePath)) continue;
        const meta = await getFileMetadata(filePath);
        if (meta.is_dir) continue;
        newAttachments.push({
          name: meta.name,
          path: meta.path,
          size: meta.size,
          mime_type: meta.mime_type,
          added_at: new Date().toISOString(),
        });
      }

      if (newAttachments.length > 0) {
        onChange([...attachments, ...newAttachments]);
      }
    } catch (err) {
      console.debug('File pick cancelled or failed', err);
    }
  }, [attachments, onChange]);

  const handleRemove = useCallback(
    (index: number) => {
      const next = attachments.filter((_, i) => i !== index);
      onChange(next);
    },
    [attachments, onChange],
  );

  return (
    <div
      style={{
        border: isDragOver ? '2px solid #0071E3' : '2px dashed transparent',
        borderRadius: '8px',
        background: isDragOver ? 'rgba(0,113,227,0.06)' : 'transparent',
        transition: 'all 0.2s ease',
        padding: isDragOver ? '4px' : '0',
      }}
    >
      {isDragOver && (
        <div
          className="flex items-center justify-center gap-2 py-6 mb-2"
          style={{ color: '#0071E3', fontSize: '13px', fontWeight: 500 }}
        >
          <FolderOpen className="w-5 h-5" />
          <span>松开以添加文件</span>
        </div>
      )}

      <div className="flex items-center gap-2 mb-2">
        <Paperclip className="w-3.5 h-3.5" style={{ color: '#6E6E73' }} />
        <span className="text-13 font-medium" style={{ color: '#1D1D1F' }}>
          文件附件
        </span>
      </div>

      <AnimatePresence initial={false}>
        {attachments.map((att, index) => {
          const { Icon, color } = getFileIcon(att.mime_type);
          return (
            <motion.div
              key={att.path}
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.2 }}
            >
              <div
                className="flex items-center gap-2.5 px-3 py-2 radius-sm mb-1.5"
                style={{ background: 'rgba(0,0,0,0.02)' }}
              >
                <span style={{ color, display: 'flex', alignItems: 'center' }}>
                  <Icon className="w-4 h-4 flex-shrink-0" />
                </span>
                <div className="flex-1 min-w-0">
                  <div
                    className="text-xs font-medium truncate"
                    style={{ color: '#1D1D1F' }}
                  >
                    {att.name}
                  </div>
                  <div className="text-10" style={{ color: '#6E6E73' }}>
                    {formatFileSize(att.size)}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => handleRemove(index)}
                  className="p-1 radius-sm transition-colors flex-shrink-0"
                  style={{ color: '#8E8E93' }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.color = '#FF453A';
                    e.currentTarget.style.background = 'rgba(255,69,58,0.06)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.color = '#8E8E93';
                    e.currentTarget.style.background = 'transparent';
                  }}
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            </motion.div>
          );
        })}
      </AnimatePresence>

      <button
        type="button"
        onClick={handleAdd}
        className="w-full flex items-center justify-center gap-2 px-3 py-2.5 radius-sm text-13 font-medium transition-all mt-1"
        style={{
          color: '#0071E3',
          background: 'transparent',
          border: '0.5px dashed rgba(0,113,227,0.3)',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = 'rgba(0,113,227,0.04)';
          e.currentTarget.style.borderColor = 'rgba(0,113,227,0.5)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = 'transparent';
          e.currentTarget.style.borderColor = 'rgba(0,113,227,0.3)';
        }}
      >
        <Plus className="w-3.5 h-3.5" />
        添加文件
      </button>
    </div>
  );
};

export default FileAttachments;
