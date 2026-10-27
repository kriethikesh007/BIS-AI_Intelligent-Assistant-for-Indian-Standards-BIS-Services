import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  MessageSquare,
  Search,
  Award,
  Gem,
  FlaskConical,
  ArrowRight,
  Zap,
  Sparkles,
  Database,
  ShieldCheck,
  CheckCircle2,
} from 'lucide-react';
import { Button, Card, Badge } from '../components/ui';
import { getDiagnostics } from '../services/api/endpoints';
import type { DiagnosticsData } from '../types/api';

interface ServiceItem {
  id: string;
  title: string;
  description: string;
  path: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  tag: string;
}

const services: ServiceItem[] = [
  {
    id: 'assistant',
    title: 'AI Compliance Assistant',
    description: 'Conversational compliance intelligence providing source-grounded answers citing exact IS clauses and gazette notifications.',
    path: '/assistant',
    icon: MessageSquare,
    tag: 'Core Workspace',
  },
  {
    id: 'find-standard',
    title: 'Product-to-Standard Recommender',
    description: 'Match product specifications and materials against Indian Standards using our 4-signal hybrid relevance scoring engine.',
    path: '/find-standard',
    icon: Zap,
    tag: 'AI Recommendation',
  },
  {
    id: 'search',
    title: 'Standards Catalog Browser',
    description: 'Search across indexed Indian Standards, technical parameters, and mandatory Quality Control Orders (QCOs).',
    path: '/search',
    icon: Search,
    tag: 'Catalog Index',
  },
  {
    id: 'certification',
    title: 'Certification & MSME Guide',
    description: 'Conformity assessment schemes: ISI Mark (Scheme I), CRS (Scheme II), FMCS, and up to 50% MSME fee concessions.',
    path: '/certification',
    icon: Award,
    tag: 'Certification',
  },
  {
    id: 'hallmarking',
    title: 'Gold Hallmarking & HUID',
    description: 'Mandatory purity fineness (24K to 14K), 6-digit laser HUID origin tracking, and certified fire assay protocols (IS 1418).',
    path: '/hallmarking',
    icon: Gem,
    tag: 'Hallmarking',
  },
  {
    id: 'laboratories',
    title: 'Laboratory Testing Network',
    description: 'Directory of BIS Central, Regional, Branch, and NABL-accredited test facilities across all Indian states.',
    path: '/laboratories',
    icon: FlaskConical,
    tag: 'Laboratory Network',
  },
];

const sampleQueries = [
  'Motorcycle helmets IS 4151',
  'Packaged drinking water IS 14543',
  '22K Gold 916 HUID rules',
  'MSME fee concessions ISI mark',
  'Lithium batteries IS 16046',
];

