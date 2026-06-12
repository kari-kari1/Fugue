/* Login — 视频开场 + 毛玻璃登录框
 * 流程：加载 → 播放视频 → 视频结束暂停 → 登录框自下而上浮现
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'react-hot-toast';
import { useAuthStore } from '../stores/authStore';
import { hasConfiguredKeys } from '../lib/llmKeys';
import { StaggerList, StaggerItem } from '../components/motion/StaggerList';

/* ===== Hero Cycling Text ===== */

const heroPhrases = [
  'Research Agent',
  'Code Review',
  'Data Pipeline',
  'Report Generator',
  'Team Orchestrator',
];

const HeroLogo = () => (
  <motion.svg
    width="64" height="64" viewBox="0 0 56 56" fill="none"
    initial={{ opacity: 0, scale: 0.8 }}
    animate={{ opacity: 1, scale: 1 }}
    transition={{ type: 'spring', stiffness: 200, damping: 20, delay: 0.2 }}
    aria-hidden="true"
  >
    <circle cx="28" cy="28" r="26" stroke="#0071E3" strokeWidth="2" opacity="0.2" />
    <circle cx="28" cy="28" r="5" fill="#0071E3" />
    <circle cx="28" cy="10" r="3.5" fill="#0071E3" opacity="0.6" />
    <circle cx="43.5" cy="20" r="3.5" fill="#0071E3" opacity="0.6" />
    <circle cx="43.5" cy="38" r="3.5" fill="#0071E3" opacity="0.6" />
    <circle cx="28" cy="48" r="3.5" fill="#0071E3" opacity="0.6" />
    <circle cx="12.5" cy="38" r="3.5" fill="#0071E3" opacity="0.6" />
    <circle cx="12.5" cy="20" r="3.5" fill="#0071E3" opacity="0.6" />
    <line x1="28" y1="23" x2="28" y2="13" stroke="#0071E3" strokeWidth="1.5" opacity="0.35" />
    <line x1="32.5" y1="25.5" x2="40.5" y2="21.5" stroke="#0071E3" strokeWidth="1.5" opacity="0.35" />
    <line x1="32.5" y1="32" x2="40.5" y2="36.5" stroke="#0071E3" strokeWidth="1.5" opacity="0.35" />
    <line x1="28" y1="33" x2="28" y2="45" stroke="#0071E3" strokeWidth="1.5" opacity="0.35" />
    <line x1="23.5" y1="32" x2="15.5" y2="36.5" stroke="#0071E3" strokeWidth="1.5" opacity="0.35" />
    <line x1="23.5" y1="25.5" x2="15.5" y2="21.5" stroke="#0071E3" strokeWidth="1.5" opacity="0.35" />
    <circle cx="28" cy="28" r="5" fill="#0071E3" opacity="0.3">
      <animate attributeName="r" values="5;10;5" dur="3s" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0.3;0;0.3" dur="3s" repeatCount="indefinite" />
    </circle>
  </motion.svg>
);

const HeroCyclingText = () => {
  const [index, setIndex] = useState(0);
  const advance = useCallback(() => setIndex((p) => (p + 1) % heroPhrases.length), []);
  useEffect(() => { const t = setInterval(advance, 2800); return () => clearInterval(t); }, [advance]);

  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      position: 'relative',
      minWidth: '240px',
      height: '1em',
      overflow: 'hidden',
      verticalAlign: 'baseline',
    }}>
      <AnimatePresence mode="wait">
        <motion.span
          key={heroPhrases[index]}
          initial={{ y: '100%', opacity: 0, filter: 'blur(4px)' }}
          animate={{ y: '0%', opacity: 1, filter: 'blur(0px)' }}
          exit={{ y: '-100%', opacity: 0, filter: 'blur(4px)' }}
          transition={{ type: 'spring', stiffness: 260, damping: 28, mass: 0.8 }}
          style={{
            position: 'absolute',
            left: 0,
            top: 0,
            display: 'flex',
            alignItems: 'center',
            height: '100%',
            whiteSpace: 'nowrap',
            color: '#0071E3',
          }}
        >
          {heroPhrases[index]}
        </motion.span>
      </AnimatePresence>
    </span>
  );
};

/* ===== Loading Spinner ===== */

const LoadingSpinner = () => (
  <motion.div
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    exit={{ opacity: 0 }}
    style={{
      position: 'absolute', inset: 0,
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      background: '#000000', zIndex: 10,
    }}
  >
    <motion.div
      animate={{ rotate: 360 }}
      transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
      style={{
        width: 32, height: 32,
        border: '2px solid rgba(255,255,255,0.1)',
        borderTopColor: '#0071E3',
        borderRadius: '50%',
      }}
    />
    <p style={{ color: 'rgba(255,255,255,0.3)', fontSize: 12, marginTop: 16, fontFamily: '-apple-system, sans-serif' }}>
      Loading...
    </p>
  </motion.div>
);

/* ===== Main Login ===== */

