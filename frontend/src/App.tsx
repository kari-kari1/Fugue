/* Fugue主应用 */

import React, { useEffect, useState, useCallback, useRef, Suspense } from 'react';
import { HashRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { useAuthStore } from './stores/authStore';

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
import { ElicitationListener } from './components/mcp/ElicitationDialog';
const KnowledgeBases = React.lazy(() => import('./pages/KnowledgeBases'));
const PublishedPage = React.lazy(() => import('./pages/PublishedPage'));
const Login = React.lazy(() => import('./pages/Login'));
const Register = React.lazy(() => import('./pages/Register'));
const Onboarding = React.lazy(() => import('./pages/Onboarding'));
import { ErrorBoundary } from './components/ErrorBoundary';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

const DISMISS_DURATION_MS = 5 * 60 * 1000;

const TokenRefreshModal: React.FC<{
  remainingSeconds: number;
  onRefresh: () => void;
  onDismiss: () => void;
  refreshing: boolean;
}> = ({ remainingSeconds, onRefresh, onDismiss, refreshing }) => {
  const minutes = Math.floor(remainingSeconds / 60);
  const seconds = remainingSeconds % 60;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm">
      <div className="bg-white border border-divider radius-xl shadow-xl-var p-6 w-full max-w-sm mx-4 animate-scale-in">
        <div className="flex justify-center mb-4">
          <div className="w-12 h-12 rounded-full bg-accent-amber-dim flex items-center justify-center">
            <svg className="w-6 h-6 text-accent-amber" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
            </svg>
          </div>
        </div>

        <h3 className="text-17 font-semibold text-primary text-center mb-2">
          会话即将过期
        </h3>

        <p className="text-13 text-secondary text-center mb-6">
          您的会话将在{' '}
          <span className="font-mono font-medium text-accent-amber">
            {minutes}:{seconds.toString().padStart(2, '0')}
          </span>{' '}
          后过期，请及时续期以避免数据丢失。
        </p>

        <div className="flex gap-3">
          <button onClick={onDismiss} disabled={refreshing}
            className="flex-1 px-4 py-2.5 text-13 font-medium text-primary bg-secondary radius-lg hover:bg-tertiary border border-divider transition-colors disabled:opacity-50">
            稍后提醒
          </button>
          <button onClick={onRefresh} disabled={refreshing}
            className="flex-1 px-4 py-2.5 text-13 font-medium text-white bg-[var(--accent-primary)] radius-lg hover:bg-[var(--accent-primary-hover)] transition-colors shadow-sm-var disabled:opacity-50 flex items-center justify-center gap-2">
            {refreshing && (
              <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            )}
            {refreshing ? '续期中...' : '立即续期'}
          </button>
        </div>
      </div>
    </div>
  );
};

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading, checkTokenExpiry, refreshToken, logout } = useAuthStore();
  const [showModal, setShowModal] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const dismissedUntilRef = useRef<number>(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  useEffect(() => {
    if (!isAuthenticated) return;

    const check = () => {
      const { isExpired, isExpiringSoon, remainingSeconds } = checkTokenExpiry();

      if (isExpired) {
        setShowModal(false);
        logout();
        return;
      }

      if (isExpiringSoon && Date.now() > dismissedUntilRef.current) {
        setCountdown(remainingSeconds);
        setShowModal(true);
      } else if (!isExpiringSoon) {
        setShowModal(false);
      }
    };

    check();

    const checkInterval = setInterval(check, 30_000);

    const countdownInterval = setInterval(() => {
      if (showModal) {
        const { isExpired, remainingSeconds } = checkTokenExpiry();
        if (isExpired) {
          setShowModal(false);
          logout();
        } else {
          setCountdown(remainingSeconds);
        }
      }
    }, 1_000);

    return () => {
      clearInterval(checkInterval);
      clearInterval(countdownInterval);
    };
  }, [isAuthenticated, showModal, checkTokenExpiry, logout]);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await refreshToken();
      setShowModal(false);
    } finally {
      setRefreshing(false);
    }
  }, [refreshToken]);

  const handleDismiss = useCallback(() => {
    dismissedUntilRef.current = Date.now() + DISMISS_DURATION_MS;
    setShowModal(false);
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-white">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent-primary" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <>
      {children}
      {showModal && (
        <TokenRefreshModal
          remainingSeconds={countdown}
          onRefresh={handleRefresh}
          onDismiss={handleDismiss}
          refreshing={refreshing}
        />
      )}
    </>
  );
};

function App() {
  const { loadUser, token } = useAuthStore();

  useEffect(() => {
    if (token) {
      loadUser();
    }
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

      <Toaster
        position="top-right"
        toastOptions={{
          duration: 3000,
          style: {
            background: 'white',
            color: 'var(--text-primary)',
            border: '1px solid var(--border-divider)',
            borderRadius: 'var(--radius-lg)',
            boxShadow: 'var(--shadow-lg)',
            fontSize: '13px',
          },
          success: {
            duration: 2000,
            iconTheme: {
              primary: '#34C759',
              secondary: 'white',
            },
          },
          error: {
            duration: 4000,
            iconTheme: {
              primary: '#FF3B30',
              secondary: 'white',
            },
          },
        }}
      />
    </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
