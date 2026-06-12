/* 导出弹窗组件 */

import React, { useState } from 'react';
import { Download, X, FileJson, FileText, Loader2 } from 'lucide-react';
import { exportsApi, downloadBlob } from '../../api/exports';
import toast from 'react-hot-toast';

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  crewId?: string;
  executionId?: string;
  type: 'workflow' | 'execution';
}

export const ExportModal: React.FC<ExportModalProps> = ({
  isOpen,
  onClose,
  crewId,
  executionId,
  type,
}) => {
  const [isExporting, setIsExporting] = useState<string | null>(null);

  // Props 验证
  if (type === 'workflow' && !crewId) {
    console.warn('ExportModal: workflow类型需要crewId');
  }
  if (type === 'execution' && !executionId) {
    console.warn('ExportModal: execution类型需要executionId');
  }

  if (!isOpen) return null;

  const handleExport = async (format: 'json' | 'markdown') => {
    setIsExporting(format);
    try {
      let blob: Blob;
      let filename: string;

      if (type === 'workflow' && crewId) {
        blob = await exportsApi.exportCrewJson(crewId);
        filename = `workflow-${crewId}.json`;
      } else if (type === 'execution' && executionId) {
        if (format === 'markdown') {
          blob = await exportsApi.exportExecutionMarkdown(executionId);
          filename = `execution-${executionId}.md`;
        } else {
          blob = await exportsApi.exportExecutionJson(executionId);
          filename = `execution-${executionId}.json`;
        }
      } else {
        throw new Error('无效的导出参数');
      }

      downloadBlob(blob, filename);
      toast.success('导出成功');
      onClose();
    } catch (error: any) {
      console.error('导出失败:', error);
      const message = error?.response?.data?.detail || error?.message || '导出失败';
      toast.error(message);
    } finally {
      setIsExporting(null);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-2xl p-6 max-w-md w-full mx-4 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Download className="w-5 h-5 text-blue-600" />
            <h3 className="text-lg font-semibold">导出</h3>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
            <X className="w-5 h-5" />
          </button>
        </div>

        <p className="text-gray-600 mb-6">
          选择导出格式：
        </p>

        <div className="space-y-3">
          <button
            onClick={() => handleExport('json')}
            disabled={isExporting !== null}
            className="w-full flex items-center gap-3 p-4 bg-gray-50 hover:bg-gray-100 rounded-xl transition-colors disabled:opacity-50"
          >
            <FileJson className="w-8 h-8 text-blue-600" />
            <div className="text-left">
              <div className="font-medium text-gray-900">JSON 格式</div>
              <div className="text-sm text-gray-600">
                {type === 'workflow' ? '完整的工作流配置' : '详细的执行数据'}
              </div>
            </div>
            {isExporting === 'json' && (
              <Loader2 className="w-5 h-5 ml-auto animate-spin text-blue-600" />
            )}
          </button>

          {type === 'execution' && (
            <button
              onClick={() => handleExport('markdown')}
              disabled={isExporting !== null}
              className="w-full flex items-center gap-3 p-4 bg-gray-50 hover:bg-gray-100 rounded-xl transition-colors disabled:opacity-50"
            >
              <FileText className="w-8 h-8 text-green-600" />
              <div className="text-left">
                <div className="font-medium text-gray-900">Markdown 格式</div>
                <div className="text-sm text-gray-600">可读性强的执行报告</div>
              </div>
              {isExporting === 'markdown' && (
                <Loader2 className="w-5 h-5 ml-auto animate-spin text-green-600" />
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
