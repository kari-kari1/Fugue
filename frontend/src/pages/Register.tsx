/* 注册页 — Apple Hero 即设计风格
 * 与 Login.tsx 保持一致的排版语言
 */

import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { toast } from 'react-hot-toast';
import { useAuthStore } from '../stores/authStore';
import { hasConfiguredKeys } from '../lib/llmKeys';
import { TextReveal } from '../components/motion/TextReveal';
import { StaggerList, StaggerItem } from '../components/motion/StaggerList';

const Register = () => {
  const navigate = useNavigate();
  const { register: registerUser, isLoading } = useAuthStore();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      toast.error('密码不一致');
      return;
    }
    try {
      const result = await registerUser({ username, email, password });
      toast.success('注册成功');
      if (result === 'need_login') {
        // 自动登录失败，跳转登录页并跳过视频动画
        navigate('/login', { state: { skipIntro: true } });
      } else {
        // 首次运行无 API Key 时跳转引导页
        navigate(hasConfiguredKeys() ? '/' : '/onboarding');
      }
    } catch (error: unknown) {
      const axiosError = error as { response?: { data?: { detail?: string | Array<{ msg?: string }> } } };
      const detail = axiosError.response?.data?.detail;
      let errorMessage = '注册失败';
      if (typeof detail === 'string') errorMessage = detail;
      else if (Array.isArray(detail)) errorMessage = detail.map((err) => err.msg || '验证错误').join('; ');
      toast.error(errorMessage);
    }
  };

  const inputStyle: React.CSSProperties = {
    width: '100%',
    height: '44px',
    background: 'transparent',
    border: 'none',
    borderBottom: '0.5px solid var(--separator)',
    fontSize: 'var(--text-body)',
    fontWeight: 'var(--fw-regular)',
    color: 'var(--text-primary)',
    outline: 'none',
    transition: 'border-color 200ms',
  };

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center"
      style={{ background: 'var(--bg-page)', padding: '0 var(--side-padding)' }}
    >
      {/* Hero 标题 */}
      <div className="w-full max-w-md text-center" style={{ marginBottom: 'var(--space-6)' }}>
        <TextReveal
          as="h1"
          style={{
            fontSize: 'clamp(48px, 7vw, 80px)',
            fontWeight: 'var(--fw-bold)',
            lineHeight: 'var(--lh-hero)',
            letterSpacing: 'var(--ls-hero)',
            color: 'var(--text-primary)',
            paddingTop: '16px',
            paddingBottom: '8px',
          }}
        >
          Join Fugue
        </TextReveal>

        <TextReveal
          as="p"
          delay={0.1}
          style={{
            marginTop: 'var(--space-3)',
            fontSize: 'var(--text-body)',
            fontWeight: 'var(--fw-regular)',
            lineHeight: 'var(--lh-body)',
            color: 'var(--text-secondary)',
          }}
        >
          Build workflows that think.
        </TextReveal>
      </div>

      {/* 表单 */}
      <StaggerList className="w-full max-w-md">
        <form onSubmit={onSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          <StaggerItem>
            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              style={inputStyle}
              onFocus={(e) => { e.currentTarget.style.borderBottomColor = 'var(--accent)'; }}
              onBlur={(e) => { e.currentTarget.style.borderBottomColor = 'var(--separator)'; }}
            />
          </StaggerItem>

          <StaggerItem>
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              style={inputStyle}
              onFocus={(e) => { e.currentTarget.style.borderBottomColor = 'var(--accent)'; }}
              onBlur={(e) => { e.currentTarget.style.borderBottomColor = 'var(--separator)'; }}
            />
          </StaggerItem>

          <StaggerItem>
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={inputStyle}
              onFocus={(e) => { e.currentTarget.style.borderBottomColor = 'var(--accent)'; }}
              onBlur={(e) => { e.currentTarget.style.borderBottomColor = 'var(--separator)'; }}
            />
          </StaggerItem>

          <StaggerItem>
            <input
              type="password"
              placeholder="Confirm Password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              style={inputStyle}
              onFocus={(e) => { e.currentTarget.style.borderBottomColor = 'var(--accent)'; }}
              onBlur={(e) => { e.currentTarget.style.borderBottomColor = 'var(--separator)'; }}
            />
          </StaggerItem>

          <StaggerItem>
            <motion.button
              type="submit"
              disabled={isLoading}
              whileTap={{ scale: 0.97 }}
              whileHover={{ scale: 1.02 }}
              transition={{ type: 'spring', stiffness: 400, damping: 25 }}
              style={{
                width: '100%',
                height: '44px',
                marginTop: 'var(--space-4)',
                background: 'var(--accent)',
                color: '#FFFFFF',
                border: 'none',
                borderRadius: 'var(--radius-pill)',
                fontSize: 'var(--text-footnote)',
                fontWeight: 'var(--fw-regular)',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                opacity: isLoading ? 0.4 : 1,
              }}
            >
              {isLoading ? 'Creating...' : 'Create Account'}
            </motion.button>
          </StaggerItem>
        </form>

        <StaggerItem>
          <p style={{
            textAlign: 'center',
            fontSize: 'var(--text-footnote)',
            color: 'var(--text-tertiary)',
            marginTop: 'var(--space-8)',
          }}>
            Already have an account?{' '}
            <Link to="/login" state={{ skipIntro: true }} style={{ color: 'var(--link)', textDecoration: 'none' }}>
              Sign in
            </Link>
          </p>
        </StaggerItem>
      </StaggerList>
    </div>
  );
};

export default Register;
