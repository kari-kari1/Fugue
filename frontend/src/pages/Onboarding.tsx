/**
 * 交互式新手教程 — 严格按报告第2章 Onboarding (5/10) + 第5章建议实现
 *
 * 报告要求:
 * - 分步向导: Step1 选择场景 → Step2 导入模板 → Step3 配置LLM → Step4 创建Agent → Step5 运行 → Step6 结果查看
 * - 添加"跳过"选项
 * - 引入新手教程模式
 */

import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';
import { t } from '../lib/i18n';
import { useTutorialStore } from '../stores/tutorialStore';

// ─── 步骤定义 ──────────────────────────────────────────────────────────────

const STEPS = [
  { id: 1, title: t('onboarding.steps.0.title'), description: t('onboarding.steps.0.desc') },
  { id: 2, title: t('onboarding.steps.1.title'), description: t('onboarding.steps.1.desc') },
  { id: 3, title: t('onboarding.steps.2.title'), description: t('onboarding.steps.2.desc') },
  { id: 4, title: t('onboarding.steps.3.title'), description: t('onboarding.steps.3.desc') },
  { id: 5, title: t('onboarding.steps.4.title'), description: t('onboarding.steps.4.desc') },
  { id: 6, title: t('onboarding.steps.5.title'), description: t('onboarding.steps.5.desc') },
  { id: 7, title: t('onboarding.steps.6.title'), description: t('onboarding.steps.6.desc') },
];

type Scenario = 'research' | 'coding' | 'writing' | 'data' | 'custom';

const SCENARIOS: { id: Scenario; icon: string; title: string; desc: string }[] = [
  { id: 'research', icon: '🔍', title: t('onboarding.scenarios.research.title'), desc: t('onboarding.scenarios.research.desc') },
  { id: 'coding', icon: '💻', title: t('onboarding.scenarios.coding.title'), desc: t('onboarding.scenarios.coding.desc') },
  { id: 'writing', icon: '✍️', title: t('onboarding.scenarios.writing.title'), desc: t('onboarding.scenarios.writing.desc') },
  { id: 'data', icon: '📊', title: t('onboarding.scenarios.data.title'), desc: t('onboarding.scenarios.data.desc') },
  { id: 'custom', icon: '⚙️', title: t('onboarding.scenarios.custom.title'), desc: t('onboarding.scenarios.custom.desc') },
];

const TEMPLATES: Record<Scenario, { key: string; agents: number; tasks: number }[]> = {
  research: [
    { key: 'onboarding.templates.research.0', agents: 3, tasks: 4 },
    { key: 'onboarding.templates.research.1', agents: 2, tasks: 3 },
  ],
  coding: [
    { key: 'onboarding.templates.coding.0', agents: 4, tasks: 5 },
    { key: 'onboarding.templates.coding.1', agents: 2, tasks: 3 },
  ],
  writing: [
    { key: 'onboarding.templates.writing.0', agents: 3, tasks: 4 },
    { key: 'onboarding.templates.writing.1', agents: 2, tasks: 3 },
  ],
  data: [
    { key: 'onboarding.templates.data.0', agents: 3, tasks: 4 },
    { key: 'onboarding.templates.data.1', agents: 2, tasks: 3 },
  ],
  custom: [],
};

// ─── 组件 ──────────────────────────────────────────────────────────────────

