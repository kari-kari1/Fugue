/* 定时任务管理页面 - Apple Clean Style */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Plus, Trash2, Pause, Play, Clock } from 'lucide-react';
import toast from 'react-hot-toast';
import { schedulesApi, type ScheduleCreate } from '../api/schedules';
import { crewsApi } from '../api/crews';
import { Button } from '../components/ui/Button';
import { parseUTC } from '../lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';

const SchedulesPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);

  const { data: tasks, isLoading } = useQuery({
    queryKey: ['schedules'],
    queryFn: () => schedulesApi.list(),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => schedulesApi.delete(id),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['schedules'] }); toast.success('定时任务已删除'); },
  });

  const toggleMutation = useMutation({
    mutationFn: (id: string) => schedulesApi.toggle(id),
    onSuccess: (result) => { queryClient.invalidateQueries({ queryKey: ['schedules'] }); toast.success(result.is_active ? '已启用' : '已暂停'); },
  });

  const activeCount = tasks?.filter((t) => t.is_active).length || 0;
  const totalRuns = tasks?.reduce((sum, t) => sum + t.run_count, 0) || 0;

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg-page)' }}>
      <header style={{ background: 'var(--bg-nav)', WebkitBackdropFilter: 'saturate(180%) blur(20px)', backdropFilter: 'saturate(180%) blur(20px)', borderBottom: '0.5px solid var(--separator)', padding: '0 var(--side-padding)' }}>
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={() => navigate('/')}>
              <ArrowLeft className="w-4 h-4 mr-1" /> 返回
            </Button>
            <h1 className="text-21 font-semibold text-primary">定时任务</h1>
          </div>
          <Button onClick={() => setShowCreateModal(true)}>
            <Plus className="w-4 h-4 mr-1" /> 创建定时任务
          </Button>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8 space-y-6">
        {/* 统计卡片 */}
        <div className="grid grid-cols-3 gap-4">
          <Card><CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-accent-primary">{tasks?.length || 0}</div>
            <div className="text-13 text-secondary">任务总数</div>
          </CardContent></Card>
          <Card><CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-accent-green">{activeCount}</div>
            <div className="text-13 text-secondary">运行中</div>
          </CardContent></Card>
          <Card><CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-purple-600">{totalRuns}</div>
            <div className="text-13 text-secondary">总执行次数</div>
          </CardContent></Card>
        </div>

        {/* 任务列表 */}
        {isLoading ? (
          <div className="space-y-3">{[1, 2, 3].map((i) => <div key={i} className="h-20 bg-secondary animate-pulse rounded-lg" />)}</div>
        ) : tasks && tasks.length > 0 ? (
          <div className="space-y-3">
            {tasks.map((task) => (
              <Card key={task.id}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        {task.is_active ? <Play className="w-4 h-4 text-accent-green" /> : <Pause className="w-4 h-4 text-tertiary" />}
                        <span className="text-13 font-medium text-primary">工作流 {task.crew_id.slice(0, 8)}</span>
                      </div>
                      <div className="text-xs text-tertiary">
                        <code className="bg-secondary px-1.5 py-0.5 rounded text-11">{task.cron_expression}</code>
                        <span className="ml-2">{task.timezone}</span>
                        <span className="ml-2">执行 {task.run_count} 次</span>
                        {task.failure_count > 0 && <span className="ml-2 text-accent-red">失败 {task.failure_count} 次</span>}
                      </div>
                      {task.next_run_at && (
                        <div className="text-xs text-accent-primary mt-1">
                          下次运行: {parseUTC(task.next_run_at).toLocaleString('zh-CN')}
                        </div>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <Button variant="ghost" size="sm" onClick={() => toggleMutation.mutate(task.id)}>
                        {task.is_active ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => deleteMutation.mutate(task.id)}>
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
              <Clock className="w-12 h-12 mx-auto text-tertiary mb-4" />
              <p className="text-secondary">还没有定时任务</p>
              <p className="text-13 text-tertiary mt-1">创建定时任务以自动执行工作流</p>
            </CardContent>
          </Card>
        )}
      </main>

      {showCreateModal && (
        <CreateScheduleModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => { setShowCreateModal(false); queryClient.invalidateQueries({ queryKey: ['schedules'] }); }}
        />
      )}
    </div>
  );
};

const CreateScheduleModal: React.FC<{ onClose: () => void; onSuccess: () => void }> = ({ onClose, onSuccess }) => {
  const [crewId, setCrewId] = useState('');
  const [cronExpression, setCronExpression] = useState('0 9 * * *');
  const [timezone, setTimezone] = useState('Asia/Shanghai');

  const { data: crews } = useQuery({ queryKey: ['crews'], queryFn: () => crewsApi.list() });

  const { data: cronValidation } = useQuery({
    queryKey: ['cron-validate', cronExpression],
    queryFn: () => schedulesApi.validateCron(cronExpression),
    enabled: cronExpression.length > 0,
  });

  const createMutation = useMutation({
    mutationFn: (data: ScheduleCreate) => schedulesApi.create(data),
    onSuccess: () => { toast.success('定时任务创建成功'); onSuccess(); },
    onError: () => toast.error('创建失败'),
  });

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <Card className="w-full max-w-md" onClick={(e) => e.stopPropagation()}>
        <CardHeader><CardTitle>创建定时任务</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-13 font-medium text-secondary mb-1.5">选择工作流</label>
            <select value={crewId} onChange={(e) => setCrewId(e.target.value)}
              className="w-full px-3 py-2.5 border border-divider radius-md text-13 outline-none bg-white">
              <option value="">请选择工作流</option>
              {crews?.map((crew) => <option key={crew.id} value={crew.id}>{crew.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-13 font-medium text-secondary mb-1.5">Cron 表达式</label>
            <input type="text" value={cronExpression} onChange={(e) => setCronExpression(e.target.value)}
              placeholder="0 9 * * *" className="w-full px-3 py-2.5 border border-divider radius-md text-13 font-mono outline-none focus:border-apple-blue" />
            {cronValidation && (
              <div className={`mt-1.5 text-xs ${cronValidation.valid ? 'text-accent-green' : 'text-accent-red'}`}>
                {cronValidation.valid ? (
                  <>✓ 有效 — 下次运行: {parseUTC(cronValidation.next_runs[0]).toLocaleString('zh-CN')}</>
                ) : '✗ 无效的 Cron 表达式'}
              </div>
            )}
          </div>
          <div>
            <label className="block text-13 font-medium text-secondary mb-1.5">时区</label>
            <select value={timezone} onChange={(e) => setTimezone(e.target.value)}
              className="w-full px-3 py-2.5 border border-divider radius-md text-13 outline-none bg-white">
              <option value="Asia/Shanghai">Asia/Shanghai (UTC+8)</option>
              <option value="UTC">UTC</option>
              <option value="America/New_York">America/New_York</option>
            </select>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="ghost" onClick={onClose}>取消</Button>
            <Button onClick={() => createMutation.mutate({ crew_id: crewId, cron_expression: cronExpression, timezone })}
              disabled={!crewId || !cronValidation?.valid || createMutation.isPending}>
              {createMutation.isPending ? '创建中...' : '创建'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SchedulesPage;
