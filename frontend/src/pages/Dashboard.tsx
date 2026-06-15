/* Dashboard — Flat Minimalism Apple Design Language
 * Zero box-shadows, extreme typography contrast, spring-only animations
 */

import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus, Trash2, Play, Clock, Settings, LayoutGrid, Puzzle,
  Globe, CalendarClock, Rocket, FileCode2, Key, ChevronRight, BookOpen,
  BarChart3, CheckCircle2, Zap, DollarSign, Loader2,
} from 'lucide-react';
import { motion } from 'framer-motion';
import { crewsApi } from '../api/crews';
import { executionsApi, type ExecutionStats } from '../api/executions';
import { demoApi } from '../api/demo';
import { getLLMKeys, getLLMBaseUrls } from '../lib/llmKeys';
import type { Crew } from '../types';
import { useAuthStore } from '../stores/authStore';
import { useIsMobile } from '../lib/responsive';
import { MobileMenu } from '../components/layout/MobileMenu';
import { formatDate, parseUTC } from '../lib/utils';
import { StaggerList } from '../components/motion/StaggerList';
import { staggerItem } from '../lib/motion-variants';
import { useThemeStore } from '../stores/themeStore';
import { TunnelTransition } from '../components/motion/TunnelTransition';
import { setLang, getLang, t } from '../lib/i18n';
import toast from 'react-hot-toast';

/* ========== Design Tokens ========== */
const BG = '#FBFBFD';
const CARD = '#FFFFFF';
const TEXT_PRIMARY = '#1D1D1F';
const TEXT_SECONDARY = '#6E6E73';
const TEXT_TERTIARY = '#86868B';
const TEXT_FAINT = '#A1A1AA';
const ACCENT = '#0071E3';
const BORDER_FAINT = '1px solid rgba(0,0,0,0.05)';
const HOVER_SHADOW = '0 20px 40px -10px rgba(0,0,0,0.06)';
const NAV_BG = 'rgba(255,255,255,0.80)';
const GLASS_BG = 'rgba(255,255,255,0.5)';
const GLASS_BLUR = 'blur(20px)';
const CARD_BLUR = 'blur(12px)';
const RADIUS_LG = '20px';
const RADIUS_FULL = '9999px';

/* ========== Nav links ========== */
const getNavLinks = () => [
  { label: t('common.nav_templates'),   path: '/templates',       icon: LayoutGrid },
  { label: t('common.nav_plugins'),     path: '/plugins',          icon: Puzzle },
  { label: t('common.nav_mcp_tools'),   path: '/mcp-marketplace',  icon: FileCode2 },
  { label: t('common.nav_knowledge'),   path: '/knowledge-bases',  icon: BookOpen },
  { label: t('common.nav_settings'),    path: '/settings',         icon: Key },
  { label: t('common.nav_webhooks'),    path: '/webhooks',         icon: Globe },
  { label: t('common.nav_schedules'),   path: '/schedules',        icon: CalendarClock },
  { label: t('common.nav_api_publish'), path: '/published',        icon: Rocket },
];

/* ========== Spring Physics ========== */
const SPRING = { type: 'spring' as const, stiffness: 300, damping: 25 };
const SPRING_TAP = { type: 'spring' as const, stiffness: 400, damping: 30 };

/* ========== Stat Card ========== */
const StatCard: React.FC<{
  icon: React.ReactNode;
  label: string;
  value: string | number;
  _color: string;
}> = ({ icon, label, value, _color: color }) => (
  <motion.div
    variants={staggerItem}
    whileHover={{ scale: 1.02, boxShadow: HOVER_SHADOW }}
    transition={SPRING}
    style={{
      background: GLASS_BG,
      backdropFilter: CARD_BLUR,
      WebkitBackdropFilter: CARD_BLUR,
      border: BORDER_FAINT,
      borderRadius: RADIUS_LG,
      padding: '20px',
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
      minWidth: 0,
    }}
  >
    <div style={{
      flexShrink: 0,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      width: 16, height: 16,
      color: '#D4D4D8',
    }}>
      {icon}
    </div>
    <div style={{ minWidth: 0 }}>
      <div style={{
        fontSize: '48px',
        fontWeight: 900,
        color: color || TEXT_PRIMARY,
        lineHeight: 1.1,
        letterSpacing: '-0.03em',
      }}>
        {value}
      </div>
      <div style={{
        fontSize: '12px',
        fontWeight: 400,
        color: TEXT_FAINT,
        marginTop: '2px',
      }}>
        {label}
      </div>
    </div>
  </motion.div>
);