export function HomePage() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [diagnostics, setDiagnostics] = useState<DiagnosticsData | null>(null);

  useEffect(() => {
    let isMounted = true;
    getDiagnostics()
      .then((data) => {
        if (isMounted) setDiagnostics(data);
      })
      .catch(() => {});
    return () => {
      isMounted = false;
    };
  }, []);

  const handleSearchSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      const trimmed = searchQuery.trim();
      if (!trimmed) return;
      navigate(`/assistant?q=${encodeURIComponent(trimmed)}`);
    },
    [searchQuery, navigate]
  );

  return (
    <div className="w-full min-h-full py-10 sm:py-14 lg:py-16">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        {/* ─── Hero Section ─── */}
        <section className="space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium border border-border-default bg-bg-secondary text-text-secondary">
            <span className="w-2 h-2 rounded-full bg-brand-500 shrink-0" />
            <span>Bureau of Indian Standards · Compliance Intelligence</span>
          </div>

          <div className="space-y-4 max-w-3xl">
            <h1 className="text-2xl sm:text-4xl lg:text-[42px] font-bold tracking-tight text-text-primary leading-[1.2] sm:leading-[1.15]">
              Intelligent Assistant for Indian Standards & BIS Services
            </h1>
            <p className="text-sm sm:text-lg text-text-secondary leading-relaxed max-w-2xl">
              Source-backed intelligence for standard discovery, product certification workflows, gold
              hallmarking, and laboratory testing — grounded in official BIS gazettes.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 pt-1">
            <Button
              size="md"
              variant="primary"
              onClick={() => navigate('/assistant')}
              icon={<MessageSquare size={15} />}
              className="px-5 py-2.5 font-medium shadow-sm w-full sm:w-auto"
            >
              Open AI Assistant
              <ArrowRight size={14} className="ml-1.5" />
            </Button>
            <Button
              size="md"
              variant="outline"
              onClick={() => navigate('/find-standard')}
              icon={<Zap size={15} />}
              className="px-4 py-2.5 font-medium w-full sm:w-auto"
            >
              Find Standard for Product
            </Button>
          </div>
        </section>

        {/* ─── Prominent Search Entry Point ─── */}
        <section aria-label="Search Standards and Compliance" className="space-y-3">
          <form onSubmit={handleSearchSubmit} className="w-full">
            <div className="flex items-center w-full rounded-xl border border-border-default bg-bg-secondary px-3.5 sm:px-4 py-1.5 transition-all focus-within:border-brand-500 focus-within:ring-2 focus-within:ring-brand-500/15 shadow-xs">
              <Search
                size={18}
                className="shrink-0 text-text-tertiary mr-3"
              />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Ask a compliance question or search standard number (e.g. IS 10500 drinking water)..."
                className="flex-1 h-11 bg-transparent border-0 outline-none text-xs sm:text-sm text-text-primary placeholder:text-text-tertiary min-w-0"
              />
              <Button
                type="submit"
                variant="primary"
                size="sm"
                disabled={!searchQuery.trim()}
                className="shrink-0 ml-2 px-3.5"
              >
                Search
              </Button>
            </div>
          </form>

          {/* Popular Queries */}
          <div className="flex flex-wrap items-center gap-2 pt-1 text-xs">
            <span className="text-text-tertiary font-medium">Popular queries:</span>
            {sampleQueries.map((query) => (
              <button
                key={query}
                type="button"
                onClick={() => navigate(`/assistant?q=${encodeURIComponent(query)}`)}
                className="px-2.5 py-1 rounded-md text-xs font-medium border border-border-default bg-bg-secondary text-text-secondary hover:text-text-primary hover:border-brand-500/40 hover:bg-bg-tertiary transition-all cursor-pointer"
              >
                {query}
              </button>
            ))}
          </div>
        </section>

        {/* ─── 6 Core Services Grid ─── */}
        <section aria-labelledby="services-heading" className="space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h2 id="services-heading" className="text-lg sm:text-xl font-semibold text-text-primary tracking-tight">
                Available Compliance Services
              </h2>
              <p className="text-xs text-text-secondary mt-0.5">
                Explore specialized discovery engines, statutory guides, and conformity workflows
              </p>
            </div>
            <span className="text-xs font-medium px-2.5 py-1 rounded-full border border-border-subtle bg-bg-secondary text-text-tertiary shrink-0">
              6 Modules
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5">
            {services.map((svc) => {
              const Icon = svc.icon;
              return (
                <div
                  key={svc.id}
                  onClick={() => navigate(svc.path)}
                  className="group flex flex-col justify-between min-h-[190px] p-5 sm:p-6 rounded-xl border border-border-default bg-bg-secondary hover:border-brand-500/50 hover:bg-bg-tertiary/60 transition-all duration-150 cursor-pointer shadow-xs hover:shadow-sm"
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="w-9 h-9 rounded-lg border border-border-subtle bg-bg-primary flex items-center justify-center shrink-0 text-brand-600 dark:text-brand-400 group-hover:border-brand-500/40 transition-colors shadow-xs">
                        <Icon size={18} />
                      </div>
                      <Badge variant="default" className="text-[10px] font-medium">
                        {svc.tag}
                      </Badge>
                    </div>

                    <div className="space-y-1.5">
                      <h3 className="text-sm sm:text-base font-semibold text-text-primary group-hover:text-brand-600 dark:group-hover:text-brand-400 transition-colors">
                        {svc.title}
                      </h3>
                      <p className="text-xs sm:text-sm text-text-secondary leading-relaxed line-clamp-3">
                        {svc.description}
                      </p>
                    </div>
                  </div>

                  <div className="mt-5 pt-3 border-t border-border-subtle flex items-center justify-between text-xs font-medium text-brand-600 dark:text-brand-400">
                    <span>Launch Workspace</span>
                    <ArrowRight size={13} className="group-hover:translate-x-1 transition-transform" />
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* ─── Knowledge Base & Infrastructure Status ─── */}
        <section className="pt-2">
          <div className="p-4 sm:p-5 rounded-xl border border-border-default bg-bg-secondary flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-xs">
            <div className="flex items-start sm:items-center gap-3 min-w-0">
              <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 mt-1 sm:mt-0 shrink-0 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
              <div className="space-y-0.5 min-w-0">
                <span className="font-semibold text-text-primary block text-sm">
                  BIS Knowledge Base & Classification Engine Active
                </span>
                <span className="text-text-secondary break-words">
                  {diagnostics?.database?.mode || 'MongoDB'} storage •{' '}
                  {diagnostics?.database?.standards_count ?? 13} standards indexed • Soft Voting Ensemble Classifier
                </span>
              </div>
            </div>

            <button
              type="button"
              onClick={() => navigate('/analytics')}
              className="inline-flex items-center gap-1.5 font-medium text-brand-600 dark:text-brand-400 hover:underline shrink-0 cursor-pointer"
            >
              <span>View System Analytics</span>
              <ArrowRight size={13} />
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}

export default HomePage;
