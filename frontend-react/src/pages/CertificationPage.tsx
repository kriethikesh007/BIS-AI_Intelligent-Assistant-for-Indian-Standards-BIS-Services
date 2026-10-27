import { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Award,
  Search,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  FileText,
  Layers,
  Sparkles,
  BookOpen,
  DollarSign,
  Building2,
  ShieldCheck,
  X,
} from 'lucide-react';
import { Button, Input, Card, Badge, Skeleton, EmptyState, ErrorState } from '../components/ui';
import { getCertificationSchemes } from '../services/api/endpoints';
import type { CertificationScheme } from '../types/api';
import { cn } from '../utils/cn';
import { motion, AnimatePresence } from 'framer-motion';

export function CertificationPage() {
  const [schemes, setSchemes] = useState<CertificationScheme[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Search filter
  const [searchTerm, setSearchTerm] = useState('');

  // Expand/collapse tracking
  const [expandedIds, setExpandedIds] = useState<Record<string, boolean>>({});

  const fetchSchemes = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getCertificationSchemes();
      const loaded = response.schemes || [];
      setSchemes(loaded);
      // Expand the first scheme by default
      if (loaded.length > 0) {
        const firstKey = loaded[0].id || loaded[0].scheme_name || 'scheme-0';
        setExpandedIds({ [firstKey]: true });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load BIS certification schemes.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSchemes();
  }, [fetchSchemes]);

  // Client-side search filtering
  const filteredSchemes = useMemo(() => {
    const q = searchTerm.toLowerCase().trim();
    if (!q) return schemes;

    return schemes.filter((s) => {
      const name = (s.scheme_name || s.name || '').toLowerCase();
      const desc = (s.description || '').toLowerCase();
      const applicable = (s.applicable_to || '').toLowerCase();
      const proc = (typeof s.procedure === 'string' ? s.procedure : typeof s.process === 'string' ? s.process : '').toLowerCase();
      const concessions = (typeof s.concessions_msme_startups === 'string' ? s.concessions_msme_startups : '').toLowerCase();

      return (
        name.includes(q) ||
        desc.includes(q) ||
        applicable.includes(q) ||
        proc.includes(q) ||
        concessions.includes(q)
      );
    });
  }, [schemes, searchTerm]);

  const toggleExpand = (identifier: string) => {
    setExpandedIds((prev) => ({
      ...prev,
      [identifier]: !prev[identifier],
    }));
  };

  const handleExpandAll = () => {
    const allExp: Record<string, boolean> = {};
    filteredSchemes.forEach((s, idx) => {
      const key = s.id || s.scheme_name || `scheme-${idx}`;
      allExp[key] = true;
    });
    setExpandedIds(allExp);
  };

  const handleCollapseAll = () => {
    setExpandedIds({});
  };

  const parseProcedureSteps = (procedureText?: unknown): string[] => {
    if (typeof procedureText !== 'string' || !procedureText.trim()) return [];

    const lines = procedureText.split('\n').map((l) => l.trim()).filter(Boolean);
    const isNumbered = lines.some((l) => /^\d+[.)]\s+/.test(l));

    if (isNumbered) {
      return lines.map((l) => l.replace(/^\d+[.)]\s+/, '').trim());
    }

    return [procedureText];
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
      {/* Page Header */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <Badge variant="brand" className="px-2 py-0.5 text-xs font-medium">
            <Award size={12} className="mr-1 inline" />
            Conformity Assessment Framework
          </Badge>
          {!loading && (
            <span className="text-xs text-text-tertiary">
              {schemes.length} schemes established
            </span>
          )}
        </div>

        <h1 className="text-2xl md:text-3xl font-semibold tracking-tight text-text-primary">
          BIS Certification Schemes Guide
        </h1>

        <p className="text-sm md:text-base text-text-secondary max-w-3xl leading-relaxed">
          Under the Bureau of Indian Standards Act, 2016 and Conformity Assessment Regulations, 2018, BIS operates multiple
          specialized schemes to evaluate product quality, consumer safety, and regulatory compliance.
        </p>
      </div>

      {/* Quick Overview Highlights */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <Card className="p-3.5 flex items-start gap-3">
          <div className="p-2 rounded-md bg-brand-500/10 text-brand-600 dark:text-brand-400 shrink-0">
            <Award size={18} />
          </div>
          <div className="space-y-0.5 min-w-0">
            <div className="text-xs font-semibold text-text-primary">
              Scheme I (ISI Mark)
            </div>
            <p className="text-[11px] text-text-secondary line-clamp-2">
              Third-party factory audit & testing for domestic products under mandatory QCOs.
            </p>
          </div>
        </Card>

        <Card className="p-3.5 flex items-start gap-3">
          <div className="p-2 rounded-md bg-sky-500/10 text-sky-600 dark:text-sky-400 shrink-0">
            <ShieldCheck size={18} />
          </div>
          <div className="space-y-0.5 min-w-0">
            <div className="text-xs font-semibold text-text-primary">
              Scheme II (CRS)
            </div>
            <p className="text-[11px] text-text-secondary line-clamp-2">
              Compulsory Registration Scheme for notified IT, electronics, and solar PV modules.
            </p>
          </div>
        </Card>

        <Card className="p-3.5 flex items-start gap-3">
          <div className="p-2 rounded-md bg-amber-500/10 text-amber-600 dark:text-amber-400 shrink-0">
            <Building2 size={18} />
          </div>
          <div className="space-y-0.5 min-w-0">
            <div className="text-xs font-semibold text-text-primary">
              FMCS
            </div>
            <p className="text-[11px] text-text-secondary line-clamp-2">
              Foreign Manufacturers Certification Scheme for overseas factories exporting to India.
            </p>
          </div>
        </Card>

        <Card className="p-3.5 flex items-start gap-3">
          <div className="p-2 rounded-md bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 shrink-0">
            <Sparkles size={18} />
          </div>
          <div className="space-y-0.5 min-w-0">
            <div className="text-xs font-semibold text-text-primary">
              MSME Concessions
            </div>
            <p className="text-[11px] text-text-secondary line-clamp-2">
              Up to 20% to 50% rebates on application and marking fees for registered micro & small enterprises.
            </p>
          </div>
        </Card>
      </div>

      {/* Search & Actions Bar */}
      <Card className="p-4 space-y-3">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          <div className="relative flex-1 max-w-md">
            <Input
              type="text"
              placeholder="Filter schemes (e.g. ISI, CRS, electronics, MSME, import)..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              icon={<Search size={15} />}
              className="pr-8"
            />
            {searchTerm && (
              <button
                type="button"
                onClick={() => setSearchTerm('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-0.5 rounded text-text-tertiary hover:text-text-primary transition-colors"
                aria-label="Clear filter"
              >
                <X size={14} />
              </button>
            )}
          </div>

          {filteredSchemes.length > 0 && (
            <div className="flex items-center gap-3 text-xs flex-shrink-0">
              <span className="text-text-secondary">
                Showing {filteredSchemes.length} of {schemes.length} schemes
              </span>
              <button
                type="button"
                onClick={handleExpandAll}
                className="text-brand-600 dark:text-brand-400 hover:underline font-medium"
              >
                Expand all
              </button>
              <span className="text-border-default">•</span>
              <button
                type="button"
                onClick={handleCollapseAll}
                className="text-text-tertiary hover:text-text-primary font-medium transition-colors"
              >
                Collapse all
              </button>
            </div>
          )}
        </div>
      </Card>

      {/* Loading Skeletons */}
      {loading && (
        <div className="space-y-3.5">
          {[1, 2, 3].map((n) => (
            <Card key={n} className="p-5 space-y-3">
              <div className="flex justify-between items-start">
                <div className="space-y-2 w-3/4">
                  <Skeleton className="h-6 w-36" />
                  <Skeleton className="h-5 w-4/5" />
                </div>
                <Skeleton className="h-6 w-20" />
              </div>
              <Skeleton className="h-20 w-full" />
            </Card>
          ))}
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <ErrorState
          title="Could not load certification schemes"
          message={error}
          retry={fetchSchemes}
        />
      )}

      {/* Empty State when no schemes match filter */}
      {!loading && !error && filteredSchemes.length === 0 && (
        <EmptyState
          icon={<Award size={32} />}
          title="No certification schemes found"
          description={
            searchTerm
              ? `No certification schemes matched "${searchTerm}". Try searching for terms like "ISI", "CRS", or "import".`
              : 'No certification schemes data available at this time.'
          }
          action={
            searchTerm ? (
              <Button variant="secondary" size="sm" onClick={() => setSearchTerm('')}>
                Clear Filter
              </Button>
            ) : (
              <Button variant="primary" size="sm" onClick={fetchSchemes}>
                Reload Schemes
              </Button>
            )
          }
        />
      )}

      {/* Certification Schemes Accordion List */}
      {!loading && !error && filteredSchemes.length > 0 && (
        <div className="space-y-3.5">
          {filteredSchemes.map((scheme, index) => {
            const identifier = scheme.id || scheme.scheme_name || `scheme-${index}`;
            const isExpanded = !!expandedIds[identifier];

            const schemeTitle =
              scheme.scheme_name || scheme.name || (scheme as { title?: string }).title || scheme.id || 'Certification Scheme';
            const schemeId = scheme.id;
            const description = scheme.description;
            const applicableTo = scheme.applicable_to || (scheme as { scope?: string }).scope;
            const eligibility = scheme.eligibility;
            const procedureText =
              scheme.procedure ||
              scheme.process ||
              (scheme as { steps?: string }).steps;
            const steps = parseProcedureSteps(procedureText);
            const concessions =
              typeof scheme.concessions_msme_startups === 'string'
                ? scheme.concessions_msme_startups
                : typeof (scheme as { msme_concessions?: unknown }).msme_concessions === 'string'
                ? ((scheme as { msme_concessions?: string }).msme_concessions as string)
                : undefined;
            const fees =
              typeof scheme.fees === 'string'
                ? scheme.fees
                : typeof (scheme as { fee_structure?: unknown }).fee_structure === 'string'
                ? ((scheme as { fee_structure?: string }).fee_structure as string)
                : undefined;
            const referenceDoc =
              typeof scheme.reference === 'string'
                ? scheme.reference
                : typeof (scheme as { source_document?: unknown }).source_document === 'string'
                ? ((scheme as { source_document?: string }).source_document as string)
                : typeof (scheme as { reference_clause?: unknown }).reference_clause === 'string'
                ? ((scheme as { reference_clause?: string }).reference_clause as string)
                : undefined;
            const sourceUrl =
              typeof (scheme as { source_url?: unknown }).source_url === 'string'
                ? ((scheme as { source_url?: string }).source_url as string)
                : typeof scheme.source === 'string'
                ? scheme.source
                : typeof (scheme as { url?: unknown }).url === 'string'
                ? ((scheme as { url?: string }).url as string)
                : undefined;

            return (
              <motion.div
                key={identifier}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.18, delay: Math.min(index * 0.03, 0.25) }}
              >
                <Card
                  className={cn(
                    'p-4 md:p-5 transition-colors',
                    isExpanded ? 'border-brand-500/50' : 'hover:border-border-strong'
                  )}
                >
                  {/* Scheme Header Row */}
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                    <div className="space-y-1.5 flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        {schemeId && (
                          <span className="font-mono text-xs font-bold px-2 py-0.5 rounded border border-border-subtle bg-bg-secondary text-brand-600 dark:text-brand-400">
                            {schemeId}
                          </span>
                        )}

                        <Badge variant="brand" className="text-[11px]">
                          BIS Official Scheme
                        </Badge>
                      </div>

                      <h3
                        className="text-base md:text-lg font-semibold leading-snug text-text-primary cursor-pointer hover:text-brand-600 dark:hover:text-brand-400 transition-colors"
                        onClick={() => toggleExpand(identifier)}
                      >
                        {schemeTitle}
                      </h3>

                      {description && (
                        <p
                          className={cn(
                            'text-xs md:text-sm text-text-secondary leading-relaxed cursor-pointer',
                            !isExpanded && 'line-clamp-2'
                          )}
                          onClick={() => toggleExpand(identifier)}
                        >
                          {description}
                        </p>
                      )}
                    </div>

                    {/* Toggle Button */}
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <Button
                        variant={isExpanded ? 'secondary' : 'outline'}
                        size="sm"
                        onClick={() => toggleExpand(identifier)}
                        className="h-7 px-2.5 text-xs gap-1 font-medium"
                      >
                        {isExpanded ? (
                          <>
                            <span>Collapse</span>
                            <ChevronUp size={13} />
                          </>
                        ) : (
                          <>
                            <span>View Scheme Guide</span>
                            <ChevronDown size={13} />
                          </>
                        )}
                      </Button>
                    </div>
                  </div>

                  {/* Expandable Section */}
                  <AnimatePresence initial={false}>
                    {isExpanded && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.18 }}
                        className="overflow-hidden"
                      >
                        <div className="mt-4 pt-4 border-t border-border-subtle space-y-4">
                          {/* Applicable To / Scope */}
                          {applicableTo && (
                            <div className="space-y-1">
                              <div className="flex items-center gap-1.5">
                                <Layers size={13} className="text-brand-600 dark:text-brand-400" />
                                <h4 className="text-[11px] font-semibold uppercase tracking-wider text-text-primary">
                                  Applicable Products & Industry Scope
                                </h4>
                              </div>
                              <p className="text-xs md:text-sm text-text-secondary leading-relaxed pl-5">
                                {applicableTo}
                              </p>
                            </div>
                          )}

                          {/* Eligibility Criteria (if present) */}
                          {eligibility && (
                            <div className="space-y-1">
                              <div className="flex items-center gap-1.5">
                                <CheckCircle2 size={13} className="text-emerald-500" />
                                <h4 className="text-[11px] font-semibold uppercase tracking-wider text-text-primary">
                                  Eligibility Criteria
                                </h4>
                              </div>
                              <p className="text-xs md:text-sm text-text-secondary leading-relaxed pl-5">
                                {eligibility}
                              </p>
                            </div>
                          )}

                          {/* Step-by-Step Procedure / Process */}
                          {steps.length > 0 && (
                            <div className="space-y-2">
                              <div className="flex items-center gap-1.5">
                                <FileText size={13} className="text-brand-600 dark:text-brand-400" />
                                <h4 className="text-[11px] font-semibold uppercase tracking-wider text-text-primary">
                                  Application & Conformity Assessment Procedure
                                </h4>
                              </div>

                              <div className="space-y-1.5 pl-1">
                                {steps.map((step, sIdx) => (
                                  <div
                                    key={sIdx}
                                    className="flex items-start gap-2.5 p-2.5 rounded-md border border-border-subtle bg-bg-secondary text-xs"
                                  >
                                    <span className="flex items-center justify-center w-5 h-5 rounded-full bg-brand-500 text-white font-bold text-[10px] shrink-0">
                                      {sIdx + 1}
                                    </span>
                                    <p className="leading-relaxed flex-1 text-text-secondary">
                                      {step}
                                    </p>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* MSME & Startup Concessions Callout */}
                          {concessions && (
                            <div className="p-3.5 rounded-md border border-emerald-500/20 bg-emerald-500/5 space-y-1">
                              <div className="flex items-center gap-1.5">
                                <Sparkles size={14} className="text-emerald-600 dark:text-emerald-400" />
                                <h4 className="text-xs font-semibold uppercase tracking-wider text-emerald-700 dark:text-emerald-300">
                                  Special Concessions for MSMEs & Startups
                                </h4>
                              </div>
                              <p className="text-xs text-text-secondary leading-relaxed">
                                {concessions}
                              </p>
                            </div>
                          )}

                          {/* Fees Information (if present) */}
                          {fees && (
                            <div className="space-y-1">
                              <div className="flex items-center gap-1.5">
                                <DollarSign size={13} className="text-amber-500" />
                                <h4 className="text-[11px] font-semibold uppercase tracking-wider text-text-primary">
                                  Fee Structure & Commercials
                                </h4>
                              </div>
                              <p className="text-xs text-text-secondary leading-relaxed pl-5">
                                {fees}
                              </p>
                            </div>
                          )}

                          {/* Legal & Regulatory Reference */}
                          {referenceDoc && (
                            <div className="space-y-1 text-xs pt-1">
                              <div className="flex items-center gap-1.5">
                                <BookOpen size={13} className="text-text-tertiary" />
                                <span className="font-semibold text-text-primary">
                                  Statutory Reference:
                                </span>
                              </div>
                              <p className="pl-5 text-text-secondary">
                                {referenceDoc}
                              </p>
                            </div>
                          )}

                          {/* Card Footer with Official Portal Link */}
                          <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-border-subtle text-xs">
                            <span className="text-text-tertiary font-mono text-[11px]">
                              Scheme ID: {schemeId || 'N/A'}
                            </span>

                            {sourceUrl && (
                              <a
                                href={sourceUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1.5 text-brand-600 dark:text-brand-400 hover:underline font-medium"
                              >
                                <span>Official BIS Scheme Portal</span>
                                <ExternalLink size={12} />
                              </a>
                            )}
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </Card>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default CertificationPage;
