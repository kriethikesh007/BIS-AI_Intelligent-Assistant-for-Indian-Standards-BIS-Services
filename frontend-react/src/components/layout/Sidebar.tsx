import React, { useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Home,
  MessageSquare,
  Search,
  Award,
  Gem,
  FlaskConical,
  ShieldCheck,
  BarChart3,
  Settings,
  ChevronLeft,
  PanelLeftClose,
  PanelLeftOpen,
  Menu,
  X,
  Sun,
  Moon,
  Sparkles,
  Layers,
} from 'lucide-react';
import { useTheme } from '../../hooks/useTheme';

interface NavItem {
  path: string;
  label: string;
  icon: React.ReactNode;
  badge?: string;
  section: 'workspaces' | 'services' | 'system';
}

const navItems: NavItem[] = [
  { path: '/', label: 'Overview', icon: <Home size={15} strokeWidth={1.8} />, section: 'workspaces' },
  { path: '/assistant', label: 'AI Assistant', icon: <MessageSquare size={15} strokeWidth={1.8} />, section: 'workspaces' },
  { path: '/find-standard', label: 'Find Standard', icon: <Sparkles size={15} strokeWidth={1.8} />, section: 'workspaces' },
  { path: '/search', label: 'Standards Catalog', icon: <Search size={15} strokeWidth={1.8} />, section: 'services' },
  { path: '/certification', label: 'Certification Guide', icon: <Award size={15} strokeWidth={1.8} />, section: 'services' },
  { path: '/hallmarking', label: 'Gold & Hallmarking', icon: <Gem size={15} strokeWidth={1.8} />, section: 'services' },
  { path: '/laboratories', label: 'Testing Laboratories', icon: <FlaskConical size={15} strokeWidth={1.8} />, section: 'services' },
  { path: '/consumer', label: 'Consumer Rights & Help', icon: <ShieldCheck size={15} strokeWidth={1.8} />, section: 'services' },
  { path: '/analytics', label: 'ML Telemetry', icon: <BarChart3 size={15} strokeWidth={1.8} />, section: 'system' },
  { path: '/admin', label: 'Admin Console', icon: <Settings size={15} strokeWidth={1.8} />, section: 'system' },
];

const sectionTitles: Record<string, string> = {
  workspaces: 'Workspaces',
  services: 'Standards & Services',
  system: 'Intelligence & Admin',
};

/* ─── Institutional Logo Emblem ─── */
function BrandEmblem({ size = 26 }: { size?: number }) {
  return (
    <div
      className="relative flex items-center justify-center rounded-lg shadow-xs overflow-hidden shrink-0 select-none bg-brand-500"
      style={{
        width: size,
        height: size,
      }}
    >
      <svg
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-4 h-4 text-white"
        stroke="currentColor"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2" />
        <circle cx="12" cy="12" r="3" fill="currentColor" />
      </svg>
    </div>
  );
}

