/* Fugue主应用 */

import React, { useEffect, useState, useCallback, useRef, Suspense } from 'react';
import { HashRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { useAuthStore } from './stores/authStore';
import { useTutorialStore } from './stores/tutorialStore';

// F4: React.lazy 代码分割 — 每个页面独立 chunk
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const Editor = React.lazy(() => import('./pages/Editor'));
const ExecutionView = React.lazy(() => import('./pages/ExecutionView'));
const Settings = React.lazy(() => import('./pages/Settings'));
const Templates = React.lazy(() => import('./pages/Templates'));
const Plugins = React.lazy(() => import('./pages/Plugins'));
const MCPMarketplace = React.lazy(() => import('./pages/MCPMarketplace'));
const WebhooksPage = React.lazy(() => import('./pages/WebhooksPage'));
const SchedulesPage = React.lazy(() => import('./pages/SchedulesPage'));
const PublishedPage = React.lazy(() => import('./pages/PublishedPage'));
const KnowledgeBases = React.lazy(() => import('./pages/KnowledgeBases'));
const SkillsMarketplace = React.lazy(() => import('./pages/SkillsMarketplace'));
const Login = React.lazy(() => import('./pages/Login'));
const Register = React.lazy(() => import('./pages/Register'));
const Onboarding = React.lazy(() => import('./pages/Onboarding'));
import { ElicitationListener } from './components/mcp/ElicitationDialog';
import { ErrorBoundary } from './components/ErrorBoundary';
import TutorialOverlay from './components/TutorialOverlay';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { refetchOnWindowFocus: false, retry: 1, staleTime: 30000 },
  },
});

// ─── Token Refresh Modal ────────────────────────────────────────────────────

const DISMISS_DURATION_MS = 10 * 60 * 1000;

const TokenRefreshModal: React.FC<{
  remainingSeconds: number; onRefresh: () => void; onDismiss: () => void; refreshing: boolean;
}> = ({ remainingSeconds, onRefresh, onDismiss, refreshing }) => {
  const minutes = Math.floor(remainingSeconds / 60);
  const seconds = remainingSeconds % 60;
  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999 }}>
      <div style={{ background: 'white', borderRadius: 16, padding: 32, maxWidth: 400, width: '90%', textAlign: 'center', boxShadow: '0 20px 60px rgba(0,0,0,0.15)' }}>
        <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>登录即将过期</h2>
        <p style={{ fontSize: 14, color: '#86868B', marginBottom: 24 }}>
          您的会话将在 {minutes} 分 {seconds} 秒后过期，是否立即续期？
        </p>
        <div style={{ display: 'flex', gap: 8, justifyContent: 'center' }}>
          <button onClick={onDismiss} style={{ padding: '10px 24px', borderRadius: 8, border: '1px solid #E5E5EA', background: 'white', fontSize: 14, cursor: 'pointer' }}>稍后再说</button>
          <button onClick={onRefresh} disabled={refreshing} style={{ padding: '10px 24px', borderRadius: 8, border: 'none', background: '#0071E3', color: 'white', fontSize: 14, cursor: 'pointer', opacity: refreshing ? 0.6 : 1 }}>
            {refreshing ? '续期中...' : '立即续期'}
          </button>
        </div>
      </div>
    </div>
  );
};

// ─── ProtectedRoute ─────────────────────────────────────────────────────────

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading, checkTokenExpiry, refreshToken, logout } = useAuthStore();
  const onboardingCompleted = useTutorialStore((s) => s.onboardingCompleted);
  const [showModal, setShowModal] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const dismissedUntilRef = useRef<number>(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, []);

  useEffect(() => {
    if (!isAuthenticated) return;
    const check = () => {
      const { isExpired, isExpiringSoon, remainingSeconds } = checkTokenExpiry();
      if (isExpired) { setShowModal(false); logout(); return; }
      if (isExpiringSoon && Date.now() > dismissedUntilRef.current) { setCountdown(remainingSeconds); setShowModal(true); }
      else if (!isExpiringSoon) { setShowModal(false); }
    };
    check();
    intervalRef.current = setInterval(check, 30_000);
    const countdownInterval = setInterval(() => {
      if (showModal) {
        const { isExpired, remainingSeconds } = checkTokenExpiry();
        if (isExpired) { setShowModal(false); logout(); } else { setCountdown(remainingSeconds); }
      }
    }, 1_000);
    return () => { clearInterval(countdownInterval); };
  }, [isAuthenticated]);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    try { await refreshToken(); setShowModal(false); } finally { setRefreshing(false); }
  }, [refreshToken]);

  const handleDismiss = useCallback(() => {
    dismissedUntilRef.current = Date.now() + DISMISS_DURATION_MS;
    setShowModal(false);
  }, []);

  if (isLoading) {
    return <div className="flex items-center justify-center min-h-screen bg-white"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent-primary" /></div>;
  }
  if (!isAuthenticated) return <Navigate to="/login" replace />;

  return (
    <>
      {!onboardingCompleted && window.location.hash !== '#/onboarding'
        ? <Navigate to="/onboarding" replace />
        : children}
      {showModal && <TokenRefreshModal remainingSeconds={countdown} onRefresh={handleRefresh} onDismiss={handleDismiss} refreshing={refreshing} />}
    </>
  );
};

// ─── App ────────────────────────────────────────────────────────────────────

function App() {
  const { loadUser, token } = useAuthStore();

  useEffect(() => {
    if (token) loadUser();
  }, [token, loadUser]);

  return (
    <ErrorBoundary>
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="min-h-screen bg-primary">
          <Suspense fallback={<div className="flex items-center justify-center h-screen"><div className="animate-spin w-8 h-8 border-2 border-gray-300 border-t-blue-500 rounded-full" /></div>}>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/onboarding" element={<ProtectedRoute><Onboarding /></ProtectedRoute>} />
            <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/crew/:crewId" element={<ProtectedRoute><Editor /></ProtectedRoute>} />
            <Route path="/execution/:executionId" element={<ProtectedRoute><ExecutionView /></ProtectedRoute>} />
            <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
            <Route path="/templates" element={<ProtectedRoute><Templates /></ProtectedRoute>} />
            <Route path="/plugins" element={<ProtectedRoute><Plugins /></ProtectedRoute>} />
            <Route path="/mcp-marketplace" element={<ProtectedRoute><MCPMarketplace /></ProtectedRoute>} />
            <Route path="/skills" element={<ProtectedRoute><SkillsMarketplace /></ProtectedRoute>} />
            <Route path="/webhooks" element={<ProtectedRoute><WebhooksPage /></ProtectedRoute>} />
            <Route path="/schedules" element={<ProtectedRoute><SchedulesPage /></ProtectedRoute>} />
            <Route path="/knowledge-bases" element={<ProtectedRoute><KnowledgeBases /></ProtectedRoute>} />
            <Route path="/published" element={<ProtectedRoute><PublishedPage /></ProtectedRoute>} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          </Suspense>
          <ElicitationListener />
        </div>
      </Router>
      <TutorialOverlay />
      <Toaster position="top-right" toastOptions={{ duration: 3000, style: { background: 'white', color: 'var(--text-primary)', border: '1px solid var(--border-divider)', borderRadius: 'var(--radius-lg)', boxShadow: 'var(--shadow-lg)', fontSize: '13px' } }} />
    </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