/* ========== Quick Stats ========== */
const QuickStats: React.FC = () => {
  const { data: stats, isLoading } = useQuery<ExecutionStats>({
    queryKey: ['execution-stats'],
    queryFn: () => executionsApi.getStats(),
    staleTime: 30_000,
  });

  const skeletonStyle: React.CSSProperties = {
    background: GLASS_BG,
    backdropFilter: CARD_BLUR,
    WebkitBackdropFilter: CARD_BLUR,
    border: BORDER_FAINT,
    borderRadius: RADIUS_LG,
    padding: '20px',
    height: 88,
  };

  if (isLoading || !stats) {
    return (
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
        gap: '12px',
        marginBottom: '40px',
      }}>
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} style={skeletonStyle}>
            <div style={{ width: '40%', height: 20, background: '#E5E5EA', borderRadius: 6, marginBottom: 8 }} />
            <div style={{ width: '60%', height: 12, background: '#E5E5EA', borderRadius: 6 }} />
          </div>
        ))}
      </div>
    );
  }

  return (
    <StaggerList>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
        gap: '12px',
        marginBottom: '40px',
      }}>
        <StatCard
          icon={<BarChart3 style={{ width: 16, height: 16 }} />}
          label={t('dashboard.total_runs')}
          value={stats.total_executions}
          _color="#0071E3"
        />
        <StatCard
          icon={<CheckCircle2 style={{ width: 16, height: 16 }} />}
          label={t('dashboard.completed')}
          value={stats.completed_executions}
          _color="#34C759"
        />
        <StatCard
          icon={<Zap style={{ width: 16, height: 16 }} />}
          label={t('dashboard.success_rate')}
          value={`${Math.round(stats.success_rate)}%`}
          _color="#FF9500"
        />
        <StatCard
          icon={<DollarSign style={{ width: 16, height: 16 }} />}
          label={t('dashboard.total_tokens')}
          value={stats.total_tokens > 1000 ? `${(stats.total_tokens / 1000).toFixed(1)}k` : stats.total_tokens}
          _color="#AF52DE"
        />
      </div>
    </StaggerList>
  );
};

