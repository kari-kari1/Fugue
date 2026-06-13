/* 分层记忆管理面板 — 编辑 project_memory、agent_experience 和 RAG 配置 */
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { BookOpen, Brain, Save, Loader2, Settings } from 'lucide-react';
import toast from 'react-hot-toast';
import { apiClient } from '../../api/client';

interface MemoryPanelProps {
  agentId?: string;
}

export const MemoryPanel: React.FC<MemoryPanelProps> = ({ agentId }) => {
  const { crewId } = useParams<{ crewId: string }>();
  const [projectMemory, setProjectMemory] = useState('');
  const [agentExperience, setAgentExperience] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  // RAG 配置
  const [chunkSize, setChunkSize] = useState(500);
  const [chunkOverlap, setChunkOverlap] = useState(50);
  const [retrievalStrategy, setRetrievalStrategy] = useState('hybrid');
  // 复合评分权重（保留供后续 RAG 评分调参）
  const [_alpha, _setAlpha] = useState(0.3);
  const [_beta, _setBeta] = useState(0.4);
  const [_gamma, _setGamma] = useState(0.3);

  useEffect(() => {
    if (!crewId) return;
    setLoading(true);
    Promise.all([
      apiClient.get(`/crews/${crewId}/memory`).catch(() => ({ data: { project_memory: '' } })),
      agentId
        ? apiClient.get(`/crews/${crewId}/agents/${agentId}/experience`).catch(() => ({ data: { agent_experience: '' } }))
        : Promise.resolve({ data: { agent_experience: '' } }),
      apiClient.get(`/crews/${crewId}`).catch(() => ({ data: {} })),
    ]).then(([pmRes, aeRes, crewRes]) => {
      setProjectMemory(pmRes.data?.project_memory || '');
      setAgentExperience(aeRes.data?.agent_experience || '');
      const mc = (crewRes.data as any)?.memory_configs?.[0] || {};
      setChunkSize(mc.chunk_size || 500);
      setChunkOverlap(mc.chunk_overlap || 50);
      setRetrievalStrategy(mc.retrieval_strategy || 'hybrid');
    }).finally(() => setLoading(false));
  }, [crewId, agentId]);

  const saveRagConfig = async () => {
    setSaving(true);
    try {
      await apiClient.put(`/crews/${crewId}`, {
        memory_config: {
          chunk_size: chunkSize,
          chunk_overlap: chunkOverlap,
          retrieval_strategy: retrievalStrategy,
        },
      });
      toast.success('RAG 配置已保存');
    } catch { toast.error('保存失败'); }
    finally { setSaving(false); }
  };

  const saveProjectMemory = async () => {
    setSaving(true);
    try {
      await apiClient.put(`/crews/${crewId}/memory`, { project_memory: projectMemory });
      toast.success('项目记忆已保存');
    } catch { toast.error('保存失败'); }
    finally { setSaving(false); }
  };

  const saveAgentExperience = async () => {
    if (!agentId) return;
    setSaving(true);
    try {
      await apiClient.put(`/crews/${crewId}/agents/${agentId}/experience`, { agent_experience: agentExperience });
      toast.success('Agent经验已保存');
    } catch { toast.error('保存失败'); }
    finally { setSaving(false); }
  };

  if (loading) return <div className="text-11" style={{ color: '#86868B' }}>加载中...</div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {/* 项目记忆 */}
      <div>
        <label className="text-11 font-medium flex items-center gap-1.5 mb-1.5" style={{ color: '#6E6E73' }}>
          <BookOpen size={12} /> 项目记忆 (AGENTS.md)
        </label>
        <textarea
          value={projectMemory}
          onChange={(e) => setProjectMemory(e.target.value)}
          rows={5}
          placeholder="项目约定、技术栈、编码规范等..."
          style={{
            width: '100%', padding: '8px 10px', borderRadius: 8, fontSize: 11,
            background: 'rgba(0,0,0,0.02)', border: '1px solid rgba(0,0,0,0.1)',
            color: '#1D1D1F', resize: 'vertical',
          }}
        />
        <button
          onClick={saveProjectMemory}
          disabled={saving}
          className="flex items-center gap-1 mt-1.5 px-2 py-1 rounded text-11 font-medium"
          style={{ background: '#0071E3', color: '#fff', border: 'none', cursor: 'pointer' }}
        >
          {saving ? <Loader2 size={10} className="animate-spin" /> : <Save size={10} />}
          保存
        </button>
      </div>

      {/* Agent经验 */}
      {agentId && (
        <div>
          <label className="text-11 font-medium flex items-center gap-1.5 mb-1.5" style={{ color: '#6E6E73' }}>
            <Brain size={12} /> Agent 经验
          </label>
          <textarea
            value={agentExperience}
            onChange={(e) => setAgentExperience(e.target.value)}
            rows={3}
            placeholder="Agent的最佳实践、已知问题等..."
            style={{
              width: '100%', padding: '8px 10px', borderRadius: 8, fontSize: 11,
              background: 'rgba(0,0,0,0.02)', border: '1px solid rgba(0,0,0,0.1)',
              color: '#1D1D1F', resize: 'vertical',
            }}
          />
          <button
            onClick={saveAgentExperience}
            disabled={saving}
            className="flex items-center gap-1 mt-1.5 px-2 py-1 rounded text-11 font-medium"
            style={{ background: '#0071E3', color: '#fff', border: 'none', cursor: 'pointer' }}
          >
            {saving ? <Loader2 size={10} className="animate-spin" /> : <Save size={10} />}
            保存
          </button>
        </div>
      )}

      {/* RAG 检索配置 */}
      <div style={{ borderTop: '0.5px solid rgba(0,0,0,0.06)', paddingTop: 10, marginTop: 8 }}>
        <label className="text-11 font-medium flex items-center gap-1.5 mb-2" style={{ color: '#6E6E73' }}>
          <Settings size={12} /> RAG 检索配置
        </label>
        <div style={{ display: 'flex', gap: 8, marginBottom: 6 }}>
          <div style={{ flex: 1 }}>
            <span style={{ fontSize: 10, color: '#86868B' }}>分块大小</span>
            <input type="number" value={chunkSize} min={100} max={2000} step={100}
              onChange={(e) => setChunkSize(Number(e.target.value))}
              style={{ width: '100%', padding: '4px 8px', borderRadius: 6, border: '1px solid rgba(0,0,0,0.1)', fontSize: 11, boxSizing: 'border-box' }} />
          </div>
          <div style={{ flex: 1 }}>
            <span style={{ fontSize: 10, color: '#86868B' }}>重叠大小</span>
            <input type="number" value={chunkOverlap} min={0} max={200} step={10}
              onChange={(e) => setChunkOverlap(Number(e.target.value))}
              style={{ width: '100%', padding: '4px 8px', borderRadius: 6, border: '1px solid rgba(0,0,0,0.1)', fontSize: 11, boxSizing: 'border-box' }} />
          </div>
        </div>
        <div style={{ marginBottom: 8 }}>
          <span style={{ fontSize: 10, color: '#86868B' }}>检索策略</span>
          <select value={retrievalStrategy} onChange={(e) => setRetrievalStrategy(e.target.value)}
            style={{ width: '100%', padding: '4px 8px', borderRadius: 6, border: '1px solid rgba(0,0,0,0.1)', fontSize: 11 }}>
            <option value="semantic">仅语义</option>
            <option value="hybrid">混合检索（语义+关键词）</option>
          </select>
        </div>
        <button onClick={saveRagConfig} disabled={saving}
          className="flex items-center gap-1 px-2 py-1 rounded text-11 font-medium"
          style={{ background: '#0071E3', color: '#fff', border: 'none', cursor: 'pointer' }}>
          {saving ? <Loader2 size={10} className="animate-spin" /> : <Save size={10} />} 保存配置
        </button>
      </div>
    </div>
  );
};
