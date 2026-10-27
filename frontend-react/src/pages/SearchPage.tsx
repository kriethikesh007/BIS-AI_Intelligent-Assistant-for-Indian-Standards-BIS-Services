import { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Search,
  BookOpen,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  CheckCircle2,
  Copy,
  Check,
  ShieldCheck,
  SlidersHorizontal,
  X,
} from 'lucide-react';
import { Button, Input, Card, Badge, Skeleton, EmptyState, ErrorState } from '../components/ui';
import { getStandards } from '../services/api/endpoints';
import type { Standard } from '../types/api';
import { useDebounce } from '../hooks/useUtils';
import { cn } from '../utils/cn';
import { motion, AnimatePresence } from 'framer-motion';

export function SearchPage() {
  const [standards, setStandards] = useState<Standard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter state
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearch = useDebounce(searchTerm, 200);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<'all' | 'mandatory' | 'voluntary'>('all');

  // Expansion and interaction states
  const [expandedIds, setExpandedIds] = useState<Record<string, boolean>>({});
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  // Fetch all standards on mount
  const fetchAllStandards = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getStandards();
      setStandards(response.standards || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load Indian Standards catalog.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAllStandards();
  }, [fetchAllStandards]);

  // Extract unique categories from loaded standards
  const categories = useMemo(() => {
    const catSet = new Set<string>();
    standards.forEach((s) => {
      if (s.category && s.category.trim()) {
        catSet.add(s.category.trim());
      }
    });
    return Array.from(catSet).sort();
  }, [standards]);

  // Client-side filtering
  const filteredStandards = useMemo(() => {
    const q = debouncedSearch.toLowerCase().trim();

    return standards.filter((s) => {
      // Category filter
      if (selectedCategory !== 'all' && s.category !== selectedCategory) {
        return false;
      }

      // Mandatory / Voluntary status filter
      if (selectedStatus !== 'all') {
        const isMandatory = s.mandatory_status?.toLowerCase().includes('mandatory');
        if (selectedStatus === 'mandatory' && !isMandatory) return false;
        if (selectedStatus === 'voluntary' && isMandatory) return false;
      }

      // Search keyword filter
      if (q) {
        const matchCode = s.standard_code?.toLowerCase().includes(q);
        const matchTitle = s.title?.toLowerCase().includes(q);
        const matchCategory = s.category?.toLowerCase().includes(q);
        const matchProduct = s.product?.toLowerCase().includes(q);
        const matchScope = s.scope?.toLowerCase().includes(q);
        const matchTesting = s.testing_parameters?.toLowerCase().includes(q);
        const matchApplicable = s.applicable_products?.some((p) => p.toLowerCase().includes(q));

        if (!matchCode && !matchTitle && !matchCategory && !matchProduct && !matchScope && !matchTesting && !matchApplicable) {
          return false;
        }
      }

      return true;
    });
  }, [standards, debouncedSearch, selectedCategory, selectedStatus]);

  const toggleExpand = (identifier: string) => {
    setExpandedIds((prev) => ({
      ...prev,
      [identifier]: !prev[identifier],
    }));
  };

  const handleExpandAll = () => {
    const allExpanded: Record<string, boolean> = {};
    filteredStandards.forEach((s) => {
      const id = s.standard_code || s.id || '';
      if (id) allExpanded[id] = true;
    });
    setExpandedIds(allExpanded);
  };

  const handleCollapseAll = () => {
    setExpandedIds({});
  };

  const handleClearFilters = () => {
    setSearchTerm('');
    setSelectedCategory('all');
    setSelectedStatus('all');
  };

  const handleCopy = (code: string) => {
    navigator.clipboard?.writeText(code).then(() => {
      setCopiedCode(code);
      setTimeout(() => setCopiedCode(null), 2000);
    });
  };

  const isFiltered = searchTerm.trim() !== '' || selectedCategory !== 'all' || selectedStatus !== 'all';

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
      {/* Page Header */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <Badge variant="brand" className="px-2 py-0.5 text-xs font-medium">
            <BookOpen size={12} className="mr-1 inline" />
            Standards Catalog
          </Badge>
          {!loading && (
            <span className="text-xs text-text-tertiary">
              {standards.length} standards indexed
            </span>
          )}
        </div>
        <h1 className="text-2xl md:text-3xl font-semibold tracking-tight text-text-primary">
          Search & Browse Indian Standards
        </h1>
        <p className="text-sm md:text-base text-text-secondary max-w-3xl leading-relaxed">
          Official Bureau of Indian Standards (BIS) specifications repository. Search by IS code or keywords, filter by
          industrial sector, and review mandatory compliance mandates and testing requirements.
        </p>
      </div>

      {/* Filter and Search Bar */}
      <Card className="p-4 md:p-5 space-y-3.5">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-2.5">
          {/* Search Input */}
          <div className="md:col-span-6 relative">
            <Input
              type="text"
              placeholder="Search by IS code (e.g. IS 10500), product, scope..."
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
                aria-label="Clear search"
              >
                <X size={14} />
              </button>
            )}
          </div>

          {/* Category Dropdown */}
          <div className="md:col-span-3">
            <div className="relative">
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="w-full h-9 px-3 text-xs md:text-sm rounded-md border border-border-default bg-bg-primary text-text-primary outline-none transition-colors appearance-none cursor-pointer focus:border-brand-500 focus:ring-1 focus:ring-brand-500/20"
                aria-label="Filter by Category"
              >
                <option value="all">All Sectors ({categories.length})</option>
                {categories.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
              <ChevronDown
                size={14}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none text-text-tertiary"
              />
            </div>
          </div>

          {/* Mandatory Status Selector */}
          <div className="md:col-span-3">
            <div className="relative">
              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value as 'all' | 'mandatory' | 'voluntary')}
                className="w-full h-9 px-3 text-xs md:text-sm rounded-md border border-border-default bg-bg-primary text-text-primary outline-none transition-colors appearance-none cursor-pointer focus:border-brand-500 focus:ring-1 focus:ring-brand-500/20"
                aria-label="Filter by Mandatory Status"
              >
                <option value="all">All Statuses</option>
                <option value="mandatory">Mandatory Orders Only</option>
                <option value="voluntary">Voluntary Only</option>
              </select>
              <ChevronDown
                size={14}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none text-text-tertiary"
              />
            </div>
          </div>
        </div>

        {/* Filter status bar & Controls */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-border-subtle text-xs">
          <div className="flex items-center gap-2">
            <span className="font-medium text-text-primary">
              Showing {filteredStandards.length} of {standards.length} standards
            </span>
            {isFiltered && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClearFilters}
                className="h-6 px-2 text-xs"
              >
                Reset filters
              </Button>
            )}
          </div>

          {filteredStandards.length > 0 && (
            <div className="flex items-center gap-2 text-xs">
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
          {[1, 2, 3, 4, 5].map((n) => (
            <Card key={n} className="p-5 space-y-3">
              <div className="flex justify-between items-start">
                <div className="space-y-2 w-3/4">
                  <div className="flex gap-2">
                    <Skeleton className="h-6 w-28" />
                    <Skeleton className="h-6 w-20" />
                  </div>
                  <Skeleton className="h-5 w-4/5" />
                </div>
                <Skeleton className="h-6 w-24" />
              </div>
              <Skeleton className="h-10 w-full" />
            </Card>
          ))}
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <ErrorState
          title="Could not load standards catalog"
          message={error}
          retry={fetchAllStandards}
        />
      )}

      {/* Empty State when no standards match filters */}
      {!loading && !error && filteredStandards.length === 0 && (
        <EmptyState
          icon={<SlidersHorizontal size={32} />}
          title="No standards found"
          description={
            isFiltered
              ? "We couldn't find any Indian Standards matching your active search and category filters. Try broadening your keywords or clearing the filter selection."
              : 'No Indian Standards records are currently indexed in the database.'
          }
          action={
            isFiltered ? (
              <Button variant="secondary" size="sm" onClick={handleClearFilters}>
                Clear All Filters
              </Button>
            ) : (
              <Button variant="primary" size="sm" onClick={fetchAllStandards}>
                Reload Catalog
              </Button>
            )
          }
        />
      )}

      {/* Standards List */}
      {!loading && !error && filteredStandards.length > 0 && (
        <div className="space-y-3">
          {filteredStandards.map((standard, index) => {
            const identifier = standard.standard_code || standard.id || `std-${index}`;
            const isExpanded = !!expandedIds[identifier];
            const isMandatory = standard.mandatory_status?.toLowerCase().includes('mandatory');
            const sourceUrl =
              standard.source ||
              (standard as Standard & { source_url?: string }).source_url;

            return (
              <motion.div
                key={identifier}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.18, delay: Math.min(index * 0.02, 0.25) }}
              >
                <Card
                  className={cn(
                    'p-4 md:p-5 transition-colors',
                    isExpanded ? 'border-brand-500/50' : 'hover:border-border-strong'
                  )}
                >
                  {/* Card Main Row */}
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                    <div className="space-y-1.5 flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        {/* Standard Code */}
                        <span className="font-mono text-sm md:text-base font-bold text-brand-600 dark:text-brand-400">
                          {standard.standard_code}
                        </span>

                        {/* Copy Code */}
                        <button
                          type="button"
                          onClick={() => handleCopy(standard.standard_code)}
                          title="Copy IS Code"
                          className="p-1 rounded text-text-tertiary hover:text-text-primary transition-colors"
                          aria-label={`Copy ${standard.standard_code}`}
                        >
                          {copiedCode === standard.standard_code ? (
                            <Check size={13} className="text-emerald-500" />
                          ) : (
                            <Copy size={13} />
                          )}
                        </button>

                        {/* Category */}
                        {standard.category && (
                          <Badge variant="default" className="text-[11px]">
                            {standard.category}
                          </Badge>
                        )}

                        {/* Mandatory / Voluntary Badge */}
                        {standard.mandatory_status && (
                          <Badge
                            variant={isMandatory ? 'warning' : 'default'}
                            className="text-[11px] font-medium"
                          >
                            {isMandatory ? (
                              <AlertTriangle size={10} className="mr-1 inline" />
                            ) : (
                              <CheckCircle2 size={10} className="mr-1 inline" />
                            )}
                            {standard.mandatory_status}
                          </Badge>
                        )}

                        {/* Verification Status */}
                        {standard.verification_status && (
                          <Badge
                            variant={standard.verification_status === 'verified' ? 'success' : 'default'}
                            className="text-[11px] font-medium"
                          >
                            <ShieldCheck size={10} className="mr-1 inline text-emerald-500" />
                            {standard.verification_status === 'verified' ? 'Verified Catalog' : standard.verification_status}
                          </Badge>
                        )}
                      </div>

                      {/* Standard Title */}
                      <h3
                        className="text-sm md:text-base font-semibold leading-snug text-text-primary cursor-pointer hover:text-brand-600 dark:hover:text-brand-400 transition-colors"
                        onClick={() => toggleExpand(identifier)}
                      >
                        {standard.title}
                      </h3>
                    </div>

                    {/* Expand/Collapse Toggle Button */}
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleExpand(identifier)}
                        className="h-7 px-2 text-xs font-medium gap-1"
                      >
                        {isExpanded ? (
                          <>
                            <span>Hide Details</span>
                            <ChevronUp size={13} />
                          </>
                        ) : (
                          <>
                            <span>View Details</span>
                            <ChevronDown size={13} />
                          </>
                        )}
                      </Button>
                    </div>
                  </div>

                  {/* Summary Scope Preview when collapsed */}
                  {!isExpanded && standard.scope && (
                    <p
                      className="text-xs line-clamp-2 mt-2 text-text-secondary leading-relaxed cursor-pointer"
                      onClick={() => toggleExpand(identifier)}
                    >
                      {standard.scope}
                    </p>
                  )}

                  {/* Expandable Detail Section */}
                  <AnimatePresence initial={false}>
                    {isExpanded && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.18 }}
                        className="overflow-hidden"
                      >
                        <div className="mt-4 pt-4 border-t border-border-subtle space-y-3.5">
                          {/* Full Scope */}
                          {standard.scope && (
                            <div className="space-y-1">
                              <h4 className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">
                                Scope & Application
                              </h4>
                              <p className="text-xs md:text-sm text-text-secondary leading-relaxed">
                                {standard.scope}
                              </p>
                            </div>
                          )}

                          {/* Testing Parameters */}
                          {standard.testing_parameters && (
                            <div className="p-3 rounded-md border border-border-subtle bg-bg-secondary space-y-1">
                              <div className="flex items-center gap-1.5">
                                <ShieldCheck size={13} className="text-brand-600 dark:text-brand-400" />
                                <span className="text-xs font-semibold text-text-primary">
                                  Prescribed Testing Parameters
                                </span>
                              </div>
                              <p className="text-xs text-text-secondary leading-relaxed">
                                {standard.testing_parameters}
                              </p>
                            </div>
                          )}

                          {/* Grid with Scheme, Clause, Reference */}
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                            {standard.certification_scheme && (
                              <div>
                                <span className="font-medium text-text-tertiary block mb-0.5">
                                  Certification Scheme
                                </span>
                                <span className="font-medium text-text-primary">
                                  {standard.certification_scheme}
                                </span>
                              </div>
                            )}

                            {(standard.page_section_clause || standard.reference_document) && (
                              <div>
                                <span className="font-medium text-text-tertiary block mb-0.5">
                                  Reference Clause / Schedule
                                </span>
                                <span className="text-text-secondary">
                                  {standard.page_section_clause || standard.reference_document}
                                </span>
                              </div>
                            )}

                            {standard.product && (
                              <div className="sm:col-span-2">
                                <span className="font-medium text-text-tertiary block mb-0.5">
                                  Primary Products Covered
                                </span>
                                <span className="text-text-secondary">
                                  {standard.product}
                                </span>
                              </div>
                            )}
                          </div>

                          {/* Applicable Products tags */}
                          {Array.isArray(standard.applicable_products) && standard.applicable_products.length > 0 && (
                            <div className="space-y-1.5">
                              <span className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary block">
                                Recognized Product Synonyms:
                              </span>
                              <div className="flex flex-wrap gap-1.5">
                                {standard.applicable_products.map((item, idx) => (
                                  <span
                                    key={idx}
                                    className="text-[11px] px-2 py-0.5 rounded border border-border-subtle bg-bg-secondary text-text-secondary"
                                  >
                                    {item}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Official Link */}
                          <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-border-subtle text-xs">
                            <span className="text-text-tertiary font-mono text-[11px]">
                              Standard ID: {standard.id || standard.standard_code}
                            </span>
                            {sourceUrl && (
                              <a
                                href={sourceUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1.5 text-brand-600 dark:text-brand-400 hover:underline font-medium"
                              >
                                <span>Official BIS Document Portal</span>
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

export default SearchPage;