/* ========== Workflow Card ========== */
const WorkflowCard: React.FC<{
  crew: Crew;
  onDelete: (id: string, name: string, e: React.MouseEvent) => void;
}> = ({ crew, onDelete }) => {
  const navigate = useNavigate();
  const [running, setRunning] = useState(false);

  const handleRun = useCallback(async (e: React.MouseEvent) => {
    e.stopPropagation();
    setRunning(true);
    try {
      const { setTransitioning, enterCyberMode } = useThemeStore.getState();
      setTransitioning('to-cyber');

      const exec = await executionsApi.create({
        crew_id: crew.id,
        llm_api_keys: getLLMKeys(),
        llm_base_urls: getLLMBaseUrls(),
      });
      toast.success('Execution started');

      setTimeout(() => {
        enterCyberMode();
        navigate(`/execution/${exec.id}`);
      }, 3200);
    } catch (err: unknown) {
      useThemeStore.getState().exitCyberMode();
      const msg = err instanceof Error ? err.message : 'Start failed';
      toast.error(msg);
    } finally {
      setRunning(false);
    }
  }, [crew.id, navigate]);

  const handleEdit = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    navigate(`/crew/${crew.id}`);
  }, [crew.id, navigate]);

  const agentCount = crew.agents?.length ?? 0;
  const taskCount = crew.tasks?.length ?? 0;

  return (
    <motion.div
      variants={staggerItem}
      onClick={() => navigate(`/crew/${crew.id}`)}
      whileHover={{ scale: 1.02, boxShadow: HOVER_SHADOW }}
      transition={SPRING}
      style={{
        background: CARD,
        borderRadius: RADIUS_LG,
        border: BORDER_FAINT,
        padding: '24px',
        cursor: 'pointer',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Header row */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '12px' }}>
        <h3 style={{
          fontSize: '17px',
          fontWeight: 700,
          color: TEXT_PRIMARY,
          lineHeight: 1.35,
          flex: 1,
          margin: 0,
        }}>
          {crew.name}
        </h3>
        <span style={{
          fontSize: '11px',
          fontWeight: 500,
          color: ACCENT,
          background: 'rgba(0,113,227,0.06)',
          padding: '2px 8px',
          borderRadius: RADIUS_FULL,
          whiteSpace: 'nowrap',
        }}>
          {crew.process === 'sequential' ? 'Sequential' : crew.process === 'hierarchical' ? 'Hierarchical' : 'Parallel'}
        </span>
      </div>

      {/* Description */}
      <p style={{
        fontSize: '13px',
        fontWeight: 400,
        color: TEXT_SECONDARY,
        lineHeight: 1.47,
        margin: 0,
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        display: '-webkit-box',
        WebkitLineClamp: 2,
        WebkitBoxOrient: 'vertical',
      }}>
        {crew.description || 'No description'}
      </p>

      {/* Agent / Task meta */}
      <div style={{
        display: 'flex',
        gap: '16px',
        fontSize: '11px',
        color: TEXT_TERTIARY,
      }}>
        {agentCount > 0 && <span>{agentCount} agent{agentCount !== 1 ? 's' : ''}</span>}
        {taskCount > 0 && <span>{taskCount} task{taskCount !== 1 ? 's' : ''}</span>}
      </div>

      {/* Bottom: separator + actions */}
      <div style={{
        borderTop: '1px solid rgba(0,0,0,0.05)',
        paddingTop: '12px',
        marginTop: '4px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <span style={{
          fontSize: '11px',
          color: TEXT_TERTIARY,
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
        }}>
          <Clock style={{ width: 12, height: 12 }} />
          {formatDate(parseUTC(crew.created_at))}
        </span>
        <div style={{ display: 'flex', gap: '8px' }}>
          <motion.button
            onClick={handleRun}
            disabled={running}
            whileTap={{ scale: 0.97 }}
            transition={SPRING_TAP}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '6px 14px',
              height: 36,
              background: ACCENT,
              color: '#FFFFFF',
              border: 'none',
              borderRadius: RADIUS_FULL,
              fontSize: '15px',
              fontWeight: 500,
              cursor: running ? 'wait' : 'pointer',
              opacity: running ? 0.7 : 1,
            }}
          >
            {running
              ? <Loader2 style={{ width: 12, height: 12 }} className="animate-spin" />
              : <Play style={{ width: 12, height: 12 }} fill="currentColor" />}
            Run
          </motion.button>
          <motion.button
            onClick={handleEdit}
            whileTap={{ scale: 0.97 }}
            whileHover={{ background: 'rgba(0,0,0,0.04)' }}
            transition={SPRING_TAP}
            style={{
              display: 'flex',
              alignItems: 'center',
              padding: '6px',
              background: 'transparent',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              color: TEXT_TERTIARY,
            }}
            title={t('dashboard.edit_workflow')}
          >
            <Settings style={{ width: 14, height: 14 }} />
          </motion.button>
          <motion.button
            onClick={(e) => onDelete(crew.id, crew.name, e as unknown as React.MouseEvent)}
            whileTap={{ scale: 0.97 }}
            whileHover={{ background: 'rgba(0,0,0,0.04)' }}
            transition={SPRING_TAP}
            style={{
              display: 'flex',
              alignItems: 'center',
              padding: '6px',
              background: 'transparent',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              color: '#FF3B30',
            }}
            title={t('dashboard.delete_workflow')}
          >
            <Trash2 style={{ width: 14, height: 14 }} />
          </motion.button>
        </div>
      </div>
    </motion.div>
  );
};

/* ========== Nav Link ========== */
const NavLink: React.FC<{
  label: string;
  path: string;
  icon: React.ElementType;
}> = ({ label, path, icon: Icon }) => {
  const navigate = useNavigate();
  return (
    <motion.button
      onClick={() => navigate(path)}
      whileTap={{ scale: 0.97 }}
      whileHover={{ color: TEXT_PRIMARY }}
      transition={SPRING}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '4px',
        padding: '6px 10px',
        background: 'transparent',
        border: 'none',
        borderRadius: '6px',
        cursor: 'pointer',
        color: TEXT_SECONDARY,
        fontSize: '13px',
        fontWeight: 400,
        whiteSpace: 'nowrap',
      }}
    >
      <Icon style={{ width: 14, height: 14 }} />
      {label}
    </motion.button>
  );
};

