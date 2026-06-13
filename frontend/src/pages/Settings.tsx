/* 设置页面 — 账户、教程、偏好、LLM 配置 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Key, Eye, EyeOff, CheckCircle, AlertCircle, Plus, Trash2, Globe, Wrench, XCircle, BookOpen } from 'lucide-react';
import { modelSupportsTools, getModelCapabilities } from '../lib/modelCapabilities';
import toast from 'react-hot-toast';

import { useAuthStore } from '../stores/authStore';
import { useTutorialStore } from '../stores/tutorialStore';
import { getLang, setLang } from '../lib/i18n';
import { Button } from '../components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { getLLMConfig, saveLLMConfig, type LLMProviderConfig, type LLMConfigMap } from '../lib/llmKeys';

const inputClass = "flex-1 px-3 py-2.5 border border-divider radius-md text-13 focus:ring-2 focus:ring-[var(--accent-primary)] focus:border-apple-blue outline-none transition-colors bg-white";

const PRESETS: { id: string; name: string; baseUrl: string; model: string; desc: string }[] = [
  { id: 'openai', name: 'OpenAI', baseUrl: 'https://api.openai.com/v1', model: 'gpt-4o', desc: 'GPT-4o / GPT-4o-mini' },
  { id: 'anthropic', name: 'Anthropic', baseUrl: 'https://api.anthropic.com/v1', model: 'claude-sonnet-4-20250514', desc: 'Claude Sonnet / Haiku' },
  { id: 'deepseek', name: 'DeepSeek', baseUrl: 'https://api.deepseek.com/v1', model: 'deepseek-chat', desc: 'DeepSeek V3 / Coder' },
  { id: 'moonshot', name: 'Moonshot', baseUrl: 'https://api.moonshot.cn/v1', model: 'moonshot-v1-8k', desc: 'Kimi / Moonshot' },
  { id: 'qwen', name: '通义千问', baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1', model: 'qwen-plus', desc: '阿里云百炼' },
  { id: 'zhipu', name: '智谱AI', baseUrl: 'https://open.bigmodel.cn/api/paas/v4', model: 'glm-4-flash', desc: 'GLM-4 系列' },
];

const Settings: React.FC = () => {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const resetTutorial = useTutorialStore((s) => s.resetTutorial);
  const setTutorialMode = useTutorialStore((s) => s.setTutorialMode);

  // LLM
  const [config, setConfig] = useState<LLMConfigMap>(() => getLLMConfig());
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({});
  const [customName, setCustomName] = useState('');

  // Language
  const [lang, setLangState] = useState(getLang());
  const toggleLang = () => { const next = lang === 'zh' ? 'en' : 'zh'; setLangState(next); setLang(next); window.location.reload(); };

  const updateProvider = (id: string, field: keyof LLMProviderConfig, value: string) => {
    setConfig((prev) => ({ ...prev, [id]: { ...{ api_key: '', base_url: '', model: '' }, ...prev[id], [field]: value } }));
  };
  const removeProvider = (id: string) => { setConfig((prev) => { const next = { ...prev }; delete next[id]; return next; }); };
  const addPreset = (preset: typeof PRESETS[0]) => {
    if (config[preset.id]) { toast('该提供商已添加'); return; }
    setConfig((prev) => ({ ...prev, [preset.id]: { api_key: '', base_url: preset.baseUrl, model: preset.model } }));
  };
  const addCustom = () => {
    const id = customName.trim().toLowerCase().replace(/\s+/g, '_');
    if (!id) { toast.error('请输入提供商名称'); return; }
    if (config[id]) { toast('该名称已存在'); return; }
    setConfig((prev) => ({ ...prev, [id]: { api_key: '', base_url: '', model: '' } }));
    setCustomName('');
  };
  const handleSave = () => {
    const cleaned: LLMConfigMap = {};
    Object.entries(config).forEach(([id, cfg]) => { if (cfg.api_key?.trim()) cleaned[id] = { ...cfg, api_key: cfg.api_key.trim() }; });
    saveLLMConfig(cleaned); setConfig(cleaned); toast.success('配置已保存');
  };
  const handleReplayTutorial = () => { resetTutorial(); setTutorialMode(true); toast.success('教程已重新开启，返回首页查看'); };

  const configuredCount = Object.values(config).filter((c) => c.api_key?.trim()).length;
  const unconfiguredPresets = PRESETS.filter((p) => !config[p.id]);

  const sectionClass = "mb-8";
  const sectionTitleClass = "text-sm font-semibold text-primary mb-4 flex items-center gap-2";

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-page)' }}>
      <header style={{ position: 'sticky', top: 0, zIndex: 'var(--z-sticky)', background: 'var(--bg-nav)', WebkitBackdropFilter: 'saturate(180%) blur(20px)', backdropFilter: 'saturate(180%) blur(20px)', borderBottom: '0.5px solid var(--separator)' }}>
        <div style={{ maxWidth: 'var(--content-max)', margin: '0 auto', padding: '0 var(--side-padding)', height: 'var(--nav-height)', display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
          <motion.button onClick={() => navigate('/')} whileTap={{ scale: 0.97 }} style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--accent)', fontSize: 'var(--text-footnote)', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <ArrowLeft style={{ width: 16, height: 16 }} /> Back
          </motion.button>
          <h1 style={{ fontSize: 'var(--text-heading)', fontWeight: 'var(--fw-semibold)', color: 'var(--text-primary)', letterSpacing: 'var(--ls-feature)', margin: 0 }}>Settings</h1>
        </div>
      </header>

      <main style={{ maxWidth: 'var(--content-max)', margin: '0 auto', padding: 'var(--space-8) var(--side-padding) var(--space-24)', display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>

        {/* ── 账户信息 ── */}
        <div className={sectionClass}>
          <h2 className={sectionTitleClass}>账户</h2>
          <Card>
            <CardContent className="p-4 space-y-3">
              <div className="flex justify-between items-center">
                <div><div className="text-13 font-medium text-primary">{user?.username || '-'}</div><div className="text-xs text-secondary">{user?.email || '-'}</div></div>
                <button onClick={logout} className="text-xs text-accent-red hover:underline">退出登录</button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* ── 偏好设置 ── */}
        <div className={sectionClass}>
          <h2 className={sectionTitleClass}>偏好设置</h2>
          <Card>
            <CardContent className="p-4 space-y-3">
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-2"><Globe className="w-4 h-4" /><span className="text-13">语言 / Language</span></div>
                <button onClick={toggleLang} className="px-3 py-1 text-xs bg-secondary border border-divider rounded-full text-primary hover:border-accent-primary transition-all font-medium">{lang === 'zh' ? 'EN' : '中文'}</button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* ── 教程 ── */}
        <div className={sectionClass}>
          <h2 className={sectionTitleClass}><BookOpen className="w-4 h-4" /> 教程与帮助</h2>
          <Card>
            <CardContent className="p-4 space-y-3">
              <p className="text-13 text-secondary">重新体验新手教程，了解 Fugue 的核心功能和操作流程。</p>
              <Button variant="outline" size="sm" onClick={handleReplayTutorial}>重新开始教程</Button>
            </CardContent>
          </Card>
        </div>

        {/* ── LLM 配置 ── */}
        <div className={sectionClass}>
          <h2 className={sectionTitleClass}><Key className="w-4 h-4" /> LLM 配置</h2>

          <Card className="mb-4">
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-accent-primary mt-0.5 flex-shrink-0" />
                <div className="text-13 text-secondary">
                  <p className="font-medium text-primary mb-1">关于模型配置</p>
                  <ul className="space-y-1 list-disc list-inside">
                    <li><strong>不配置</strong>：使用内置演示模式（Mock），可完整体验执行流程</li>
                    <li><strong>配置后</strong>：调用真实 LLM 模型，获得真实 AI 输出</li>
                    <li>支持所有 <strong>OpenAI 兼容</strong>接口</li>
                    <li>配置仅保存在浏览器本地，不会上传到服务器</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>

          {!configuredCount && (
            <Card className="border-accent-green/15 bg-accent-green-dim mb-4">
              <CardContent className="p-4"><div className="flex items-center gap-2 text-accent-green text-13"><CheckCircle className="w-4 h-4" /><span className="font-medium">当前使用演示模式（Mock）</span></div></CardContent>
            </Card>
          )}

          {Object.entries(config).map(([id, cfg]) => {
            const preset = PRESETS.find((p) => p.id === id);
            return (
              <Card key={id} className="mb-3">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div><CardTitle className="text-15 flex items-center gap-2"><Key className="w-4 h-4 text-secondary" />{preset?.name || id}</CardTitle><CardDescription>{preset?.desc || '自定义 OpenAI 兼容提供商'}</CardDescription></div>
                    <div className="flex items-center gap-2">
                      {cfg.api_key && <span className="text-xs bg-accent-green-dim text-accent-green px-2.5 py-1 rounded-full font-medium">已配置</span>}
                      {cfg.api_key && cfg.model && (() => {
                        const caps = getModelCapabilities(id, cfg.model);
                        if (!modelSupportsTools(id, cfg.model)) return <span className="inline-flex items-center gap-1 text-11 bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full font-medium"><XCircle className="w-3 h-3" /> 无工具支持</span>;
                        if (caps.includes('image_generation')) return <span className="inline-flex items-center gap-1 text-11 bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full font-medium"><Wrench className="w-3 h-3" /> 支持全部工具</span>;
                        return <span className="inline-flex items-center gap-1 text-11 bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full font-medium"><Wrench className="w-3 h-3" /> 支持基础工具</span>;
                      })()}
                      <button onClick={() => removeProvider(id)} className="text-secondary hover:text-accent-red transition-colors p-1 radius-sm hover:bg-accent-red-dim"><Trash2 className="w-4 h-4" /></button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div><label className="block text-xs font-medium text-secondary mb-1.5">Base URL</label><div className="flex items-center gap-2"><Globe className="w-4 h-4 text-secondary flex-shrink-0" /><input type="text" value={cfg.base_url} onChange={(e) => updateProvider(id, 'base_url', e.target.value)} placeholder="https://api.example.com/v1" className={inputClass} /></div></div>
                  <div><label className="block text-xs font-medium text-secondary mb-1.5">API Key</label><div className="relative"><input type={showKeys[id] ? 'text' : 'password'} value={cfg.api_key} onChange={(e) => updateProvider(id, 'api_key', e.target.value)} placeholder="sk-..." className={`w-full px-3 py-2.5 pr-10 border border-divider radius-md text-13 focus:ring-2 focus:ring-[var(--accent-primary)] focus:border-apple-blue outline-none transition-colors bg-white`} /><button type="button" onClick={() => setShowKeys((p) => ({ ...p, [id]: !p[id] }))} className="absolute right-2 top-1/2 -translate-y-1/2 text-secondary hover:text-primary p-1">{showKeys[id] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}</button></div></div>
                  <div><label className="block text-xs font-medium text-secondary mb-1.5">默认模型</label><input type="text" value={cfg.model} onChange={(e) => updateProvider(id, 'model', e.target.value)} placeholder="gpt-4o" className={inputClass} /></div>
                </CardContent>
              </Card>
            );
          })}

          {unconfiguredPresets.length > 0 && (
            <Card className="mb-3">
              <CardHeader><CardTitle className="text-sm">添加提供商</CardTitle></CardHeader>
              <CardContent><div className="flex flex-wrap gap-2">{unconfiguredPresets.map((p) => (<button key={p.id} onClick={() => addPreset(p)} className="px-4 py-2 text-13 bg-secondary border border-divider rounded-full text-primary hover:border-accent-primary hover:bg-white transition-all font-medium">+ {p.name}</button>))}</div></CardContent>
            </Card>
          )}

          <Card className="mb-3">
            <CardHeader><CardTitle className="text-sm">添加自定义提供商（OpenAI 兼容）</CardTitle></CardHeader>
            <CardContent><div className="flex gap-2"><input type="text" value={customName} onChange={(e) => setCustomName(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && addCustom()} placeholder="提供商名称（如 siliconflow）" className={inputClass} /><Button variant="outline" size="sm" onClick={addCustom}><Plus className="w-4 h-4 mr-1" /> 添加</Button></div></CardContent>
          </Card>

          <div className="flex justify-end gap-3">
            <button className="btn-secondary px-5 py-2.5 rounded-full" onClick={() => navigate('/')}>取消</button>
            <button className="btn-primary px-5 py-2.5 rounded-full" onClick={handleSave}>保存配置</button>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Settings;
