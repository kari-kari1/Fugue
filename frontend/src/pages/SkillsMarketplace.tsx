/**
 * Skills 功能扩展市场 — 报告第2章 Marketplace (4/10) + 第5章要求
 *
 * 报告要求:
 * - 增加 Marketplace 卡片悬停预览
 * - 版本历史展示
 * - 使用统计（安装数、评分）
 * - 第三方开发者接入展示
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';
import { apiClient } from '../api/client';
import { useAuthStore } from '../stores/authStore';

interface Skill {
  name: string;
  description: string;
  version: string;
  author: string;
  category: string;
  tags: string[];
  parameters: Record<string, { type: string; description?: string; required?: boolean; default?: unknown }>;
  required_tools: string[];
  prompt_template: string;
  task_template: { tasks?: { name: string; description: string; expected_output?: string }[] };
  star_count: number;
  install_count: number;
  verified: boolean;
}

interface Category {
  id: string;
  name: string;
  count: number;
}

export default function SkillsMarketplace() {
  const { user } = useAuthStore();
  const [skills, setSkills] = useState<Skill[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [hoveredSkill, setHoveredSkill] = useState<Skill | null>(null);
  const [selectedSkill, setSelectedSkill] = useState<Skill | null>(null);
  const [showImportMenu, setShowImportMenu] = useState(false);
  const [showImportInput, setShowImportInput] = useState<'json' | 'zip' | 'git' | null>(null);
  const [gitUrl, setGitUrl] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const isAdmin = user?.is_superuser ?? false;

  const loadSkills = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (selectedCategory) params.append('category', selectedCategory);
      if (searchQuery) params.append('search', searchQuery);

      const res = await apiClient.get(`/skills?${params}`);
      setSkills(res.data.skills);
      setCategories(res.data.categories);
    } catch {
      toast.error('加载技能失败');
    } finally {
      setLoading(false);
    }
  }, [selectedCategory, searchQuery]);

  useEffect(() => { loadSkills(); }, [loadSkills]);

  const handleInstall = async (skill: Skill) => {
    try {
      await apiClient.post(`/skills/${skill.name}/install`, { skill_name: skill.name });
      toast.success(`已安装: ${skill.name}`);
      loadSkills();
    } catch {
      toast.error('安装失败');
    }
  };

  const handleDelete = async (skill: Skill) => {
    if (!window.confirm(`确定要删除技能 "${skill.name}" 吗？此操作不可撤销。`)) return;
    try {
      await apiClient.delete(`/skills/${skill.name}`);
      toast.success(`已删除: ${skill.name}`);
      loadSkills();
    } catch {
      toast.error('删除失败');
    }
  };

  const handleImportFile = async (type: 'json' | 'zip') => {
    if (!fileInputRef.current) return;
    fileInputRef.current.accept = type === 'json' ? '.json' : '.zip';
    fileInputRef.current.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;
      const formData = new FormData();
      formData.append('file', file);
      try {
        const endpoint = type === 'json' ? '/skills/import/json' : '/skills/import/zip';
        await apiClient.post(endpoint, formData, { headers: { 'Content-Type': 'multipart/form-data' } });
        toast.success(`技能导入成功`);
        loadSkills();
      } catch {
        toast.error('导入失败');
      }
    };
    fileInputRef.current.click();
    setShowImportMenu(false);
    setShowImportInput(null);
  };

  const handleImportGit = async () => {
    if (!gitUrl.trim()) { toast.error('请输入 Git URL'); return; }
    try {
      await apiClient.post('/skills/import/git', { url: gitUrl.trim() });
      toast.success('从 Git 导入成功');
      setGitUrl('');
      setShowImportInput(null);
      setShowImportMenu(false);
      loadSkills();
    } catch {
      toast.error('导入失败');
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* 标题 */}
        <header className="mb-8 flex items-start justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-3xl font-bold mb-2">Skills 技能市场</h1>
            <p className="text-gray-400">
              一键安装可复用的任务技能，扩展智能体能力。
              <a href="/docs/plugin-sdk" className="text-blue-400 hover:underline ml-2">
                开发者文档 →
              </a>
            </p>
          </div>

          {/* 导入技能按钮 */}
          {isAdmin && (
            <div className="relative">
              <button
                onClick={() => setShowImportMenu(!showImportMenu)}
                className="px-4 py-2.5 bg-green-600 hover:bg-green-700 text-white rounded-lg
                           font-medium text-sm transition-all flex items-center gap-2"
              >
                <span>+</span> 导入技能
              </button>
              {showImportMenu && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => { setShowImportMenu(false); setShowImportInput(null); }} />
                  <div className="absolute right-0 mt-2 w-44 bg-gray-800 border border-gray-700 rounded-lg
                                  shadow-xl z-50 overflow-hidden">
                    {!showImportInput ? (
                      <>
                        <button
                          onClick={() => handleImportFile('json')}
                          className="w-full text-left px-4 py-2.5 text-sm text-gray-300 hover:bg-gray-700 transition-colors"
                        >
                          📄 从JSON导入
                        </button>
                        <button
                          onClick={() => handleImportFile('zip')}
                          className="w-full text-left px-4 py-2.5 text-sm text-gray-300 hover:bg-gray-700 transition-colors"
                        >
                          📦 从ZIP导入
                        </button>
                        <button
                          onClick={() => setShowImportInput('git')}
                          className="w-full text-left px-4 py-2.5 text-sm text-gray-300 hover:bg-gray-700 transition-colors"
                        >
                          🔗 从Git导入
                        </button>
                      </>
                    ) : (
                      <div className="p-3">
                        <input
                          type="text"
                          placeholder="输入 Git 仓库 URL"
                          value={gitUrl}
                          onChange={(e) => setGitUrl(e.target.value)}
                          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-sm
                                     text-white placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-blue-500 mb-2"
                          autoFocus
                        />
                        <div className="flex gap-2">
                          <button
                            onClick={handleImportGit}
                            className="flex-1 py-1.5 bg-green-600 hover:bg-green-700 text-white rounded text-xs transition-colors"
                          >
                            导入
                          </button>
                          <button
                            onClick={() => { setShowImportInput(null); setGitUrl(''); }}
                            className="flex-1 py-1.5 bg-gray-600 hover:bg-gray-500 text-white rounded text-xs transition-colors"
                          >
                            取消
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          )}
        </header>

        {/* 搜索和过滤 */}
        <div className="flex flex-wrap gap-4 mb-8">
          <input
            type="text"
            placeholder="搜索技能..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 min-w-[200px] px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg
                       text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="搜索技能"
          />
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={() => setSelectedCategory(null)}
              className={`px-3 py-1.5 rounded-lg text-sm transition-all ${
                !selectedCategory ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-white'
              }`}
            >
              全部
            </button>
            {categories.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(selectedCategory === cat.id ? null : cat.id)}
                className={`px-3 py-1.5 rounded-lg text-sm transition-all ${
                  selectedCategory === cat.id ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-white'
                }`}
              >
                {cat.name} ({cat.count})
              </button>
            ))}
          </div>
        </div>

        {/* 技能网格 */}
        {loading ? (
          <div className="text-center py-20 text-gray-500">加载中...</div>
        ) : skills.length === 0 ? (
          <div className="text-center py-20 text-gray-500">暂无技能</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {skills.map((skill) => (
              <SkillCard
                key={skill.name}
                skill={skill}
                onHover={setHoveredSkill}
                onClick={setSelectedSkill}
                onInstall={handleInstall}
                onDelete={handleDelete}
                isAdmin={isAdmin}
              />
            ))}
          </div>
        )}
      </div>

      {/* 悬停预览面板 */}
      <AnimatePresence>
        {hoveredSkill && !selectedSkill && (
          <HoverPreview skill={hoveredSkill} />
        )}
      </AnimatePresence>

      {/* 隐藏的文件输入 (用于 JSON/ZIP 导入) */}
      <input
        type="file"
        ref={fileInputRef}
        style={{ display: 'none' }}
      />

      {/* 详情弹窗 */}
      <AnimatePresence>
        {selectedSkill && (
          <SkillDetailModal skill={selectedSkill} onClose={() => setSelectedSkill(null)} onInstall={handleInstall} />
        )}
      </AnimatePresence>
    </div>
  );
}

