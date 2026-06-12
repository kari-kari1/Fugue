/* Webhook管理页面 - Apple Clean Style */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Plus, Trash2, TestTube, Webhook as WebhookIcon, CheckCircle, XCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import { webhooksApi, type WebhookCreate } from '../api/webhooks';
import { Button } from '../components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';

const WebhooksPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);

  const { data: webhooks, isLoading } = useQuery({
    queryKey: ['webhooks'],
    queryFn: () => webhooksApi.list(),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => webhooksApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['webhooks'] });
      toast.success('Webhook已删除');
    },
  });

  const testMutation = useMutation({
    mutationFn: (id: string) => webhooksApi.test(id),
    onSuccess: (result) => {
      toast.success(result.success ? '测试发送成功' : '测试失败');
    },
    onError: () => toast.error('测试发送失败'),
  });

  const activeCount = webhooks?.filter((w) => w.is_active).length || 0;
  const disabledCount = webhooks?.filter((w) => !w.is_active).length || 0;

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg-page)' }}>
      <header style={{ background: 'var(--bg-nav)', WebkitBackdropFilter: 'saturate(180%) blur(20px)', backdropFilter: 'saturate(180%) blur(20px)', borderBottom: '0.5px solid var(--separator)', padding: '0 var(--side-padding)' }}>
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={() => navigate('/')}>
              <ArrowLeft className="w-4 h-4 mr-1" /> 返回
            </Button>
            <h1 className="text-21 font-semibold text-primary">Webhook 管理</h1>
          </div>
          <Button onClick={() => setShowCreateModal(true)}>
            <Plus className="w-4 h-4 mr-1" /> 创建 Webhook
          </Button>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8 space-y-6">
        {/* 统计卡片 */}
        <div className="grid grid-cols-3 gap-4">
          <Card><CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-accent-primary">{webhooks?.length || 0}</div>
            <div className="text-13 text-secondary">Webhook 总数</div>
          </CardContent></Card>
          <Card><CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-accent-green">{activeCount}</div>
            <div className="text-13 text-secondary">活跃</div>
          </CardContent></Card>
          <Card><CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-accent-red">{disabledCount}</div>
            <div className="text-13 text-secondary">禁用</div>
          </CardContent></Card>
        </div>

        {/* Webhook列表 */}
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-20 bg-secondary animate-pulse rounded-lg" />
            ))}
          </div>
        ) : webhooks && webhooks.length > 0 ? (
          <div className="space-y-3">
            {webhooks.map((webhook) => (
              <Card key={webhook.id}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        {webhook.is_active ? (
                          <CheckCircle className="w-4 h-4 text-accent-green" />
                        ) : (
                          <XCircle className="w-4 h-4 text-accent-red" />
                        )}
                        <span className="text-13 font-medium text-primary">{webhook.url}</span>
                      </div>
                      <div className="text-xs text-tertiary">
                        事件: {webhook.events.join(', ')}
                        {webhook.failure_count > 0 && (
                          <span className="ml-2 text-accent-red">失败 {webhook.failure_count} 次</span>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="ghost" size="sm" onClick={() => testMutation.mutate(webhook.id)} disabled={testMutation.isPending}>
                        <TestTube className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => deleteMutation.mutate(webhook.id)} disabled={deleteMutation.isPending}>
                        <Trash2 className="w-4 h-4 text-accent-red" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="p-12 text-center">
              <WebhookIcon className="w-12 h-12 mx-auto text-tertiary mb-4" />
              <p className="text-secondary">还没有 Webhook</p>
              <p className="text-13 text-tertiary mt-1">创建 Webhook 以接收执行事件通知</p>
            </CardContent>
          </Card>
        )}
      </main>

      {showCreateModal && (
        <CreateWebhookModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => { setShowCreateModal(false); queryClient.invalidateQueries({ queryKey: ['webhooks'] }); }}
        />
      )}
    </div>
  );
};

const CreateWebhookModal: React.FC<{ onClose: () => void; onSuccess: () => void }> = ({ onClose, onSuccess }) => {
  const [url, setUrl] = useState('');
  const [events, setEvents] = useState<string[]>([]);
  const [secret, setSecret] = useState('');

  const { data: eventsData } = useQuery({
    queryKey: ['webhook-events'],
    queryFn: () => webhooksApi.getEvents(),
  });

  const createMutation = useMutation({
    mutationFn: (data: WebhookCreate) => webhooksApi.create(data),
    onSuccess: () => { toast.success('Webhook 创建成功'); onSuccess(); },
    onError: () => toast.error('创建失败'),
  });

  const toggleEvent = (type: string) => {
    setEvents((prev) => prev.includes(type) ? prev.filter((e) => e !== type) : [...prev, type]);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <Card className="w-full max-w-md" onClick={(e) => e.stopPropagation()}>
        <CardHeader><CardTitle>创建 Webhook</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-13 font-medium text-secondary mb-1.5">回调 URL</label>
            <input type="url" value={url} onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com/webhook" className="w-full px-3 py-2.5 border border-divider radius-md text-13 outline-none focus:border-apple-blue" />
          </div>
          <div>
            <label className="block text-13 font-medium text-secondary mb-1.5">订阅事件</label>
            <div className="space-y-2">
              {eventsData?.events.map((event) => (
                <label key={event.type} className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={events.includes(event.type)} onChange={() => toggleEvent(event.type)} className="rounded" />
                  <span className="text-13">{event.name}</span>
                  <span className="text-xs text-tertiary">{event.description}</span>
                </label>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-13 font-medium text-secondary mb-1.5">签名密钥（可选）</label>
            <input type="text" value={secret} onChange={(e) => setSecret(e.target.value)}
              placeholder="用于验证签名" className="w-full px-3 py-2.5 border border-divider radius-md text-13 outline-none focus:border-apple-blue" />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="ghost" onClick={onClose}>取消</Button>
            <Button onClick={() => createMutation.mutate({ url, events, secret: secret || undefined })}
              disabled={!url || events.length === 0 || createMutation.isPending}>
              {createMutation.isPending ? '创建中...' : '创建'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default WebhooksPage;