type Phase = 'loading' | 'playing' | 'ready';

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isLoading } = useAuthStore();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const skipIntro = (location.state as { skipIntro?: boolean })?.skipIntro;
  const [phase, setPhase] = useState<Phase>(skipIntro ? 'ready' : 'loading');
  const videoRef = useRef<HTMLVideoElement>(null);

  // 视频可以播放时自动开始
  const handleCanPlay = useCallback(() => {
    if (!skipIntro) videoRef.current?.play().catch(() => {});
  }, [skipIntro]);

  // 视频播放结束 → 暂停在最后一帧 → 显示登录框
  const handleEnded = useCallback(() => {
    if (videoRef.current) videoRef.current.pause();
    setPhase('ready');
  }, []);

  // 视频开始播放 → 离开 loading 状态
  const handlePlaying = useCallback(() => {
    setPhase('playing');
  }, []);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(email, password);
      toast.success('登录成功');
      // 首次运行无 API Key 时跳转引导页
      navigate(hasConfiguredKeys() ? '/' : '/onboarding');
    } catch (error: unknown) {
      const axiosError = error as { response?: { data?: { detail?: string | Array<{ msg?: string }> | { msg?: string; message?: string } } } };
      const detail = axiosError.response?.data?.detail;
      let errorMessage = '登录失败';
      if (typeof detail === 'string') errorMessage = detail;
      else if (Array.isArray(detail)) errorMessage = detail.map((err) => err.msg || '验证错误').join('; ');
      else if (detail && typeof detail === 'object') errorMessage = detail.msg || detail.message || '请求参数错误';
      toast.error(errorMessage);
    }
  };

  const showUI = phase === 'ready';

  return (
    <div style={{
      position: 'fixed', inset: 0,
      background: '#000000',
      overflow: 'hidden',
    }}>

      {/* ===== 视频背景 ===== */}
      <video
        ref={videoRef}
        muted
        playsInline
        preload="auto"
        onCanPlayThrough={handleCanPlay}
        onPlaying={handlePlaying}
        onEnded={handleEnded}
        style={{
          position: 'absolute', inset: 0,
          width: '100%', height: '100%',
          objectFit: 'cover',
          zIndex: 0,
        }}
      >
        <source src="/login-bg.mp4" type="video/mp4" />
      </video>

      {/* ===== 加载遮罩 ===== */}
      <AnimatePresence>
        {phase === 'loading' && <LoadingSpinner />}
      </AnimatePresence>

      {/* ===== 跳过按钮 — loading/playing 阶段显示 ===== */}
      <AnimatePresence>
        {!showUI && phase !== 'loading' && (
          <motion.button
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3 }}
            onClick={() => {
              if (videoRef.current) videoRef.current.pause();
              setPhase('ready');
            }}
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            style={{
              position: 'absolute',
              top: 24, right: 24,
              zIndex: 20,
              background: 'rgba(255, 255, 255, 0.12)',
              WebkitBackdropFilter: 'blur(30px) saturate(1.8)',
              backdropFilter: 'blur(30px) saturate(1.8)',
              border: '0.5px solid rgba(255, 255, 255, 0.2)',
              borderRadius: 20,
              color: 'rgba(255, 255, 255, 0.7)',
              fontSize: 13,
              fontWeight: 500,
              padding: '8px 20px',
              cursor: 'pointer',
              fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif',
              letterSpacing: '-0.01em',
            }}
          >
            Skip
          </motion.button>
        )}
      </AnimatePresence>

      {/* ===== 视频上的暗色遮罩（提升登录框可读性） ===== */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: showUI ? 1 : 0 }}
        transition={{ duration: 0.8 }}
        style={{
          position: 'absolute', inset: 0,
          background: 'rgba(0,0,0,0.45)',
          zIndex: 1,
          pointerEvents: 'none',
        }}
      />

      {/* ===== 登录框 — 视频播完后自下而上浮现 ===== */}
      <AnimatePresence>
        {showUI && (
          <motion.div
            initial={{ opacity: 0, y: 60, filter: 'blur(8px)' }}
            animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
            exit={{ opacity: 0, y: 60 }}
            transition={{ type: 'spring', stiffness: 100, damping: 18, mass: 1 }}
            style={{
              position: 'absolute',
              inset: 0,
              zIndex: 2,
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
              padding: '40px 0',
            }}
          >
            {/* Logo + 标题 */}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: 32 }}>
              <HeroLogo />
              <h1 style={{
                fontSize: 'clamp(40px, 7vw, 72px)',
                fontWeight: 700,
                color: '#F5F5F7',
                lineHeight: 1.05,
                letterSpacing: '-0.025em',
                margin: '14px 0 6px',
                fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif',
              }}>
                Fugue
              </h1>
              <div style={{
                fontSize: 'clamp(20px, 3vw, 28px)',
                fontWeight: 400,
                color: 'rgba(255,255,255,0.5)',
                display: 'flex', alignItems: 'center', gap: 10,
                fontFamily: '-apple-system, sans-serif',
                lineHeight: 1,
              }}>
                <span>Automate</span>
                <HeroCyclingText />
              </div>
            </div>

            {/* 毛玻璃登录卡片 */}
            <div style={{ width: '100%', maxWidth: 380, padding: '0 24px' }}>
              {/* 外层光晕 */}
              <div style={{
                position: 'relative',
              }}>
                <div style={{
                  position: 'absolute', inset: -1,
                  borderRadius: 24,
                  background: 'linear-gradient(135deg, rgba(0,113,227,0.25) 0%, rgba(175,82,222,0.1) 50%, rgba(0,212,255,0.15) 100%)',
                  zIndex: 0,
                }} />

                {/* 毛玻璃卡片 */}
                <div style={{
                  position: 'relative', zIndex: 1,
                  background: 'rgba(15, 15, 20, 0.55)',
                  WebkitBackdropFilter: 'blur(50px) saturate(2)',
                  backdropFilter: 'blur(50px) saturate(2)',
                  borderRadius: 24,
                  border: '1px solid rgba(0, 113, 227, 0.15)',
                  boxShadow: '0 0 40px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.05)',
                  padding: '36px 32px 28px',
                }}>
                  <StaggerList>
                    <form onSubmit={onSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
                      <StaggerItem>
                        <div style={{ marginBottom: 16 }}>
                          <input
                            type="email" placeholder="Email" required autoComplete="email"
                            value={email} onChange={(e) => setEmail(e.target.value)}
                            style={{
                              width: '100%', height: 48,
                              background: 'rgba(255,255,255,0.05)',
                              border: '1px solid rgba(255,255,255,0.08)',
                              borderRadius: 12,
                              fontSize: 15, fontWeight: 400, color: '#F5F5F7',
                              outline: 'none', padding: '0 16px',
                              transition: 'border-color 200ms, box-shadow 200ms, background 200ms',
                            }}
                            onFocus={(e) => { e.currentTarget.style.borderColor = 'rgba(0,113,227,0.5)'; e.currentTarget.style.boxShadow = '0 0 12px rgba(0,113,227,0.15)'; e.currentTarget.style.background = 'rgba(255,255,255,0.08)'; }}
                            onBlur={(e) => { e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)'; e.currentTarget.style.boxShadow = 'none'; e.currentTarget.style.background = 'rgba(255,255,255,0.05)'; }}
                          />
                        </div>
                      </StaggerItem>

                      <StaggerItem>
                        <div style={{ marginBottom: 24 }}>
                          <input
                            type="password" placeholder="Password" required autoComplete="current-password"
                            value={password} onChange={(e) => setPassword(e.target.value)}
                            style={{
                              width: '100%', height: 48,
                              background: 'rgba(255,255,255,0.05)',
                              border: '1px solid rgba(255,255,255,0.08)',
                              borderRadius: 12,
                              fontSize: 15, fontWeight: 400, color: '#F5F5F7',
                              outline: 'none', padding: '0 16px',
                              transition: 'border-color 200ms, box-shadow 200ms, background 200ms',
                            }}
                            onFocus={(e) => { e.currentTarget.style.borderColor = 'rgba(0,113,227,0.5)'; e.currentTarget.style.boxShadow = '0 0 12px rgba(0,113,227,0.15)'; e.currentTarget.style.background = 'rgba(255,255,255,0.08)'; }}
                            onBlur={(e) => { e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)'; e.currentTarget.style.boxShadow = 'none'; e.currentTarget.style.background = 'rgba(255,255,255,0.05)'; }}
                          />
                        </div>
                      </StaggerItem>

                      <StaggerItem>
                        <motion.button
                          type="submit"
                          disabled={isLoading}
                          whileTap={{ scale: 0.97 }}
                          whileHover={{ scale: 1.01, boxShadow: '0 4px 20px rgba(0,113,227,0.4)' }}
                          transition={{ type: 'spring', stiffness: 400, damping: 25 }}
                          style={{
                            width: '100%', height: 48,
                            background: 'linear-gradient(135deg, #0071E3 0%, #2997FF 100%)',
                            color: '#FFFFFF', border: 'none', borderRadius: 12,
                            fontSize: 15, fontWeight: 600,
                            cursor: isLoading ? 'not-allowed' : 'pointer',
                            opacity: isLoading ? 0.5 : 1,
                            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                            boxShadow: '0 2px 12px rgba(0,113,227,0.3)',
                          }}
                        >
                          {isLoading ? (
                            <>
                              <motion.span
                                animate={{ rotate: 360 }}
                                transition={{ repeat: Infinity, duration: 0.8, ease: 'linear' }}
                                style={{ display: 'inline-block', width: 16, height: 16, border: '2px solid rgba(255,255,255,0.3)', borderTopColor: '#FFF', borderRadius: '50%' }}
                              />
                              Signing in...
                            </>
                          ) : 'Sign In'}
                        </motion.button>
                      </StaggerItem>
                    </form>

                    <StaggerItem>
                      <p style={{ textAlign: 'center', fontSize: 13, color: 'rgba(255,255,255,0.35)', marginTop: 18, fontFamily: '-apple-system, sans-serif' }}>
                        Don't have an account?{' '}
                        <Link to="/register" style={{ color: '#2997FF', textDecoration: 'none' }}>Sign up</Link>
                      </p>
                    </StaggerItem>
                  </StaggerList>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Login;