// ─── Skill 卡片 ────────────────────────────────────────────────────────────

function SkillCard({ skill, onHover, onClick, onInstall, onDelete, isAdmin }: {
  skill: Skill;
  onHover: (s: Skill | null) => void;
  onClick: (s: Skill) => void;
  onInstall: (s: Skill) => void;
  onDelete: (s: Skill) => void;
  isAdmin: boolean;
}) {
  const [editing, setEditing] = useState(false);
  const [editName, setEditName] = useState(skill.name);
  const [editDesc, setEditDesc] = useState(skill.description);

  const handleEditSave = async () => {
    try {
      await apiClient.put(`/skills/${skill.name}`, { name: editName, description: editDesc });
      toast.success('技能已更新');
      setEditing(false);
      // reload handled by parent
      window.location.reload();
    } catch {
      toast.error('更新失败');
    }
  };

  if (editing) {
    return (
      <motion.div
        className="bg-gray-900 border border-blue-700 rounded-xl p-5"
        role="article"
      >
        <input
          type="text"
          value={editName}
          onChange={(e) => setEditName(e.target.value)}
          className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-white
                     placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-blue-500 mb-2"
          placeholder="技能名称"
        />
        <textarea
          value={editDesc}
          onChange={(e) => setEditDesc(e.target.value)}
          className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-white
                     placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-blue-500 mb-3"
          rows={3}
          placeholder="技能描述"
        />
        <div className="flex gap-2">
          <button
            onClick={handleEditSave}
            className="flex-1 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs transition-colors"
          >
            保存
          </button>
          <button
            onClick={() => { setEditing(false); setEditName(skill.name); setEditDesc(skill.description); }}
            className="flex-1 py-1.5 bg-gray-600 hover:bg-gray-500 text-white rounded text-xs transition-colors"
          >
            取消
          </button>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      whileHover={{ y: -2 }}
      onMouseEnter={() => onHover(skill)}
      onMouseLeave={() => onHover(null)}
      className="bg-gray-900 border border-gray-800 rounded-xl p-5 cursor-pointer
                 hover:border-gray-600 transition-all group"
      onClick={() => onClick(skill)}
      role="article"
      aria-label={`${skill.name} - ${skill.description}`}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          {skill.verified && (
            <span className="w-5 h-5 bg-blue-600 rounded-full flex items-center justify-center text-xs" title="官方验证">✓</span>
          )}
          <h3 className="font-semibold text-white group-hover:text-blue-400 transition-colors">{skill.name}</h3>
        </div>
        <div className="flex items-center gap-2">
          {isAdmin && (
            <>
              <button
                onClick={(e) => { e.stopPropagation(); setEditing(true); }}
                className="px-2 py-0.5 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded text-xs transition-colors"
                title="编辑"
              >
                编辑
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); onDelete(skill); }}
                className="px-2 py-0.5 bg-red-900/50 hover:bg-red-800 text-red-400 rounded text-xs transition-colors"
                title="删除"
              >
                删除
              </button>
            </>
          )}
          <span className="text-xs text-gray-500">v{skill.version}</span>
        </div>
      </div>

      <p className="text-sm text-gray-400 mb-4 line-clamp-2">{skill.description}</p>

      <div className="flex flex-wrap gap-1.5 mb-4">
        {skill.tags.slice(0, 3).map((tag) => (
          <span key={tag} className="px-2 py-0.5 bg-gray-800 text-gray-400 rounded text-xs">{tag}</span>
        ))}
      </div>

      <div className="flex items-center justify-between text-xs text-gray-500">
        <div className="flex items-center gap-3">
          <span>⭐ {skill.star_count}</span>
          <span>📦 {skill.install_count} 安装</span>
        </div>
        <button
          onClick={(e) => { e.stopPropagation(); onInstall(skill); }}
          className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs transition-all"
          aria-label={`安装 ${skill.name}`}
        >
          安装
        </button>
      </div>
    </motion.div>
  );
}