export default function Onboarding() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [apiKey, setApiKey] = useState('');
  const [provider, setProvider] = useState('openai');
  const [agentName, setAgentName] = useState('');
  const [isTutorialMode, setIsTutorialMode] = useState(true);
  const [isCompleting, setIsCompleting] = useState(false);

  const completeOnboarding = useTutorialStore((s) => s.completeOnboarding);
  const setTutorialMode = useTutorialStore((s) => s.setTutorialMode);

  const canProceed = useCallback(() => {
    switch (currentStep) {
      case 1: return scenarios.length > 0;
      case 2: return true; // 模板可选
      case 3: return apiKey.trim().length > 0;
      case 4: return agentName.trim().length > 0;
      default: return true;
    }
  }, [currentStep, scenarios, apiKey, agentName]);

  const handleNext = () => {
    if (currentStep < STEPS.length) {
      setCurrentStep(currentStep + 1);
    } else {
      handleComplete();
    }
  };

  const handleBack = () => {
    if (currentStep > 1) setCurrentStep(currentStep - 1);
  };

  const handleSkip = () => {
    completeOnboarding();
    setTutorialMode(false);
    navigate('/');
    toast(t('onboarding.skip_toast'), { icon: '💡' });
  };

  const handleComplete = async () => {
    setIsCompleting(true);
    try {
      // 1. 保存 LLM API Key 到正确的存储位置
      const { saveLLMConfig, getLLMConfig } = await import('../lib/llmKeys');
      const config = getLLMConfig();
      config[provider] = {
        api_key: apiKey,
        base_url: '',
        model: provider === 'openai' ? 'gpt-4o-mini' : provider === 'anthropic' ? 'claude-sonnet-4-20250514' : 'gemini-1.5-flash',
      };
      saveLLMConfig(config);

      // 2. 通过 API 创建第一个工作流 (Crew)
      const { apiClient } = await import('../api/client');
      let crewId: string | null = null;
      try {
        const crewRes = await apiClient.post('/crews/', {
          name: agentName
            ? t('onboarding.crew_workflow_name', { name: agentName })
            : t('onboarding.first_workflow_name'),
          description: t('onboarding.first_workflow_desc', { scenario: scenarios.join(', ') || 'custom' }),
          process: 'sequential',
        });
        crewId = crewRes.data.id;
      } catch (e) {
        console.warn('创建工作流失败，跳过:', e);
      }

      // 3. 如果有模板选择，尝试导入模板数据
      if (selectedTemplate && crewId) {
        try {
          await apiClient.post(`/crews/${crewId}/agents/`, {
            name: agentName || t('onboarding.first_agent_name'),
            role: t('onboarding.first_agent_role'),
            goal: t('onboarding.first_agent_goal'),
            backstory: t('onboarding.first_agent_backstory'),
            llm_provider: provider,
            llm_model: config[provider].model,
          });
        } catch (e) {
          console.warn('创建Agent失败，跳过:', e);
        }
      }

      // 4. 保存完成状态 (Zustand store)
      completeOnboarding();
      if (isTutorialMode) {
        setTutorialMode(true);
      }

      toast.success(t('onboarding.config_saved'));

      // 5. 跳转到编辑器（如果有创建的工作流）或首页
      if (crewId) {
        navigate(`/crew/${crewId}`);
      } else {
        navigate('/');
      }
    } catch {
      toast.error(t('onboarding.config_save_failed'));
    } finally {
      setIsCompleting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 flex flex-col">
      {/* 顶部栏 */}
      <header className="flex items-center justify-between px-8 py-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">A</span>
          </div>
          <span className="text-white font-semibold">Fugue</span>
        </div>
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
            <input
              type="checkbox"
              checked={isTutorialMode}
              onChange={(e) => setIsTutorialMode(e.target.checked)}
              className="rounded border-gray-600"
              aria-label={t('onboarding.tutorial_mode_label')}
            />
            {t('onboarding.tutorial_mode_label')}
          </label>
          <button
            onClick={handleSkip}
            className="text-sm text-gray-400 hover:text-white transition-colors"
            aria-label={t('common.skip')}
          >
            {t('common.skip')}
          </button>
        </div>
      </header>

      {/* 步骤指示器 */}
      <nav className="flex justify-center px-8 py-6" aria-label="配置步骤">
        <div className="flex items-center gap-2">
          {STEPS.map((step, i) => (
            <React.Fragment key={step.id}>
              <button
                onClick={() => step.id <= currentStep && setCurrentStep(step.id)}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-all ${
                  step.id === currentStep
                    ? 'bg-blue-600 text-white'
                    : step.id < currentStep
                    ? 'bg-blue-600/20 text-blue-400 cursor-pointer hover:bg-blue-600/30'
                    : 'bg-gray-800 text-gray-500 cursor-default'
                }`}
                disabled={step.id > currentStep}
                aria-current={step.id === currentStep ? 'step' : undefined}
              >
                <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                  step.id < currentStep ? 'bg-blue-500 text-white' : ''
                }`}>
                  {step.id < currentStep ? '✓' : step.id}
                </span>
                <span className="hidden md:inline">{step.title}</span>
              </button>
              {i < STEPS.length - 1 && (
                <div className={`w-8 h-0.5 ${step.id < currentStep ? 'bg-blue-500' : 'bg-gray-700'}`} />
              )}
            </React.Fragment>
          ))}
        </div>
      </nav>

      {/* 步骤内容 */}
      <main className="flex-1 flex items-center justify-center px-4 pb-24">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="w-full max-w-2xl"
          >
            {currentStep === 1 && (
              <StepScenario scenarios={scenarios} onToggle={(s) => setScenarios((prev) => prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s])} />
            )}
            {currentStep === 2 && (
              <StepTemplate scenarios={scenarios} selected={selectedTemplate} onSelect={setSelectedTemplate} onSkip={handleNext} />
            )}
            {currentStep === 3 && (
              <StepLLM provider={provider} apiKey={apiKey} onProviderChange={setProvider} onKeyChange={setApiKey} onSkip={handleNext} />
            )}
            {currentStep === 4 && (
              <StepAgent name={agentName} onChange={setAgentName} />
            )}
            {currentStep === 5 && (
              <StepRun tutorialMode={isTutorialMode} />
            )}
            {currentStep === 6 && (
              <StepResult />
            )}
            {currentStep === 7 && (
              <StepPreferences tutorialMode={isTutorialMode} setTutorialMode={setIsTutorialMode} />
            )}
          </motion.div>
        </AnimatePresence>
      </main>

      {/* 底部导航 */}
      <footer className="fixed bottom-0 inset-x-0 bg-gray-900/80 backdrop-blur-md border-t border-gray-800 px-8 py-4">
        <div className="max-w-2xl mx-auto flex justify-between">
          <button
            onClick={handleBack}
            disabled={currentStep === 1}
            className="px-6 py-2.5 text-gray-400 hover:text-white disabled:opacity-30 disabled:cursor-default transition-colors"
          >
            {t('common.prev_step')}
          </button>
          <button
            onClick={handleNext}
            disabled={!canProceed() || isCompleting}
            className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium
                       disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {isCompleting ? t('common.saving') : currentStep >= 6 ? t('common.start_using') : t('common.next_step')}
          </button>
        </div>
      </footer>
    </div>
  );
}

