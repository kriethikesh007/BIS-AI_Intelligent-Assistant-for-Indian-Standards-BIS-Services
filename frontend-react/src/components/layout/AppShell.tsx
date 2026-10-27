import React, { useState, useCallback, useEffect } from 'react';
import { Outlet, useLocation, useNavigate, Link } from 'react-router-dom';
import { Menu, Search, Moon, Sun, ChevronRight, Sparkles } from 'lucide-react';
import { Sidebar, MobileDrawer } from './Sidebar';
import { useMediaQuery, useLocalStorage } from '../../hooks/useUtils';
import { useTheme } from '../../hooks/useTheme';

const pageMetadata: Record<string, { title: string; section: string }> = {
  '/': { title: 'Overview', section: 'Workspace' },
  '/assistant': { title: 'AI Assistant', section: 'Workspace' },
  '/find-standard': { title: 'Product Recommender', section: 'Workspace' },
  '/search': { title: 'Standards Catalog', section: 'Standards & Services' },
  '/certification': { title: 'Certification Guide', section: 'Standards & Services' },
  '/hallmarking': { title: 'Gold Hallmarking & HUID', section: 'Standards & Services' },
  '/laboratories': { title: 'Laboratory Directory', section: 'Standards & Services' },
  '/consumer': { title: 'Consumer Protection & Help', section: 'Standards & Services' },
  '/analytics': { title: 'ML Performance & Telemetry', section: 'Intelligence & Admin' },
  '/admin': { title: 'Admin Console', section: 'Intelligence & Admin' },
};

export function AppShell() {
  const isMobile = useMediaQuery('(max-width: 768px)');
  const [collapsed, setCollapsed] = useLocalStorage('bis-sidebar-collapsed', false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();

  const toggleSidebar = useCallback(() => setCollapsed(prev => !prev), [setCollapsed]);
  const currentMeta = pageMetadata[location.pathname] || { title: 'Indian Standards', section: 'BIS-AI' };

  // Keyboard shortcut '/' to quickly jump to search
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === '/' && !['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement)?.tagName)) {
        e.preventDefault();
        navigate('/search');
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [navigate]);

  return (
    <div className="flex h-screen overflow-hidden bg-bg-primary text-text-primary">
      {/* Desktop Sidebar */}
      {!isMobile && (
        <Sidebar collapsed={collapsed} onToggle={toggleSidebar} />
      )}

      {/* Mobile Drawer */}
      {isMobile && (
        <MobileDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} />
      )}

      {/* Main Content Viewport */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden bg-bg-primary">
        {/* Top Header Bar */}
        <header
          className="flex items-center justify-between h-[52px] px-3 sm:px-6 border-b border-border-default bg-bg-primary shrink-0 select-none z-10"
        >
          {/* Left: Mobile Toggle & Breadcrumbs */}
          <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1 mr-2">
            {isMobile && (
              <button
                onClick={() => setDrawerOpen(true)}
                className="p-1.5 rounded-md -ml-1 text-text-secondary hover:text-text-primary cursor-pointer shrink-0"
                aria-label="Open navigation menu"
              >
                <Menu size={18} />
              </button>
            )}

            <nav aria-label="Breadcrumbs" className="flex items-center gap-1.5 text-xs min-w-0 overflow-hidden">
              <Link
                to="/"
                className="font-medium text-text-tertiary hover:text-text-primary transition-colors shrink-0"
              >
                BIS-AI
              </Link>
              <span className="text-text-tertiary shrink-0">/</span>
              <span className="font-semibold text-text-primary truncate">
                {currentMeta.title}
              </span>
            </nav>
          </div>

          {/* Right: Quick Search Button, Status Pill, Theme Toggle */}
          <div className="flex items-center gap-2 sm:gap-2.5 shrink-0">
            {/* Quick Search Shortcut */}
            <button
              onClick={() => navigate('/search')}
              className="hidden sm:inline-flex items-center gap-2 px-2.5 h-7 rounded-md border border-border-default bg-bg-secondary text-[11px] text-text-tertiary hover:text-text-primary hover:border-border-strong transition-all cursor-pointer"
              title="Search standards catalog (shortcut: /)"
            >
              <Search size={12} />
              <span>Search standards...</span>
              <kbd
                className="px-1 py-0.2 rounded text-[10px] font-mono border border-border-subtle bg-bg-primary"
              >
                /
              </kbd>
            </button>

            {/* Live Engine Status Pill */}
            <div
              className="hidden md:inline-flex items-center gap-1.5 px-2.5 h-6 rounded-full border border-border-subtle bg-bg-secondary text-[10px] font-medium text-text-secondary"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span>Online</span>
            </div>

            {/* Quick Theme Toggle in Top Bar for immediate access */}
            <button
              onClick={toggleTheme}
              className="p-1.5 rounded-md text-text-secondary hover:text-text-primary hover:bg-bg-secondary transition-colors cursor-pointer border border-transparent hover:border-border-subtle"
              aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`}
              title="Toggle theme"
            >
              {theme === 'light' ? <Moon size={15} /> : <Sun size={15} />}
            </button>
          </div>
        </header>

        {/* Scrollable Page Content */}
        <main className="flex-1 overflow-y-auto bg-bg-primary">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
