/* 知识库管理页面 — 创建/查看/上传文档/管理 */

import React, { useState, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Database, FileText, Trash2, Upload, Search, X, BookOpen, ArrowLeft, AlertTriangle, CheckCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';

interface KB {
  id: string;
  name: string;
  description?: string;
  embedding_model: string;
  document_count: number;
  chunk_count: number;
  agent_mappings?: { id: string; agent_id: string }[];
  created_at: string;
}

interface Doc {
  id: string;
  filename: string;
  file_type: string;
  chunk_count: number;
  created_at: string;
}

const KnowledgeBases: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedKB, setSelectedKB] = useState<KB | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { data: kbs, isLoading } = useQuery({
    queryKey: ['knowledge-bases'],
    queryFn: async () => (await apiClient.get<KB[]>('/knowledge-bases/')).data,
  });

  const { data: vsStatus } = useQuery({
    queryKey: ['vector-store-status'],
    queryFn: async () => (await apiClient.get<{ available: boolean; engine: string; message: string }>('/knowledge-bases/vector-store/status')).data,
    staleTime: 60000,
  });

  const { data: docs } = useQuery({
    queryKey: ['kb-documents', selectedKB?.id],
    queryFn: async () => (await apiClient.get<Doc[]>(`/knowledge-bases/${selectedKB!.id}/documents`)).data,
    enabled: !!selectedKB,
  });

  const createMutation = useMutation({
    mutationFn: async () => {
      return (await apiClient.post('/knowledge-bases/', { name: newName, description: newDesc || undefined })).data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-bases'] });
      setShowCreate(false);
      setNewName('');
      setNewDesc('');
      toast.success('知识库创建成功');
    },
    onError: () => toast.error('创建失败'),
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/knowledge-bases/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge-bases'] });
      setSelectedKB(null);
      toast.success('已删除');
    },
  });

  const uploadChunks = async (text: string, filename: string) => {
    if (!selectedKB) return;
    // 分块：每 500 字符一块
    const chunks: string[] = [];
    for (let i = 0; i < text.length; i += 500) {
      chunks.push(text.slice(i, i + 500));
    }
    try {
        await apiClient.post(`/knowledge-bases/${selectedKB.id}/chunks`, {
          chunks: chunks.map(chunk => ({
            content: chunk,
            metadata: { source: filename, uploaded_at: new Date().toISOString() },
          })),
        });
      queryClient.invalidateQueries({ queryKey: ['knowledge-bases'] });
      queryClient.invalidateQueries({ queryKey: ['kb-documents', selectedKB.id] });
      toast.success(`已上传 ${filename}（${chunks.length} 个文本块）`);
    } catch {
      toast.error('上传失败');
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const text = await file.text();
    await uploadChunks(text, file.name);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleSearch = async () => {
    if (!selectedKB || !searchQuery.trim()) return;
    try {
      const res = await apiClient.get(`/knowledge-bases/${selectedKB.id}/search`, { params: { query: searchQuery, top_k: 5 } });
      setSearchResults(res.data?.results || []);
    } catch {
      toast.error('搜索失败');
    }
  };

  // 搜索命中的文档来源集合
  const matchedSources = new Set(
    searchResults.map(r => r.metadata?.source).filter(Boolean)
  );

  // 排序文档：命中文件置顶 + 按文件名排序
  const sortedDocs = [...(docs || [])].sort((a, b) => {
    const aMatch = matchedSources.has(a.filename) ? 0 : 1;
    const bMatch = matchedSources.has(b.filename) ? 0 : 1;
    if (aMatch !== bMatch) return aMatch - bMatch;
    return a.filename.localeCompare(b.filename);
  });

  // 高亮关键词
  const highlightText = (text: string, keyword: string) => {
    if (!keyword.trim()) return text;
    const regex = new RegExp(`(${keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    const parts = text.split(regex);
    return parts.map((part, i) =>
      regex.test(part)
        ? <mark key={i} style={{ background: '#FFE066', color: '#1D1D1F', borderRadius: 2, padding: '0 1px' }}>{part}</mark>
        : part
    );
  };

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-primary, #F5F5F7)', padding: '24px' }}>
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <button
              onClick={() => navigate('/')}
              style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '6px 10px', borderRadius: 8, background: 'rgba(0,0,0,0.04)', border: 'none', cursor: 'pointer', color: '#6E6E73', fontSize: 13 }}
            >
              <ArrowLeft style={{ width: 14, height: 14 }} /> 返回
            </button>
            <BookOpen style={{ width: 24, height: 24, color: '#0071E3' }} />
            <h1 style={{ fontSize: 22, fontWeight: 600, color: 'var(--text-primary, #1D1D1F)', margin: 0 }}>
              知识库管理
            </h1>
          </div>
          <button
            onClick={() => setShowCreate(true)}
            style={{
              display: 'flex', alignItems: 'center', gap: 6, padding: '8px 16px',
              borderRadius: 8, background: '#0071E3', color: '#fff', border: 'none',
              fontSize: 13, fontWeight: 500, cursor: 'pointer',
            }}
          >
            <Plus style={{ width: 14, height: 14 }} /> 新建知识库
          </button>
        </div>

        {/* 向量存储状态提示 */}
        {vsStatus && !vsStatus.available && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: 10, padding: '10px 16px',
            borderRadius: 10, background: 'rgba(255, 159, 10, 0.08)',
            border: '1px solid rgba(255, 159, 10, 0.2)', marginTop: 12, fontSize: 13,
          }}>
            <AlertTriangle style={{ width: 16, height: 16, color: '#FF9F0A', flexShrink: 0 }} />
            <span style={{ color: '#1D1D1F' }}>{vsStatus.message}</span>
          </div>
        )}
        {vsStatus && vsStatus.available && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: 10, padding: '8px 16px',
            borderRadius: 10, background: 'rgba(52, 199, 89, 0.06)',
            border: '1px solid rgba(52, 199, 89, 0.15)', marginTop: 12, fontSize: 12,
          }}>
            <CheckCircle style={{ width: 14, height: 14, color: '#34C759', flexShrink: 0 }} />
            <span style={{ color: '#6E6E73' }}>向量引擎: {vsStatus.engine}</span>
          </div>
        )}

        {/* 创建弹窗 */}
        <AnimatePresence>
          {showCreate && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              style={{
                background: '#fff', borderRadius: 12, padding: 20, marginBottom: 24,
                border: '1px solid rgba(0,0,0,0.08)', boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>新建知识库</h3>
                <button onClick={() => setShowCreate(false)} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
                  <X style={{ width: 16, height: 16, color: '#86868B' }} />
                </button>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <input
                  placeholder="知识库名称"
                  value={newName}
                  onChange={e => setNewName(e.target.value)}
                  style={{
                    padding: '10px 14px', borderRadius: 8, border: '1px solid rgba(0,0,0,0.12)',
                    fontSize: 14, outline: 'none',
                  }}
                />
                <input
                  placeholder="描述（可选）"
                  value={newDesc}
                  onChange={e => setNewDesc(e.target.value)}
                  style={{
                    padding: '10px 14px', borderRadius: 8, border: '1px solid rgba(0,0,0,0.12)',
                    fontSize: 14, outline: 'none',
                  }}
                />
                <button
                  onClick={() => createMutation.mutate()}
                  disabled={!newName.trim() || createMutation.isPending}
                  style={{
                    padding: '10px 20px', borderRadius: 8, background: '#0071E3', color: '#fff',
                    border: 'none', fontSize: 14, fontWeight: 500, cursor: 'pointer', alignSelf: 'flex-end',
                    opacity: newName.trim() ? 1 : 0.5,
                  }}
                >
                  {createMutation.isPending ? '创建中...' : '创建'}
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* 主内容 */}
        <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: 20 }}>
          {/* 左侧：知识库列表 */}
          <div style={{
            background: '#fff', borderRadius: 12, border: '1px solid rgba(0,0,0,0.08)',
            overflow: 'hidden',
          }}>
            <div style={{ padding: '14px 16px', borderBottom: '1px solid rgba(0,0,0,0.06)', fontSize: 13, fontWeight: 600, color: '#6E6E73' }}>
              知识库列表
            </div>
            {isLoading ? (
              <div style={{ padding: 40, textAlign: 'center', color: '#86868B', fontSize: 13 }}>加载中...</div>
            ) : !kbs || kbs.length === 0 ? (
              <div style={{ padding: 40, textAlign: 'center', color: '#86868B', fontSize: 13 }}>暂无知识库，点击右上角创建</div>
            ) : (
              <div>
                {kbs.map(kb => (
                  <div
                    key={kb.id}
                    onClick={() => { setSelectedKB(kb); setSearchResults([]); }}
                    style={{
                      padding: '12px 16px', cursor: 'pointer',
                      background: selectedKB?.id === kb.id ? 'rgba(0,113,227,0.06)' : 'transparent',
                      borderLeft: selectedKB?.id === kb.id ? '3px solid #0071E3' : '3px solid transparent',
                      transition: 'all 0.15s',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <Database style={{ width: 14, height: 14, color: '#0071E3' }} />
                      <span style={{ fontSize: 14, fontWeight: 500, color: '#1D1D1F' }}>{kb.name}</span>
                    </div>
                    <div style={{ fontSize: 11, color: '#86868B', marginTop: 4, paddingLeft: 22 }}>
                      {kb.document_count || 0} 文档 · {kb.chunk_count || 0} 文本块
                      {kb.agent_mappings && kb.agent_mappings.length > 0 && (
                        <span style={{ color: '#0071E3' }}> · 已关联 {kb.agent_mappings.length} Agent</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 右侧：知识库详情 */}
          <div style={{
            background: '#fff', borderRadius: 12, border: '1px solid rgba(0,0,0,0.08)',
            padding: 20,
          }}>
            {!selectedKB ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: 400, color: '#86868B' }}>
                <BookOpen style={{ width: 48, height: 48, opacity: 0.3, marginBottom: 16 }} />
                <p style={{ fontSize: 14 }}>选择左侧知识库查看详情</p>
              </div>
            ) : (
              <>
                {/* 详情头部 */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
                  <div>
                    <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600, color: '#1D1D1F' }}>{selectedKB.name}</h2>
                    {selectedKB.description && (
                      <p style={{ margin: '4px 0 0', fontSize: 13, color: '#86868B' }}>{selectedKB.description}</p>
                    )}
                  </div>
                  <button
                    onClick={() => deleteMutation.mutate(selectedKB.id)}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 4, padding: '6px 12px',
                      borderRadius: 6, background: 'rgba(255,59,48,0.08)', color: '#FF3B30',
                      border: '0.5px solid rgba(255,59,48,0.2)', fontSize: 12, cursor: 'pointer',
                    }}
                  >
                    <Trash2 style={{ width: 12, height: 12 }} /> 删除
                  </button>
                </div>

                {/* 上传文件 */}
                <div style={{
                  background: 'rgba(0,113,227,0.04)', borderRadius: 10, padding: 20,
                  border: '1px dashed rgba(0,113,227,0.3)', marginBottom: 20,
                  textAlign: 'center', cursor: 'pointer',
                }} onClick={() => fileInputRef.current?.click()}>
                  <Upload style={{ width: 24, height: 24, color: '#0071E3', marginBottom: 8 }} />
                  <p style={{ margin: 0, fontSize: 14, color: '#0071E3', fontWeight: 500 }}>点击上传文件</p>
                  <p style={{ margin: '4px 0 0', fontSize: 11, color: '#86868B' }}>支持 TXT、MD、JSON、CSV、代码文件等文本格式</p>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".txt,.md,.json,.csv,.py,.js,.ts,.html,.css,.yaml,.yml,.xml,.log"
                    onChange={handleFileUpload}
                    style={{ display: 'none' }}
                  />
                </div>

                {/* 语义搜索 */}
                <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
                  <input
                    placeholder="搜索知识库内容..."
                    value={searchQuery}
                    onChange={e => setSearchQuery(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleSearch()}
                    style={{
                      flex: 1, padding: '10px 14px', borderRadius: 8,
                      border: '1px solid rgba(0,0,0,0.12)', fontSize: 13, outline: 'none',
                    }}
                  />
                  <button
                    onClick={handleSearch}
                    style={{
                      padding: '10px 16px', borderRadius: 8, background: '#0071E3',
                      color: '#fff', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4,
                    }}
                  >
                    <Search style={{ width: 14, height: 14 }} /> 搜索
                  </button>
                </div>

                {/* 搜索结果 */}
                {searchResults.length > 0 && (
                  <div style={{ marginBottom: 20 }}>
                    <div style={{ fontSize: 12, color: '#6E6E73', marginBottom: 8, fontWeight: 600 }}>
                      搜索结果（{searchResults.length} 条）
                      <button
                        onClick={() => setSearchResults([])}
                        style={{ marginLeft: 8, fontSize: 11, color: '#86868B', background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline' }}
                      >清除</button>
                    </div>
                    {searchResults
                      .sort((a, b) => (a.metadata?.source || '').localeCompare(b.metadata?.source || ''))
                      .map((r, i) => (
                      <div key={i} style={{
                        padding: '10px 14px', borderRadius: 8, background: 'rgba(0,113,227,0.04)',
                        border: '1px solid rgba(0,113,227,0.1)', marginBottom: 8, fontSize: 13,
                      }}>
                        <div style={{ color: '#1D1D1F', lineHeight: 1.5 }}>
                          {highlightText(r.content?.slice(0, 200) || '', searchQuery)}...
                        </div>
                        <div style={{ fontSize: 11, color: '#86868B', marginTop: 4 }}>
                          相似度: {(1 - (r.distance || 0)).toFixed(2)}
                          {r.metadata?.source && (
                            <span style={{ color: '#0071E3' }}> · {r.metadata.source}</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* 文档列表 */}
                <div>
                  <div style={{ fontSize: 12, color: '#6E6E73', marginBottom: 8, fontWeight: 600 }}>
                    文档列表（{docs?.length || 0}）
                    {matchedSources.size > 0 && (
                      <span style={{ color: '#0071E3', marginLeft: 8, fontWeight: 400 }}>
                        · {matchedSources.size} 个匹配
                      </span>
                    )}
                  </div>
                  {sortedDocs.length === 0 ? (
                    <p style={{ fontSize: 13, color: '#86868B' }}>暂无文档，上传文件开始构建知识库</p>
                  ) : (
                    sortedDocs.map(doc => {
                      const isMatch = matchedSources.has(doc.filename);
                      return (
                        <div key={doc.id} style={{
                          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                          padding: '10px 14px', borderRadius: 8, marginBottom: 6,
                          background: isMatch ? 'rgba(0,113,227,0.06)' : 'transparent',
                          border: isMatch ? '1px solid rgba(0,113,227,0.2)' : '1px solid rgba(0,0,0,0.06)',
                          transition: 'all 0.15s',
                        }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <FileText style={{ width: 14, height: 14, color: isMatch ? '#0071E3' : '#86868B' }} />
                            <span style={{ fontSize: 13, color: '#1D1D1F', fontWeight: isMatch ? 600 : 400 }}>
                              {searchQuery.trim() ? highlightText(doc.filename, searchQuery) : doc.filename}
                            </span>
                            <span style={{ fontSize: 11, color: '#86868B' }}>{doc.chunk_count} 块</span>
                            {isMatch && (
                              <span style={{ fontSize: 10, color: '#0071E3', background: 'rgba(0,113,227,0.1)', padding: '1px 6px', borderRadius: 4 }}>匹配</span>
                            )}
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default KnowledgeBases;