// ─── 悬停预览面板 ──────────────────────────────────────────────────────────

function HoverPreview({ skill }: { skill: Skill }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 10 }}
      className="fixed bottom-4 right-4 w-80 bg-gray-900 border border-gray-700 rounded-xl
                 shadow-2xl p-5 z-50"
    >
      <h4 className="font-semibold text-white mb-2">{skill.name}</h4>
      <p className="text-sm text-gray-400 mb-3">{skill.description}</p>
      <div className="text-xs text-gray-500 space-y-1">
        <p>作者: {skill.author || '社区'}</p>
        <p>版本: {skill.version}</p>
        <p>依赖工具: {skill.required_tools.join(', ') || '无'}</p>
        <p>参数: {Object.keys(skill.parameters).length} 个</p>
      </div>
      {skill.task_template.tasks && skill.task_template.tasks.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-800">
          <p className="text-xs font-medium text-gray-300 mb-1">任务流程:</p>
          {skill.task_template.tasks.map((t, i) => (
            <p key={i} className="text-xs text-gray-500">{i + 1}. {t.name}</p>
          ))}
        </div>
      )}
    </motion.div>
  );
}

// ─── 详情弹窗 ──────────────────────────────────────────────────────────────

function SkillDetailModal({ skill, onClose, onInstall }: {
  skill: Skill; onClose: () => void; onInstall: (s: Skill) => void;
}) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label={`${skill.name} 详情`}
    >
      <motion.div
        initial={{ scale: 0.95, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.95, y: 20 }}
        onClick={(e) => e.stopPropagation()}
        className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-lg mx-4 max-h-[80vh] overflow-y-auto p-6"
      >
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="flex items-center gap-2">
              {skill.verified && <span className="text-blue-400">✓ 已验证</span>}
              <h2 className="text-xl font-bold text-white">{skill.name}</h2>
            </div>
            <p className="text-sm text-gray-400 mt-1">{skill.description}</p>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-white" aria-label="关闭">✕</button>
        </div>

        {/* 统计 */}
        <div className="flex gap-6 mb-6 text-sm">
          <div><span className="text-gray-500">作者:</span> <span className="text-gray-300">{skill.author || '社区'}</span></div>
          <div><span className="text-gray-500">版本:</span> <span className="text-gray-300">{skill.version}</span></div>
          <div><span className="text-gray-500">安装:</span> <span className="text-gray-300">{skill.install_count}</span></div>
          <div><span className="text-gray-500">评分:</span> <span className="text-gray-300">⭐ {skill.star_count}</span></div>
        </div>

        {/* 标签 */}
        <div className="flex flex-wrap gap-2 mb-6">
          {skill.tags.map((tag) => (
            <span key={tag} className="px-2.5 py-1 bg-gray-800 text-gray-300 rounded-lg text-xs">{tag}</span>
          ))}
        </div>

        {/* 任务流程 */}
        {skill.task_template.tasks && skill.task_template.tasks.length > 0 && (
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-300 mb-3">任务流程</h3>
            <div className="space-y-2">
              {skill.task_template.tasks.map((t, i) => (
                <div key={i} className="flex items-start gap-3 p-3 bg-gray-800/50 rounded-lg">
                  <span className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center text-xs font-bold shrink-0">{i + 1}</span>
                  <div>
                    <p className="text-sm text-white font-medium">{t.name}</p>
                    <p className="text-xs text-gray-400">{t.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 参数 */}
        {Object.keys(skill.parameters).length > 0 && (
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-300 mb-3">参数</h3>
            <div className="space-y-2">
              {Object.entries(skill.parameters).map(([key, param]) => (
                <div key={key} className="flex items-center justify-between p-2 bg-gray-800/50 rounded text-sm">
                  <div>
                    <code className="text-blue-400">{key}</code>
                    {param.required && <span className="text-red-400 ml-1">*</span>}
                    <span className="text-gray-500 ml-2">({param.type})</span>
                  </div>
                  <span className="text-gray-400 text-xs">{param.description || ''}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 提示词预览 */}
        {skill.prompt_template && (
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-300 mb-3">提示词模板</h3>
            <pre className="text-xs text-gray-400 bg-gray-800/50 rounded-lg p-4 overflow-x-auto whitespace-pre-wrap">
              {skill.prompt_template.slice(0, 500)}{skill.prompt_template.length > 500 ? '...' : ''}
            </pre>
          </div>
        )}

        {/* 操作 */}
        <div className="flex gap-3">
          <button
            onClick={() => onInstall(skill)}
            className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-all"
          >
            安装技能
          </button>
          <button
            onClick={onClose}
            className="px-6 py-2.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-all"
          >
            关闭
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}