export function Sidebar({ collapsed, onToggle }: { collapsed: boolean; onToggle: () => void }) {
  const { theme, toggleTheme } = useTheme();

  const renderNavGroup = (section: 'workspaces' | 'services' | 'system') => {
    const items = navItems.filter(i => i.section === section);
    return (
      <div key={section} className="mb-4">
        {!collapsed && (
          <div
            className="px-2.5 mb-1.5 text-[10px] font-semibold uppercase tracking-wider select-none text-text-tertiary"
          >
            {sectionTitles[section]}
          </div>
        )}
        <div className="flex flex-col gap-0.5">
          {items.map(item => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `group relative flex items-center gap-2.5 px-2.5 h-8 rounded-md text-xs font-medium transition-all duration-120 select-none ${
                  collapsed ? 'justify-center' : ''
                } ${
                  isActive
                    ? 'bg-brand-500/10 text-brand-600 dark:text-brand-400'
                    : 'text-text-secondary hover:text-text-primary hover:bg-bg-tertiary/50'
                }`
              }
              title={collapsed ? item.label : undefined}
            >
              {({ isActive }) => (
                <>
                  {isActive && !collapsed && (
                    <motion.span
                      layoutId="sidebarActivePill"
                      className="absolute left-0 top-1.5 bottom-1.5 w-0.5 rounded-full bg-brand-500"
                      transition={{ type: 'spring', stiffness: 350, damping: 30 }}
                    />
                  )}
                  <span className={`shrink-0 transition-transform duration-100 ${isActive ? 'scale-105' : 'group-hover:scale-105'}`}>
                    {item.icon}
                  </span>
                  {!collapsed && (
                    <span className="truncate flex-1 tracking-tight">{item.label}</span>
                  )}
                  {!collapsed && item.badge && (
                    <span
                      className={`text-[9px] font-semibold px-1.5 py-0.2 rounded uppercase tracking-wider ${
                        isActive ? 'bg-brand-500 text-white' : 'bg-bg-tertiary text-text-tertiary'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </>
              )}
            </NavLink>
          ))}
        </div>
      </div>
    );
  };

  return (
    <aside
      className="h-full flex flex-col border-r border-border-default bg-bg-secondary transition-all duration-150 select-none"
      style={{
        width: collapsed ? 'var(--sidebar-collapsed-width)' : 'var(--sidebar-width)',
      }}
    >
      {/* ─── Header: Brand Mark & Collapse Toggle ─── */}
      <div
        className="flex items-center justify-between px-3 h-13 border-b border-border-subtle shrink-0"
      >
        <div className="flex items-center gap-2.5 min-w-0">
          <BrandEmblem size={26} />
          {!collapsed && (
            <div className="min-w-0 flex flex-col">
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-bold tracking-tight text-text-primary">
                  BIS-AI
                </span>
                <span
                  className="text-[9px] px-1 py-0.2 rounded font-semibold border border-border-default bg-bg-primary text-text-secondary"
                >
                  2026
                </span>
              </div>
              <span className="text-[10px] truncate text-text-tertiary">
                Indian Standards Engine
              </span>
            </div>
          )}
        </div>
        <button
          onClick={onToggle}
          className="p-1.5 rounded-md border border-border-default bg-bg-primary text-text-tertiary hover:text-text-primary hover:border-border-strong transition-all cursor-pointer shadow-xs"
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <PanelLeftOpen size={14} /> : <PanelLeftClose size={14} />}
        </button>
      </div>

      {/* ─── Navigation ─── */}
      <nav className="flex-1 overflow-y-auto py-3 px-2">
        {(['workspaces', 'services', 'system'] as const).map(renderNavGroup)}
      </nav>

      {/* ─── Footer: Status & Theme Toggle ─── */}
      <div
        className="p-2 border-t border-border-subtle shrink-0 flex flex-col gap-1.5"
      >
        {!collapsed && (
          <div
            className="flex items-center justify-between px-2 py-1.5 rounded-md text-[11px] border border-border-subtle bg-bg-primary"
          >
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="font-medium text-text-secondary">
                Standards Online
              </span>
            </div>
            <span className="font-mono text-[10px] text-text-tertiary">
              IS v1.4
            </span>
          </div>
        )}

        <button
          onClick={toggleTheme}
          className={`flex items-center gap-2 px-2 h-7 rounded-md text-xs transition-colors hover:bg-bg-tertiary text-text-secondary hover:text-text-primary w-full cursor-pointer ${
            collapsed ? 'justify-center' : ''
          }`}
          aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
        >
          {theme === 'light' ? <Moon size={14} /> : <Sun size={14} />}
          {!collapsed && (
            <span className="text-[11px] font-medium flex-1 text-left">
              {theme === 'light' ? 'Dark theme' : 'Light theme'}
            </span>
          )}
        </button>
      </div>
    </aside>
  );
}

/* ─── Mobile Drawer ─── */
export function MobileDrawer({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { theme, toggleTheme } = useTheme();

  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [open]);

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-xs"
            style={{ zIndex: 'var(--z-overlay)' as unknown as number }}
            onClick={onClose}
          />
          <motion.div
            initial={{ x: -280 }}
            animate={{ x: 0 }}
            exit={{ x: -280 }}
            transition={{ type: 'spring', damping: 28, stiffness: 320 }}
            className="fixed left-0 top-0 bottom-0 w-[270px] flex flex-col border-r border-border-default bg-bg-secondary shadow-2xl"
            style={{
              zIndex: 'var(--z-modal)' as unknown as number,
            }}
          >
            <div
              className="flex items-center justify-between px-4 h-13 border-b border-border-subtle shrink-0"
            >
              <div className="flex items-center gap-2.5">
                <BrandEmblem size={24} />
                <span className="text-xs font-bold text-text-primary">
                  BIS-AI Engine
                </span>
              </div>
              <button
                onClick={onClose}
                className="p-1 rounded-md cursor-pointer text-text-tertiary hover:text-text-primary"
                aria-label="Close menu"
              >
                <X size={16} />
              </button>
            </div>

            <nav className="flex-1 overflow-y-auto py-3 px-2">
              {(['workspaces', 'services', 'system'] as const).map(section => {
                const items = navItems.filter(i => i.section === section);
                return (
                  <div key={section} className="mb-4">
                    <div
                      className="px-2.5 mb-1.5 text-[10px] font-semibold uppercase tracking-wider text-text-tertiary"
                    >
                      {sectionTitles[section]}
                    </div>
                    {items.map(item => (
                      <NavLink
                        key={item.path}
                        to={item.path}
                        onClick={onClose}
                        className={({ isActive }) =>
                          `flex items-center gap-2.5 px-2.5 h-8.5 rounded-md text-xs font-medium transition-colors ${
                            isActive
                              ? 'bg-brand-500/10 text-brand-600 dark:text-brand-400'
                              : 'text-text-secondary hover:text-text-primary hover:bg-bg-tertiary/50'
                          }`
                        }
                      >
                        {item.icon}
                        <span className="flex-1 truncate">{item.label}</span>
                        {item.badge && (
                          <span
                            className="text-[9px] px-1.5 py-0.2 rounded font-semibold bg-brand-500 text-white"
                          >
                            {item.badge}
                          </span>
                        )}
                      </NavLink>
                    ))}
                  </div>
                );
              })}
            </nav>

            <div
              className="p-3 border-t border-border-subtle flex items-center justify-between"
            >
              <button
                onClick={toggleTheme}
                className="flex items-center gap-2 px-2 py-1.5 rounded-md text-xs cursor-pointer text-text-secondary hover:text-text-primary hover:bg-bg-tertiary"
              >
                {theme === 'light' ? <Moon size={14} /> : <Sun size={14} />}
                <span className="text-[11px] font-medium">{theme === 'light' ? 'Dark theme' : 'Light theme'}</span>
              </button>
              <span className="text-[10px] font-mono text-text-tertiary">
                Online
              </span>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