/* ========== Flat Button ========== */
const FlatButton: React.FC<{
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'ghost';
  disabled?: boolean;
}> = ({ children, onClick, variant = 'primary', disabled }) => {
  const base: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    height: 36,
    padding: '0 18px',
    fontSize: '15px',
    fontWeight: 500,
    borderRadius: RADIUS_FULL,
    border: 'none',
    cursor: disabled ? 'not-allowed' : 'pointer',
    opacity: disabled ? 0.5 : 1,
    whiteSpace: 'nowrap',
  };
  const variants: Record<string, React.CSSProperties> = {
    primary: { background: ACCENT, color: '#FFFFFF' },
    secondary: { background: 'transparent', color: TEXT_PRIMARY, border: '1px solid rgba(0,0,0,0.1)' },
    ghost: { background: 'transparent', color: ACCENT },
  };
  return (
    <motion.button
      onClick={onClick}
      disabled={disabled}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.97 }}
      transition={SPRING_TAP}
      style={{ ...base, ...variants[variant] }}
    >
      {children}
    </motion.button>
  );
};

/* ========== Dashboard Main ========== */
const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const queryClient = useQueryClient();
  const isMobile = useIsMobile();

  // Language switcher
  const [lang, setLangState] = useState(getLang());
  const toggleLang = () => {
    const next = lang === 'zh' ? 'en' : 'zh';
    setLangState(next);
    setLang(next);
    window.location.reload();
  };

  const { data: crews, isLoading } = useQuery({
    queryKey: ['crews'],
    queryFn: () => crewsApi.list(),
  });

  const createMutation = useMutation({
    mutationFn: () => crewsApi.create({ name: 'New Workflow', description: '' }),
    onSuccess: (crew) => {
      queryClient.invalidateQueries({ queryKey: ['crews'] });
      navigate(`/crew/${crew.id}`);
    },
    onError: () => toast.error('Failed to create workflow'),
  });

  const deleteMutation = useMutation({
    mutationFn: (crewId: string) => crewsApi.delete(crewId),
    onMutate: async (crewId) => {
      await queryClient.cancelQueries({ queryKey: ['crews'] });
      const prev = queryClient.getQueryData<Crew[]>(['crews']);
      queryClient.setQueryData<Crew[]>(['crews'], (old) => (old || []).filter((c) => c.id !== crewId));
      return { prev };
    },
    onError: (_e, _id, ctx) => {
      if (ctx?.prev) queryClient.setQueryData(['crews'], ctx.prev);
      toast.error('Delete failed');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crews'] });
    },
  });

  const demoMutation = useMutation({
    mutationFn: () => demoApi.seedWorkflow(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crews'] });
      queryClient.invalidateQueries({ queryKey: ['execution-stats'] });
      toast.success('Demo workflow created');
    },
    onError: () => toast.error('Demo creation failed'),
  });

  const handleDelete = (crewId: string, crewName: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (window.confirm(`Delete "${crewName}"? This cannot be undone.`)) {
      deleteMutation.mutate(crewId);
    }
  };

  const handleLogout = () => { logout(); navigate('/login'); };

  const hasCrews = crews && crews.length > 0;

  return (
    <TunnelTransition>
    <div style={{ minHeight: '100vh', background: BG }}>
      {/* ===== Nav bar ===== */}
      <header style={{
        position: 'sticky',
        top: 0,
        zIndex: 50,
        background: NAV_BG,
        backdropFilter: GLASS_BLUR,
        WebkitBackdropFilter: GLASS_BLUR,
        borderBottom: BORDER_FAINT,
      }}>
        <div style={{
          maxWidth: 1200,
          margin: '0 auto',
          padding: '0 24px',
          height: 52,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '16px',
        }}>
          {/* Brand */}
          <span
            onClick={() => navigate('/')}
            style={{
              cursor: 'pointer',
              flexShrink: 0,
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <img
              src="/logo.png"
              alt="Fugue"
              style={{ height: '48px' }}
              onError={(e) => {
                // Fallback to text if image fails to load
                (e.target as HTMLImageElement).style.display = 'none';
                const fallback = (e.target as HTMLImageElement).nextElementSibling;
                if (fallback) (fallback as HTMLElement).style.display = 'inline';
              }}
            />
            <span style={{
              display: 'none',
              fontSize: '17px',
              fontWeight: 700,
              color: TEXT_PRIMARY,
              letterSpacing: '-0.02em',
            }}>
              Fugue
            </span>
          </span>

          {/* Center nav — mobile: hamburger drawer, desktop: inline links */}
          {isMobile ? (
            <div style={{ display: 'flex', alignItems: 'center', flex: 1, justifyContent: 'flex-end' }}>
              <MobileMenu onLogout={handleLogout} username={user?.username} />
            </div>
          ) : (
            <nav style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              overflow: 'hidden',
              flex: 1,
              justifyContent: 'center',
            }}>
              {getNavLinks().map((link) => (
                <NavLink key={link.path} {...link} />
              ))}
            </nav>
          )}

          {/* Right: user controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
            {/* Language switcher */}
            <motion.button
              onClick={toggleLang}
              whileTap={{ scale: 0.97 }}
              whileHover={{ color: TEXT_PRIMARY }}
              transition={SPRING}
              style={{
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                color: TEXT_SECONDARY,
                fontSize: '12px',
                fontWeight: 500,
                padding: '6px 8px',
                borderRadius: '6px',
              }}
              title={t('common.switch_language')}
            >
              {lang === 'zh' ? 'EN' : '中文'}
            </motion.button>
            <span style={{
              fontSize: '13px',
              color: TEXT_SECONDARY,
              maxWidth: 100,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}>
              {user?.username}
            </span>
            <motion.button
              onClick={() => navigate('/settings')}
              whileTap={{ scale: 0.97 }}
              whileHover={{ color: TEXT_PRIMARY }}
              transition={SPRING}
              style={{
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                color: TEXT_SECONDARY,
                padding: '6px',
                borderRadius: '6px',
                display: 'flex',
                alignItems: 'center',
              }}
              title={t('common.settings')}
            >
              <Settings style={{ width: 18, height: 18 }} />
            </motion.button>
            <motion.button
              onClick={handleLogout}
              whileTap={{ scale: 0.97 }}
              whileHover={{ color: TEXT_PRIMARY }}
              transition={SPRING}
              style={{
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                color: TEXT_SECONDARY,
                fontSize: '13px',
                padding: '6px 8px',
              }}
            >
              Sign Out
            </motion.button>
          </div>
        </div>
      </header>

      {/* ===== Main content ===== */}
      <main style={{
        maxWidth: 1200,
        margin: '0 auto',
        padding: '64px 24px 96px',
      }}>
        {/* Hero title — clip-path reveal */}
        <div style={{ marginBottom: '48px', overflow: 'hidden' }}>
          <motion.h1
            initial={{ clipPath: 'inset(100% 0 0 0)' }}
            animate={{ clipPath: 'inset(0 0 0 0)' }}
            transition={SPRING}
            style={{
              fontSize: 'clamp(32px, 5vw, 48px)',
              fontWeight: 900,
              lineHeight: 1.1,
              letterSpacing: '-0.03em',
              color: TEXT_PRIMARY,
              margin: 0,
            }}
          >
            Your Workflows.
          </motion.h1>
        </div>

        {/* QuickStats */}
        <QuickStats />

        {/* Action bar */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          marginBottom: '32px',
          flexWrap: 'wrap',
        }}>
          <FlatButton onClick={() => createMutation.mutate()}>
            <Plus style={{ width: 16, height: 16 }} />
            New Workflow
          </FlatButton>
          <FlatButton
            variant="secondary"
            onClick={() => demoMutation.mutate()}
            disabled={demoMutation.isPending}
          >
            {demoMutation.isPending
              ? <Loader2 style={{ width: 14, height: 14 }} className="animate-spin" />
              : <Play style={{ width: 14, height: 14 }} />}
            Try Demo
          </FlatButton>
        </div>

        {/* Loading skeletons */}
        {isLoading && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
            gap: '20px',
          }}>
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} style={{
                background: CARD,
                border: BORDER_FAINT,
                borderRadius: RADIUS_LG,
                padding: '24px',
                height: 180,
              }}>
                <div style={{ width: '60%', height: 16, background: '#E5E5EA', borderRadius: 8, marginBottom: 12 }} />
                <div style={{ width: '100%', height: 12, background: '#E5E5EA', borderRadius: 6, marginBottom: 8 }} />
                <div style={{ width: '40%', height: 12, background: '#E5E5EA', borderRadius: 6 }} />
              </div>
            ))}
          </div>
        )}

        {/* Empty state */}
        {!hasCrews && !isLoading && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={SPRING}
            style={{ textAlign: 'center', padding: '96px 0' }}
          >
            <h2 style={{
              fontSize: 'clamp(32px, 5vw, 48px)',
              fontWeight: 900,
              color: TEXT_PRIMARY,
              lineHeight: 1.1,
              letterSpacing: '-0.03em',
              marginBottom: '16px',
            }}>
              Create your first workflow.
            </h2>
            <p style={{
              fontSize: '17px',
              fontWeight: 400,
              color: TEXT_SECONDARY,
              lineHeight: 1.47,
              maxWidth: 480,
              margin: '0 auto 40px',
            }}>
              Connect AI Agents and Tasks to build powerful multi-agent workflows. Or try a demo to get started.
            </p>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
              <FlatButton onClick={() => createMutation.mutate()}>
                <Plus style={{ width: 18, height: 18 }} />
                New Workflow
              </FlatButton>
              <FlatButton variant="secondary" onClick={() => demoMutation.mutate()}>
                <Play style={{ width: 16, height: 16 }} />
                Try Demo
              </FlatButton>
              <FlatButton variant="secondary" onClick={() => navigate('/templates')}>
                <LayoutGrid style={{ width: 16, height: 16 }} />
                Browse Templates
              </FlatButton>
            </div>
          </motion.div>
        )}

        {/* Workflow card grid */}
        {hasCrews && (
          <StaggerList>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
              gap: '20px',
            }}>
              {/* New-card placeholder */}
              <motion.div
                variants={staggerItem}
                onClick={() => createMutation.mutate()}
                whileHover={{ scale: 1.02, boxShadow: HOVER_SHADOW }}
                transition={SPRING}
                style={{
                  background: GLASS_BG,
                  backdropFilter: CARD_BLUR,
                  WebkitBackdropFilter: CARD_BLUR,
                  border: '1px dashed rgba(0,0,0,0.12)',
                  borderRadius: RADIUS_LG,
                  padding: '24px',
                  cursor: 'pointer',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  minHeight: 160,
                  gap: '8px',
                }}
              >
                <Plus style={{ width: 24, height: 24, color: TEXT_SECONDARY }} />
                <span style={{
                  fontSize: '13px',
                  fontWeight: 400,
                  color: TEXT_SECONDARY,
                }}>
                  New Workflow
                </span>
              </motion.div>

              {/* Workflow cards */}
              {crews.map((crew) => (
                <WorkflowCard key={crew.id} crew={crew} onDelete={handleDelete} />
              ))}
            </div>
          </StaggerList>
        )}

        {/* Explore section */}
        {hasCrews && (
          <div style={{ marginTop: '64px' }}>
            <h2 style={{
              fontSize: '28px',
              fontWeight: 800,
              color: TEXT_PRIMARY,
              lineHeight: 1.1,
              letterSpacing: '-0.02em',
              marginBottom: '20px',
            }}>
              Explore
            </h2>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
              gap: '12px',
            }}>
              {getNavLinks().map((link) => (
                <motion.button
                  key={link.path}
                  onClick={() => navigate(link.path)}
                  whileHover={{ scale: 1.02, boxShadow: HOVER_SHADOW }}
                  whileTap={{ scale: 0.99 }}
                  transition={SPRING}
                  style={{
                    background: CARD,
                    borderRadius: RADIUS_LG,
                    border: BORDER_FAINT,
                    padding: '20px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    textAlign: 'left',
                  }}
                >
                  <div style={{
                    width: 36, height: 36,
                    borderRadius: '10px',
                    background: 'rgba(0,113,227,0.06)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    flexShrink: 0,
                  }}>
                    <link.icon style={{ width: 18, height: 18, color: ACCENT }} />
                  </div>
                  <span style={{
                    fontSize: '13px',
                    fontWeight: 600,
                    color: TEXT_PRIMARY,
                    flex: 1,
                  }}>
                    {link.label}
                  </span>
                  <ChevronRight style={{ width: 16, height: 16, color: TEXT_TERTIARY }} />
                </motion.button>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
    </TunnelTransition>
  );
};

export default Dashboard;