// ─── Step 1: 选择场景 ─────────────────────────────────────────────────────

function StepScenario({ scenarios, onToggle }: { scenarios: Scenario[]; onToggle: (s: Scenario) => void }) {
  return (
    <div>
      <h2 className="text-2xl font-bold text-white mb-2">{t('onboarding.step1.heading')}</h2>
      <p className="text-gray-400 mb-2">{t('onboarding.step1.subheading')}</p>
      <p className="text-xs text-blue-400 mb-6">{t('common.multi_select_hint')}</p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {SCENARIOS.map((s) => (
          <button
            key={s.id}
            onClick={() => onToggle(s.id)}
            className={`p-5 rounded-xl border text-left transition-all ${
              scenarios.includes(s.id)
                ? 'border-blue-500 bg-blue-500/10 ring-1 ring-blue-500/50'
                : 'border-gray-700 bg-gray-800/50 hover:border-gray-600'
            }`}
            aria-pressed={scenarios.includes(s.id)}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-2xl">{s.icon}</span>
              {scenarios.includes(s.id) && (
                <span className="w-5 h-5 rounded bg-blue-500 flex items-center justify-center text-xs text-white">✓</span>
              )}
            </div>
            <span className="text-white font-semibold block mb-1">{s.title}</span>
            <span className="text-sm text-gray-400">{s.desc}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

// ─── Step 2: 导入模板 ─────────────────────────────────────────────────────

function StepTemplate({ scenarios, selected, onSelect, onSkip }: {
  scenarios: Scenario[]; selected: string | null; onSelect: (t: string | null) => void; onSkip: () => void;
}) {
  const templates = scenarios.flatMap((s) => TEMPLATES[s] || []);
  const uniqueTemplates = templates.filter((t, i, arr) => arr.findIndex((x) => x.key === t.key) === i);

  return (
    <div>
      <h2 className="text-2xl font-bold text-white mb-2">{t('onboarding.step2.heading')}</h2>
      <p className="text-gray-400 mb-8">{t('onboarding.step2.subheading')}</p>
      {uniqueTemplates.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <p className="text-lg mb-2">{t('onboarding.step2.custom_mode_title')}</p>
          <p className="text-sm">{t('onboarding.step2.custom_mode_desc')}</p>
        </div>
      ) : (
        <div className="space-y-3">
          {uniqueTemplates.map((tmpl) => (
            <button
              key={tmpl.key}
              onClick={() => onSelect(selected === tmpl.key ? null : tmpl.key)}
              className={`w-full p-4 rounded-xl border text-left transition-all flex items-center justify-between ${
                selected === tmpl.key
                  ? 'border-blue-500 bg-blue-500/10'
                  : 'border-gray-700 bg-gray-800/50 hover:border-gray-600'
              }`}
            >
              <div>
                <span className="text-white font-medium">{t(tmpl.key)}</span>
                <span className="text-sm text-gray-400 ml-3">
                  {t('common.agents_count', { count: tmpl.agents })} · {t('common.tasks_count', { count: tmpl.tasks })}
                </span>
              </div>
              {selected === tmpl.key && <span className="text-blue-400">✓ {t('common.selected')}</span>}
            </button>
          ))}
        </div>
      )}
      <button
        onClick={onSkip}
        className="mt-4 text-sm text-gray-500 hover:text-gray-300 transition-colors"
      >
        {t('onboarding.step2.skip_later')} →
      </button>
    </div>
  );
}

// ─── Step 3: 配置 LLM ─────────────────────────────────────────────────────

function StepLLM({ provider, apiKey, onProviderChange, onKeyChange, onSkip }: {
  provider: string; apiKey: string;
  onProviderChange: (p: string) => void; onKeyChange: (k: string) => void; onSkip: () => void;
}) {
  const providers = [
    { id: 'openai', name: 'OpenAI', placeholder: 'sk-...' },
    { id: 'anthropic', name: 'Anthropic', placeholder: 'sk-ant-...' },
    { id: 'google', name: 'Google AI', placeholder: 'AIza...' },
  ];

  return (
    <div>
      <h2 className="text-2xl font-bold text-white mb-2">{t('onboarding.step3.heading')}</h2>
      <p className="text-gray-400 mb-8">{t('onboarding.step3.subheading')}</p>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-3">{t('onboarding.step3.select_provider')}</label>
          <div className="flex gap-3">
            {providers.map((p) => (
              <button
                key={p.id}
                onClick={() => onProviderChange(p.id)}
                className={`flex-1 py-3 px-4 rounded-lg border text-sm font-medium transition-all ${
                  provider === p.id
                    ? 'border-blue-500 bg-blue-500/10 text-blue-400'
                    : 'border-gray-700 bg-gray-800 text-gray-300 hover:border-gray-600'
                }`}
              >
                {p.name}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label htmlFor="api-key" className="block text-sm font-medium text-gray-300 mb-2">
            {t('onboarding.step3.api_key_label')}
          </label>
          <input
            id="api-key"
            type="password"
            value={apiKey}
            onChange={(e) => onKeyChange(e.target.value)}
            placeholder={providers.find(p => p.id === provider)?.placeholder || ''}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg
                       text-white placeholder-gray-500 focus:outline-none focus:ring-2
                       focus:ring-blue-500 focus:border-blue-500 transition-all"
            aria-required="true"
          />
          <p className="mt-2 text-xs text-gray-500">
            {t('onboarding.step3.key_local_notice')}
          </p>
        </div>
      </div>
      <button
        onClick={onSkip}
        className="mt-6 text-sm text-gray-500 hover:text-gray-300 transition-colors"
      >
        {t('onboarding.step3.skip_later')} →
      </button>
    </div>
  );
}

// ─── Step 4: 创建 Agent ───────────────────────────────────────────────────

function StepAgent({ name, onChange }: { name: string; onChange: (n: string) => void }) {
  return (
    <div>
      <h2 className="text-2xl font-bold text-white mb-2">{t('onboarding.step4.heading')}</h2>
      <p className="text-gray-400 mb-8">{t('onboarding.step4.subheading')}</p>

      <div className="space-y-6">
        <div>
          <label htmlFor="agent-name" className="block text-sm font-medium text-gray-300 mb-2">
            {t('onboarding.step4.agent_name_label')}
          </label>
          <input
            id="agent-name"
            type="text"
            value={name}
            onChange={(e) => onChange(e.target.value)}
            placeholder={t('onboarding.step4.agent_name_placeholder')}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg
                       text-white placeholder-gray-500 focus:outline-none focus:ring-2
                       focus:ring-blue-500 focus:border-blue-500 transition-all"
            aria-required="true"
            maxLength={50}
          />
        </div>

        <div className="bg-gray-800/50 rounded-xl p-5 border border-gray-700">
          <h3 className="text-sm font-medium text-gray-300 mb-3">💡 {t('onboarding.step4.tips_title')}</h3>
          <ul className="text-sm text-gray-400 space-y-2">
            <li>• {t('onboarding.step4.tip1')}</li>
            <li>• {t('onboarding.step4.tip2')}</li>
            <li>• {t('onboarding.step4.tip3')}</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

// ─── Step 5: 运行演示 ─────────────────────────────────────────────────────

function StepRun({ tutorialMode }: { tutorialMode: boolean }) {
  return (
    <div>
      <h2 className="text-2xl font-bold text-white mb-2">{t('onboarding.step5.heading')}</h2>
      <p className="text-gray-400 mb-8">{t('onboarding.step5.subheading')}</p>

      <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700 space-y-4">
        <div className="flex items-start gap-3">
          <span className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-sm font-bold text-white shrink-0">1</span>
          <div>
            <p className="text-white font-medium">{t('onboarding.step5.item1_title')}</p>
            <p className="text-sm text-gray-400">{t('onboarding.step5.item1_desc')}</p>
          </div>
        </div>
        <div className="flex items-start gap-3">
          <span className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-sm font-bold text-white shrink-0">2</span>
          <div>
            <p className="text-white font-medium">{t('onboarding.step5.item2_title')}</p>
            <p className="text-sm text-gray-400">{t('onboarding.step5.item2_desc')}</p>
          </div>
        </div>
        <div className="flex items-start gap-3">
          <span className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-sm font-bold text-white shrink-0">3</span>
          <div>
            <p className="text-white font-medium">{t('onboarding.step5.item3_title')}</p>
            <p className="text-sm text-gray-400">{t('onboarding.step5.item3_desc')}</p>
          </div>
        </div>
      </div>

      {tutorialMode && (
        <div className="mt-6 p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl">
          <p className="text-sm text-amber-300">
            <strong>🎓 {t('onboarding.tutorial_mode_label')}</strong> — {t('onboarding.step5.tutorial_banner')}
          </p>
        </div>
      )}
    </div>
  );
}

// ─── Step 6: 完成 ──────────────────────────────────────────────────────────

function StepResult() {
  return (
    <div className="text-center">
      <div className="w-20 h-20 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
        <span className="text-4xl">🎉</span>
      </div>
      <h2 className="text-2xl font-bold text-white mb-2">{t('onboarding.step6.heading')}</h2>
      <p className="text-gray-400 mb-8 max-w-md mx-auto">
        {t('onboarding.step6.subheading')}
      </p>

      <div className="grid grid-cols-2 gap-4 max-w-md mx-auto text-left">
        <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
          <p className="text-white font-medium mb-1">📐 {t('onboarding.step6.card1_title')}</p>
          <p className="text-xs text-gray-400">{t('onboarding.step6.card1_desc')}</p>
        </div>
        <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
          <p className="text-white font-medium mb-1">📚 {t('onboarding.step6.card2_title')}</p>
          <p className="text-xs text-gray-400">{t('onboarding.step6.card2_desc')}</p>
        </div>
        <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
          <p className="text-white font-medium mb-1">🔌 {t('onboarding.step6.card3_title')}</p>
          <p className="text-xs text-gray-400">{t('onboarding.step6.card3_desc')}</p>
        </div>
        <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
          <p className="text-white font-medium mb-1">📖 {t('onboarding.step6.card4_title')}</p>
          <p className="text-xs text-gray-400">{t('onboarding.step6.card4_desc')}</p>
        </div>
      </div>
    </div>
  );
}


// ─── Step 7: 个性化设置 ─────────────────────────────────────────────────────

function StepPreferences({ tutorialMode, setTutorialMode }: { tutorialMode: boolean; setTutorialMode: (v: boolean) => void }) {
  return (
    <div className="text-center">
      <div className="w-20 h-20 bg-purple-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
        <span className="text-4xl">⚙️</span>
      </div>
      <h2 className="text-2xl font-bold text-white mb-2">{t('onboarding.step7.heading')}</h2>
      <p className="text-gray-400 mb-8 max-w-md mx-auto">
        {t('onboarding.step7.subheading')}
      </p>

      <div className="max-w-md mx-auto space-y-4 text-left">
        <label className="flex items-center justify-between bg-gray-800/50 rounded-xl p-4 border border-gray-700">
          <div>
            <p className="text-white font-medium">🎓 {t('onboarding.step7.guided_tips_label')}</p>
            <p className="text-xs text-gray-400">{t('onboarding.step7.guided_tips_desc')}</p>
          </div>
          <input
            type="checkbox"
            checked={tutorialMode}
            onChange={(e) => setTutorialMode(e.target.checked)}
            className="w-5 h-5 rounded accent-blue-600"
            aria-label={t('onboarding.step7.guided_tips_label')}
          />
        </label>

        <label className="flex items-center justify-between bg-gray-800/50 rounded-xl p-4 border border-gray-700">
          <div>
            <p className="text-white font-medium">🔔 {t('onboarding.step7.notifications_label')}</p>
            <p className="text-xs text-gray-400">{t('onboarding.step7.notifications_desc')}</p>
          </div>
          <input
            type="checkbox"
            defaultChecked={true}
            className="w-5 h-5 rounded accent-blue-600"
            aria-label={t('onboarding.step7.notifications_label')}
          />
        </label>
      </div>
    </div>
  );
}
