/* API发布管理页面 - Apple Clean Style */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Plus, Trash2, Globe, Copy, Key } from 'lucide-react';
import toast from 'react-hot-toast';
import { publishedApi, apiKeysApi, type PublishRequest } from '../api/published';
import { crewsApi } from '../api/crews';
import { Button } from '../components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';

const PublishedPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showPublishModal, setShowPublishModal] = useState(false);
  const [showKeyModal, setShowKeyModal] = useState(false);

  const { data: publishedData, isLoading } = useQuery({
    queryKey: ['published'],
    queryFn: () => publishedApi.list(),
  });

  const { data: keysData } = useQuery({
    queryKey: ['api-keys'],
    queryFn: () => apiKeysApi.list(),
  });

  const unpublishMutation = useMutation({
    mutationFn: (id: string) => publishedApi.unpublish(id),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['published'] }); toast.success('已取消发布'); },
  });

  const deleteKeyMutation = useMutation({
    mutationFn: (id: string) => apiKeysApi.delete(id),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['api-keys'] }); toast.success('API Key 已删除'); },
  });

  const workflows = publishedData?.workflows || [];

  const copyEndpoint = (slug: string) => {
    navigator.clipboard.writeText(`${window.location.origin}/api/v1/published/execute/${slug}`);
    toast.success('Endpoint 已复制');
  };

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg-page)' }}>
      <header style={{ background: 'var(--bg-nav)', WebkitBackdropFilter: 'saturate(180%) blur(20px)', backdropFilter: 'saturate(180%) blur(20px)', borderBottom: '0.5px solid var(--separator)', padding: '0 var(--side-padding)' }}>
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={() => navigate('/')}>
              <ArrowLeft className="w-4 h-4 mr-1" /> 返回
            </Button>
            <h1 className="text-21 font-semibold text-primary">API 发布管理</h1>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setShowKeyModal(true)}>
              <Key className="w-4 h-4 mr-1" /> API Keys
            </Button>
            <Button onClick={() => setShowPublishModal(true)}>
              <Plus className="w-4 h-4 mr-1" /> 发布 API
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8 space-y-6">
        {/* 统计卡片 */}
        <div className="grid grid-cols-3 gap-4">
          <Card><CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-accent-primary">{workflows.length}</div>
            <div className="text-13 text-secondary">已发布 API</div>
          </CardContent></Card>
          <Card><CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-accent-green">0</div>
            <div className="text-13 text-secondary">总调用次数</div>
          </CardContent></Card>
          <Card><CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-purple-600">{keysData?.total || 0}</div>
            <div className="text-13 text-secondary">API Keys</div>
          </CardContent></Card>
        </div>

        {/* 已发布列表 */}
        {isLoading ? (
          <div className="space-y-3">{[1, 2].map((i) => <div key={i} className="h-20 bg-secondary animate-pulse rounded-lg" />)}</div>
        ) : workflows.length > 0 ? (
          <div className="space-y-3">
            {workflows.map((wf) => (
              <Card key={wf.id}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="text-13 font-medium text-primary mb-1">{wf.name}</div>
                      <div className="flex items-center gap-2">
                        <code className="text-xs bg-secondary px-1.5 py-0.5 rounded text-tertiary">
                          /api/v1/published/execute/{wf.slug}
                        </code>
                        <button onClick={() => copyEndpoint(wf.slug)} className="text-tertiary hover:text-primary">
                          <Copy className="w-3 h-3" />
                        </button>
                      </div>
                      <div className="text-xs text-tertiary mt-1">
                        v{wf.version} · 限流 {wf.rate_limit}/min · {wf.is_public ? '公开' : '私有'}
                      </div>
                    </div>
                    <Button variant="ghost" size="sm" onClick={() => unpublishMutation.mutate(wf.id)}>
                      <Trash2 className="w-4 h-4 text-accent-red" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="p-12 text-center">
              <Globe className="w-12 h-12 mx-auto text-tertiary mb-4" />
              <p className="text-secondary">还没有发布的工作流 API</p>
              <p className="text-13 text-tertiary mt-1">将工作流发布为 REST API 供外部调用</p>
            </CardContent>
          </Card>
        )}
      </main>

      {showPublishModal && (
        <PublishModal onClose={() => setShowPublishModal(false)}
          onSuccess={() => { setShowPublishModal(false); queryClient.invalidateQueries({ queryKey: ['published'] }); }} />
      )}
      {showKeyModal && (
        <ApiKeyModal onClose={() => setShowKeyModal(false)} keys={keysData?.keys || []}
          onDelete={(id) => deleteKeyMutation.mutate(id)} />
      )}
    </div>
  );
};

const PublishModal: React.FC<{ onClose: () => void; onSuccess: () => void }> = ({ onClose, onSuccess }) => {
  const [crewId, setCrewId] = useState('');
  const [slug, setSlug] = useState('');
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');

  const { data: crews } = useQuery({ queryKey: ['crews'], queryFn: () => crewsApi.list() });

  const createMutation = useMutation({
    mutationFn: (data: PublishRequest) => publishedApi.publish(crewId, data),
    onSuccess: () => { toast.success('API 发布成功'); onSuccess(); },
    onError: () => toast.error('发布失败'),
  });

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <Card className="w-full max-w-md" onClick={(e) => e.stopPropagation()}>
        <CardHeader><CardTitle>发布工作流为 API</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-13 font-medium text-secondary mb-1.5">选择工作流</label>
            <select value={crewId} onChange={(e) => setCrewId(e.target.value)}
              className="w-full px-3 py-2.5 border border-divider radius-md text-13 outline-none bg-white">
              <option value="">请选择</option>
              {crews?.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-13 font-medium text-secondary mb-1.5">API Slug</label>
            <input value={slug} onChange={(e) => setSlug(e.target.value)} placeholder="my-api"
              className="w-full px-3 py-2.5 border border-divider radius-md text-13 font-mono outline-none focus:border-apple-blue" />
          </div>
          <div>
            <label className="block text-13 font-medium text-secondary mb-1.5">名称</label>
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="我的 API"
              className="w-full px-3 py-2.5 border border-divider radius-md text-13 outline-none focus:border-apple-blue" />
          </div>
          <div>
            <label className="block text-13 font-medium text-secondary mb-1.5">描述</label>
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={2}
              className="w-full px-3 py-2.5 border border-divider radius-md text-13 outline-none focus:border-apple-blue resize-none" />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="ghost" onClick={onClose}>取消</Button>
            <Button onClick={() => createMutation.mutate({ slug, name, description })}
              disabled={!crewId || !slug || !name || createMutation.isPending}>
              {createMutation.isPending ? '发布中...' : '发布'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

const ApiKeyModal: React.FC<{
  onClose: () => void;
  keys: Array<{ id: string; name: string; key_prefix: string }>;
  onDelete: (id: string) => void;
}> = ({ onClose, keys, onDelete }) => {
  const queryClient = useQueryClient();
  const [keyName, setKeyName] = useState('');
  const [newKey, setNewKey] = useState<string | null>(null);

  const createKeyMutation = useMutation({
    mutationFn: () => apiKeysApi.create({ name: keyName, permissions: ['execute'] }),
    onSuccess: (result) => { setNewKey(result.key); queryClient.invalidateQueries({ queryKey: ['api-keys'] }); toast.success('Key 创建成功'); },
  });

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <Card className="w-full max-w-md" onClick={(e) => e.stopPropagation()}>
        <CardHeader><CardTitle>API Keys 管理</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          {newKey && (
            <div className="p-3 bg-accent-green-dim rounded-lg">
              <div className="text-xs font-medium text-accent-green mb-1">请保存此 Key（仅显示一次）</div>
              <code className="text-13 break-all">{newKey}</code>
            </div>
          )}
          <div className="flex gap-2">
            <input value={keyName} onChange={(e) => setKeyName(e.target.value)} placeholder="Key 名称"
              className="flex-1 px-3 py-2 border border-divider radius-md text-13 outline-none" />
            <Button size="sm" onClick={() => createKeyMutation.mutate()} disabled={!keyName || createKeyMutation.isPending}>创建</Button>
          </div>
          <div className="space-y-2">
            {keys.map((key) => (
              <div key={key.id} className="flex items-center justify-between p-2 bg-secondary rounded">
                <div>
                  <span className="text-13 font-medium">{key.name}</span>
                  <span className="text-xs text-tertiary ml-2">{key.key_prefix}...</span>
                </div>
                <Button variant="ghost" size="sm" onClick={() => onDelete(key.id)}>
                  <Trash2 className="w-3 h-3 text-accent-red" />
                </Button>
              </div>
            ))}
            {keys.length === 0 && <p className="text-13 text-tertiary text-center py-4">暂无 API Key</p>}
          </div>
          <div className="flex justify-end pt-2">
            <Button variant="ghost" onClick={onClose}>关闭</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PublishedPage;
