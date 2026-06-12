import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Menu, X, Home, LayoutTemplate, Settings, LogOut } from 'lucide-react';

interface MobileMenuProps {
  onLogout: () => void;
  username?: string;
}

export const MobileMenu: React.FC<MobileMenuProps> = ({ onLogout, username }) => {
  const [isOpen, setIsOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    setIsOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  const navItems = [
    { path: '/', label: '首页', icon: Home },
    { path: '/templates', label: '模板市场', icon: LayoutTemplate },
    { path: '/settings', label: '设置', icon: Settings },
  ];

  const handleNavigate = (path: string) => {
    navigate(path);
    setIsOpen(false);
  };

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="p-2 radius-md hover:bg-white/[0.06] transition-colors"
        aria-label="打开菜单"
      >
        <Menu className="h-6 w-6 text-primary" />
      </button>

      {isOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 transition-opacity"
          onClick={() => setIsOpen(false)}
          aria-hidden="true"
        />
      )}

      <div
        className={`fixed top-0 right-0 h-full w-72 bg-[var(--glass-bg)] backdrop-blur-xl border-l border-[var(--glass-border)] shadow-2xl z-50 transform transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="flex items-center justify-between p-4 border-b border-[var(--border-subtle)]">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-[var(--accent-steel)] flex items-center justify-center">
              <span className="text-[#060609] text-sm font-semibold">
                {username?.charAt(0)?.toUpperCase() || 'U'}
              </span>
            </div>
            <span className="text-sm font-medium text-primary truncate">
              {username || '用户'}
            </span>
          </div>
          <button
            onClick={() => setIsOpen(false)}
            className="p-2 radius-md hover:bg-white/[0.06] transition-colors"
            aria-label="关闭菜单"
          >
            <X className="h-5 w-5 text-tertiary" />
          </button>
        </div>

        <nav className="p-4 space-y-1">
          {navItems.map(({ path, label, icon: Icon }) => {
            const isActive = location.pathname === path;
            return (
              <button
                key={path}
                onClick={() => handleNavigate(path)}
                className={`w-full flex items-center gap-3 px-3 py-3 radius-lg text-left transition-colors ${
                  isActive
                    ? 'bg-accent-cyan-dim text-accent-cyan'
                    : 'text-primary hover:bg-white/[0.06]'
                }`}
              >
                <Icon className={`h-5 w-5 ${isActive ? 'text-accent-cyan' : 'text-tertiary'}`} />
                <span className="font-medium">{label}</span>
              </button>
            );
          })}
        </nav>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-[var(--border-subtle)]">
          <button
            onClick={() => {
              setIsOpen(false);
              onLogout();
            }}
            className="w-full flex items-center gap-3 px-3 py-3 radius-lg text-accent-red hover:bg-accent-red-dim transition-colors"
          >
            <LogOut className="h-5 w-5" />
            <span className="font-medium">退出登录</span>
          </button>
        </div>
      </div>
    </>
  );
};
