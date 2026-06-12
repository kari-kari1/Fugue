/* Onboarding — 首次运行引导
 * 流程：欢迎 → 配置 API Key → 完成
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Key, ArrowRight, ArrowLeft, CheckCircle, Sparkles, ExternalLink } from 'lucide-react';
import toast from 'react-hot-toast';
import { hasConfiguredKeys, saveLLMConfig, getLLMConfig } from '../lib/llmKeys';

type Step = 'welcome' | 'api-key' | 'done';

const PROVIDERS = [
  { id: 'openai', name: 'OpenAI', placeholder: 'sk-...', url: 'https://platform.openai.com/api-keys', defaultModel: 'gpt-4o' },
  { id: 'anthropic', name: 'Anthropic', placeholder: 'sk-ant-...', url: 'https://console.anthropic.com/', defaultModel: 'claude-sonnet-4-20250514' },
  { id: 'deepseek', name: 'DeepSeek', placeholder: 'sk-...', url: 'https://platform.deepseek.com/', defaultModel: 'deepseek-chat', baseUrl: 'https://api.deepseek.com/v1' },
];

const spring = { type: 'spring' as const, stiffness: 300, damping: 30 };

export default function Onboarding() {
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>('welcome');
  const [selectedProvider, setSelectedProvider] = useState('openai');
  const [apiKey, setApiKey] = useState('');
  const [showKey, setShowKey] = useState(false);

  // 已有配置则跳过
  if (hasConfiguredKeys()) {
    navigate('/', { replace: true });
    return null;
  }

  const handleSaveKey = () => {
    if (!apiKey.trim()) {
      toast.error('请输入 API Key');
      return;
    }
    const provider = PROVIDERS.find((p) => p.id === selectedProvider)!;
    const existing = getLLMConfig();
    existing[selectedProvider] = {
      api_key: apiKey.trim(),
      base_url: provider.baseUrl || '',
      model: provider.defaultModel,
    };
    saveLLMConfig(existing);
    toast.success(`${provider.name} API Key 已保存`);
    setStep('done');
  };

  const handleSkip = () => {
    setStep('done');
  };

  const handleFinish = () => {
    navigate('/', { replace: true });
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'var(--bg-page, #F5F5F7)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '40px 24px',
        fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif',
      }}
    >
      <div style={{ width: '100%', maxWidth: 520 }}>
        <AnimatePresence mode="wait">
          {step === 'welcome' && (
            <motion.div
              key="welcome"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -30 }}
              transition={spring}
              style={{
                background: 'rgba(255,255,255,0.6)',
                backdropFilter: 'blur(40px) saturate(1.8)',
                WebkitBackdropFilter: 'blur(40px) saturate(1.8)',
                borderRadius: 24,
                border: '0.5px solid rgba(255,255,255,0.8)',
                boxShadow: '0 2px 20px rgba(0,0,0,0.04), inset 0 1px 0 rgba(255,255,255,0.8)',
                padding: '48px 40px',
                textAlign: 'center',
              }}
            >
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ ...spring, delay: 0.1 }}
                style={{
                  width: 72, height: 72, borderRadius: 20,
                  background: 'linear-gradient(135deg, #0071E3 0%, #2997FF 100%)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  margin: '0 auto 24px',
                }}
              >
                <Sparkles size={32} color="#fff" />
              </motion.div>

              <h1 style={{
                fontSize: 28, fontWeight: 700, color: 'var(--text-primary, #1D1D1F)',
                letterSpacing: '-0.02em', marginBottom: 8,
              }}>
                欢迎使用 Fugue
              </h1>
              <p style={{
                fontSize: 16, color: 'var(--text-secondary, #86868B)',
                lineHeight: 1.5, marginBottom: 36, maxWidth: 380, margin: '0 auto 36px',
              }}>
                多智能体协作工作流平台。只需一步配置，即可开始构建你的 AI 工作流。
              </p>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setStep('api-key')}
                style={{
                  width: '100%', height: 50,
                  background: 'linear-gradient(135deg, #0071E3 0%, #2997FF 100%)',
                  color: '#fff', border: 'none', borderRadius: 14,
                  fontSize: 16, fontWeight: 600, cursor: 'pointer',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                  boxShadow: '0 2px 12px rgba(0,113,227,0.3)',
                }}
              >
                开始配置 <ArrowRight size={18} />
              </motion.button>

              <button
                onClick={handleSkip}
                style={{
                  background: 'none', border: 'none', color: '#86868B',
                  fontSize: 14, cursor: 'pointer', marginTop: 16, padding: '8px 16px',
                }}
              >
                跳过，稍后配置
              </button>
            </motion.div>
          )}

          {step === 'api-key' && (
            <motion.div
              key="api-key"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -30 }}
              transition={spring}
              style={{
                background: 'rgba(255,255,255,0.6)',
                backdropFilter: 'blur(40px) saturate(1.8)',
                WebkitBackdropFilter: 'blur(40px) saturate(1.8)',
                borderRadius: 24,
                border: '0.5px solid rgba(255,255,255,0.8)',
                boxShadow: '0 2px 20px rgba(0,0,0,0.04), inset 0 1px 0 rgba(255,255,255,0.8)',
                padding: '40px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
                <div style={{
                  width: 40, height: 40, borderRadius: 12,
                  background: 'linear-gradient(135deg, #0071E3 0%, #2997FF 100%)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <Key size={20} color="#fff" />
                </div>
                <h2 style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary, #1D1D1F)', margin: 0 }}>
                  配置 LLM API Key
                </h2>
              </div>
              <p style={{ fontSize: 14, color: 'var(--text-secondary, #86868B)', marginBottom: 28 }}>
                选择一个 AI 服务商并输入 API Key。配置保存在本地浏览器中，不会上传到服务器。
              </p>

              {/* Provider 选择 */}
              <div style={{ display: 'flex', gap: 8, marginBottom: 24, flexWrap: 'wrap' }}>
                {PROVIDERS.map((p) => (
                  <motion.button
                    key={p.id}
                    whileHover={{ scale: 1.03 }}
                    whileTap={{ scale: 0.97 }}
                    onClick={() => setSelectedProvider(p.id)}
                    style={{
                      padding: '10px 20px', borderRadius: 12,
                      border: selectedProvider === p.id
                        ? '2px solid #0071E3'
                        : '1px solid var(--border-divider, #E5E5EA)',
                      background: selectedProvider === p.id
                        ? 'rgba(0,113,227,0.08)'
                        : 'rgba(255,255,255,0.5)',
                      color: selectedProvider === p.id ? '#0071E3' : 'var(--text-primary, #1D1D1F)',
                      fontSize: 14, fontWeight: selectedProvider === p.id ? 600 : 400,
                      cursor: 'pointer',
                    }}
                  >
                    {p.name}
                  </motion.button>
                ))}
              </div>

              {/* API Key 输入 */}
              <div style={{ marginBottom: 16 }}>
                <label style={{
                  display: 'block', fontSize: 13, fontWeight: 500,
                  color: 'var(--text-primary, #1D1D1F)', marginBottom: 6,
                }}>
                  API Key
                </label>
                <div style={{ position: 'relative' }}>
                  <input
                    type={showKey ? 'text' : 'password'}
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder={PROVIDERS.find((p) => p.id === selectedProvider)?.placeholder || 'sk-...'}
                    style={{
                      width: '100%', height: 48,
                      background: 'rgba(255,255,255,0.5)',
                      border: '1px solid var(--border-divider, #E5E5EA)',
                      borderRadius: 12, fontSize: 15,
                      padding: '0 48px 0 16px', outline: 'none',
                      color: 'var(--text-primary, #1D1D1F)',
                    }}
                    onFocus={(e) => { e.currentTarget.style.borderColor = '#0071E3'; }}
                    onBlur={(e) => { e.currentTarget.style.borderColor = 'var(--border-divider, #E5E5EA)'; }}
                  />
                  <button
                    onClick={() => setShowKey(!showKey)}
                    style={{
                      position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
                      background: 'none', border: 'none', cursor: 'pointer',
                      color: '#86868B', padding: 4,
                    }}
                  >
                    {showKey ? '🙈' : '👁'}
                  </button>
                </div>
              </div>

              {/* 获取 Key 链接 */}
              <a
                href={PROVIDERS.find((p) => p.id === selectedProvider)?.url}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  display: 'inline-flex', alignItems: 'center', gap: 4,
                  fontSize: 13, color: '#0071E3', textDecoration: 'none',
                  marginBottom: 28,
                }}
              >
                前往获取 API Key <ExternalLink size={12} />
              </a>

              {/* 按钮 */}
              <div style={{ display: 'flex', gap: 12 }}>
                <button
                  onClick={() => setStep('welcome')}
                  style={{
                    height: 48, padding: '0 20px', borderRadius: 12,
                    border: '1px solid var(--border-divider, #E5E5EA)',
                    background: 'rgba(255,255,255,0.5)',
                    color: 'var(--text-primary, #1D1D1F)',
                    fontSize: 15, cursor: 'pointer',
                    display: 'flex', alignItems: 'center', gap: 6,
                  }}
                >
                  <ArrowLeft size={16} /> 返回
                </button>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleSaveKey}
                  style={{
                    flex: 1, height: 48,
                    background: 'linear-gradient(135deg, #0071E3 0%, #2997FF 100%)',
                    color: '#fff', border: 'none', borderRadius: 12,
                    fontSize: 15, fontWeight: 600, cursor: 'pointer',
                    boxShadow: '0 2px 12px rgba(0,113,227,0.3)',
                  }}
                >
                  保存并继续
                </motion.button>
              </div>

              <button
                onClick={handleSkip}
                style={{
                  background: 'none', border: 'none', color: '#86868B',
                  fontSize: 13, cursor: 'pointer', marginTop: 16, width: '100%', textAlign: 'center',
                }}
              >
                跳过，稍后在设置中配置
              </button>
            </motion.div>
          )}

          {step === 'done' && (
            <motion.div
              key="done"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -30 }}
              transition={spring}
              style={{
                background: 'rgba(255,255,255,0.6)',
                backdropFilter: 'blur(40px) saturate(1.8)',
                WebkitBackdropFilter: 'blur(40px) saturate(1.8)',
                borderRadius: 24,
                border: '0.5px solid rgba(255,255,255,0.8)',
                boxShadow: '0 2px 20px rgba(0,0,0,0.04), inset 0 1px 0 rgba(255,255,255,0.8)',
                padding: '48px 40px',
                textAlign: 'center',
              }}
            >
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ ...spring, delay: 0.1 }}
                style={{
                  width: 72, height: 72, borderRadius: '50%',
                  background: 'linear-gradient(135deg, #34C759 0%, #30D158 100%)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  margin: '0 auto 24px',
                }}
              >
                <CheckCircle size={36} color="#fff" />
              </motion.div>

              <h2 style={{
                fontSize: 24, fontWeight: 700, color: 'var(--text-primary, #1D1D1F)',
                marginBottom: 8,
              }}>
                {hasConfiguredKeys() ? '配置完成！' : '准备就绪'}
              </h2>
              <p style={{
                fontSize: 15, color: 'var(--text-secondary, #86868B)',
                lineHeight: 1.5, marginBottom: 32, maxWidth: 360, margin: '0 auto 32px',
              }}>
                {hasConfiguredKeys()
                  ? 'API Key 已保存。你现在可以创建和运行 AI 工作流了。'
                  : '你可以随时在「设置」中配置 API Key。使用 Mock 模式可以体验基本功能。'}
              </p>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleFinish}
                style={{
                  width: '100%', height: 50,
                  background: 'linear-gradient(135deg, #0071E3 0%, #2997FF 100%)',
                  color: '#fff', border: 'none', borderRadius: 14,
                  fontSize: 16, fontWeight: 600, cursor: 'pointer',
                  boxShadow: '0 2px 12px rgba(0,113,227,0.3)',
                }}
              >
                进入 Fugue
              </motion.button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* 底部进度指示 */}
        <div style={{
          display: 'flex', justifyContent: 'center', gap: 8, marginTop: 32,
        }}>
          {(['welcome', 'api-key', 'done'] as Step[]).map((s) => (
            <motion.div
              key={s}
              animate={{
                width: step === s ? 24 : 8,
                background: step === s ? '#0071E3' : '#D1D1D6',
              }}
              transition={spring}
              style={{ height: 4, borderRadius: 2 }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
