import { useState, useRef, useEffect, useCallback } from 'react';
import {
  Sparkles,
  Search,
  FileText,
  AlertTriangle,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Tag,
  ShieldCheck,
  RotateCcw,
  Copy,
  Check,
  CheckCircle2,
  SlidersHorizontal,
} from 'lucide-react';
import { Button, Card, Badge, Skeleton, EmptyState, ErrorState } from '../components/ui';
import { getRecommendations } from '../services/api/endpoints';
import type { RecommendResponse, Standard } from '../types/api';
import { cn } from '../utils/cn';
import { motion, AnimatePresence } from 'framer-motion';

// Quick suggested queries to give users immediate starting points
const SAMPLE_QUERIES = [
  'Packaged drinking water in 20-litre jars for commercial distribution',
  'Lithium-ion battery packs for electric two-wheelers and scooters',
  'Protective helmets for motorcycle riders and two-wheeler drivers',
  'Plugs and socket-outlets 16A for domestic appliances',
  'LED self-ballasted lamps and luminaires for general lighting',
];

interface ExtractedAnalysisShape {
  category?: string;
  product?: string;
  keywords?: string[];
  technical_terms?: string[];
  [key: string]: unknown;
}

export function FindStandardPage() {
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RecommendResponse | null>(null);
  const [showAnalysis, setShowAnalysis] = useState(true);
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);

  // Clean up any pending request on unmount
  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  const handleSearch = useCallback(
    async (queryText?: string) => {
      const textToSearch = (queryText ?? description).trim();
      if (!textToSearch) return;

      // Abort any ongoing request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      const controller = new AbortController();
      abortControllerRef.current = controller;

      setLoading(true);
      setError(null);

      try {
        const response = await getRecommendations(textToSearch, controller.signal);
        setResult(response);
        setShowAnalysis(true);
      } catch (err) {
        if (err instanceof DOMException && err.name === 'AbortError') {
          return;
        }
        setError(err instanceof Error ? err.message : 'Failed to retrieve recommendations. Please try again.');
      } finally {
        setLoading(false);
      }
    },
    [description]
  );

  const handleSelectSample = (sample: string) => {
    setDescription(sample);
    handleSearch(sample);
  };

  const handleReset = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setDescription('');
    setResult(null);
    setError(null);
  };

  const handleCopy = (code: string) => {
    navigator.clipboard?.writeText(code).then(() => {
      setCopiedCode(code);
      setTimeout(() => setCopiedCode(null), 2000);
    });
  };

  const analysis = result?.extracted_analysis as ExtractedAnalysisShape | undefined;
  const recommendations = result?.recommendations ?? [];

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-6">
      {/* Page Header */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <Badge variant="brand" className="px-2 py-0.5 text-xs font-medium">
            <Sparkles size={12} className="mr-1 inline" />
            AI Standard Recommender
          </Badge>
          <span className="text-xs text-text-tertiary">Semantic Match Engine</span>
        </div>
        <h1 className="text-2xl md:text-3xl font-semibold tracking-tight text-text-primary">
          Find Indian Standard by Product Description
        </h1>
        <p className="text-sm md:text-base text-text-secondary max-w-3xl leading-relaxed">
          Describe your product specifications, materials, or intended application in natural language. Our semantic
          engine cross-references official BIS gazettes, mandatory conformity schemes, and testing requirements.
        </p>
      </div>

      {/* Input Section */}
      <Card className="p-5 space-y-4">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label htmlFor="product-description-input" className="text-xs font-semibold uppercase tracking-wider text-text-secondary">
              Product Description & Specifications
            </label>
            <span className="text-xs text-text-tertiary">{description.length} characters</span>
          </div>

          <div className="relative rounded-lg border border-border-default bg-bg-primary transition-all focus-within:border-brand-500 focus-within:ring-1 focus-within:ring-brand-500/20">
            <textarea
              id="product-description-input"
              rows={4}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              onKeyDown={(e) => {
                if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                  e.preventDefault();
                  handleSearch();
                }
              }}
              placeholder="e.g. Lithium-ion battery packs for electric two-wheelers, with battery management system (BMS) and thermal runaway safeguards..."
              disabled={loading}
              className="w-full p-3.5 text-sm rounded-lg bg-transparent text-text-primary placeholder:text-text-tertiary outline-none resize-none leading-relaxed disabled:opacity-50"
            />
          </div>
        </div>

        {/* Action Buttons & Shortcut */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1">
          <div className="flex flex-wrap items-center gap-2.5">
            <Button
              variant="primary"
              size="md"
              onClick={() => handleSearch()}
              loading={loading}
              disabled={!description.trim() || loading}
              icon={<Search size={15} />}
            >
              {loading ? 'Analyzing Product...' : 'Find Applicable Standards'}
            </Button>

            {(description || result || error) && (
              <Button
                variant="outline"
                size="md"
                onClick={handleReset}
                disabled={loading}
                icon={<RotateCcw size={14} />}
              >
                Reset
              </Button>
            )}
          </div>

          <span className="text-xs text-text-tertiary hidden sm:inline">
            Press <kbd className="px-1.5 py-0.5 rounded border border-border-default bg-bg-secondary text-[11px] font-mono">Ctrl</kbd> + <kbd className="px-1.5 py-0.5 rounded border border-border-default bg-bg-secondary text-[11px] font-mono">Enter</kbd> to submit
          </span>
        </div>

        {/* Sample Prompt Chips */}
        <div className="pt-3 border-t border-border-subtle">
          <p className="text-xs font-medium text-text-tertiary mb-2">
            Suggested benchmark queries:
          </p>
          <div className="flex flex-wrap gap-1.5">
            {SAMPLE_QUERIES.map((sample) => (
              <button
                key={sample}
                type="button"
                onClick={() => handleSelectSample(sample)}
                disabled={loading}
                className="text-xs px-2.5 py-1.5 rounded-md border border-border-subtle bg-bg-secondary text-text-secondary hover:border-brand-500/50 hover:text-text-primary transition-all text-left disabled:opacity-50"
              >
                {sample}
              </button>
            ))}
          </div>
        </div>
      </Card>

      {/* Loading Skeletons */}
      {loading && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <Skeleton className="h-5 w-44" />
            <Skeleton className="h-5 w-20" />
          </div>
          {[1, 2, 3].map((n) => (
            <Card key={n} className="p-5 space-y-3">
              <div className="flex justify-between items-start">
                <div className="space-y-2 w-3/4">
                  <Skeleton className="h-6 w-32" />
                  <Skeleton className="h-5 w-4/5" />
                </div>
                <Skeleton className="h-6 w-20" />
              </div>
              <Skeleton className="h-14 w-full" />
              <div className="flex gap-2">
                <Skeleton className="h-5 w-24" />
                <Skeleton className="h-5 w-28" />
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <ErrorState
          title="Recommendation Failed"
          message={error}
          retry={() => handleSearch()}
        />
      )}

      {/* Empty State before any search */}
      {!result && !loading && !error && (
        <EmptyState
          icon={<FileText size={32} />}
          title="No recommendations yet"
          description="Enter your product specifications or select a sample query above to discover applicable Indian Standards, conformity schemes, and mandatory specifications."
        />
      )}

      {/* Search Results */}
      {result && !loading && !error && (
        <div className="space-y-6">
          {/* Extracted Analysis Section */}
          {analysis && (
            <Card className="overflow-hidden border border-border-default" padding="none">
              <button
                type="button"
                onClick={() => setShowAnalysis((prev) => !prev)}
                className="w-full flex items-center justify-between p-3.5 bg-bg-secondary cursor-pointer text-left transition-colors hover:bg-bg-tertiary/50"
                aria-expanded={showAnalysis}
              >
                <div className="flex items-center gap-2">
                  <Sparkles size={15} className="text-brand-600 dark:text-brand-400" />
                  <span className="text-xs font-semibold uppercase tracking-wider text-text-primary">
                    Extracted Semantic Analysis
                  </span>
                  <Badge variant="brand" className="text-[10px] px-1.5 py-0.5">
                    Query Insights
                  </Badge>
                </div>
                {showAnalysis ? (
                  <ChevronUp size={16} className="text-text-tertiary" />
                ) : (
                  <ChevronDown size={16} className="text-text-tertiary" />
                )}
              </button>

              <AnimatePresence initial={false}>
                {showAnalysis && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.18 }}
                  >
                    <div className="p-4 space-y-3 border-t border-border-subtle bg-bg-primary text-xs">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {analysis.category && (
                          <div>
                            <span className="text-[11px] font-medium text-text-tertiary block mb-1">
                              Inferred Category
                            </span>
                            <Badge variant="default" className="text-xs font-medium">
                              {analysis.category}
                            </Badge>
                          </div>
                        )}
                        {analysis.product && (
                          <div>
                            <span className="text-[11px] font-medium text-text-tertiary block mb-1">
                              Detected Product Entity
                            </span>
                            <span className="text-xs font-medium text-text-primary">
                              {analysis.product}
                            </span>
                          </div>
                        )}
                      </div>

                      {Array.isArray(analysis.keywords) && analysis.keywords.length > 0 && (
                        <div>
                          <span className="text-[11px] font-medium text-text-tertiary block mb-1.5">
                            Extracted Keywords
                          </span>
                          <div className="flex flex-wrap gap-1.5">
                            {analysis.keywords.map((kw, i) => (
                              <Badge key={i} variant="default" className="text-[11px]">
                                <Tag size={9} className="mr-1 inline" />
                                {kw}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}

                      {Array.isArray(analysis.technical_terms) && analysis.technical_terms.length > 0 && (
                        <div>
                          <span className="text-[11px] font-medium text-text-tertiary block mb-1.5">
                            Technical Parameters Identified
                          </span>
                          <div className="flex flex-wrap gap-1.5">
                            {analysis.technical_terms.map((term, i) => (
                              <Badge key={i} variant="info" className="text-[11px]">
                                {term}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </Card>
          )}

          {/* Results List Header */}
          <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
            <div>
              <h2 className="text-base font-semibold text-text-primary">
                Recommended Standards ({recommendations.length})
              </h2>
              <p className="text-xs text-text-secondary">
                Ranked by hybrid TF-IDF, vector similarity, and Bureau taxonomy matching.
              </p>
            </div>
            {result.product_description && (
              <span className="text-xs text-text-tertiary max-w-sm truncate">
                &ldquo;{result.product_description}&rdquo;
              </span>
            )}
          </div>

          {/* No Results Fallback */}
          {recommendations.length === 0 ? (
            <EmptyState
              icon={<SlidersHorizontal size={32} />}
              title="No matching standards found"
              description="No Indian Standards closely matched this specific product description. Try expanding with additional technical specifications, materials, or voltage/pressure ratings."
              action={
                <Button variant="secondary" size="sm" onClick={() => handleReset()}>
                  Clear & Try Again
                </Button>
              }
            />
          ) : (
            <div className="space-y-3.5">
              {recommendations.map((standard, index) => {
                const relevancePct = Math.round(
                  typeof standard.relevance_score === 'number'
                    ? standard.relevance_score > 1
                      ? standard.relevance_score
                      : standard.relevance_score * 100
                    : 85
                );

                const isMandatory = standard.mandatory_status?.toLowerCase().includes('mandatory');
                const sourceUrl =
                  standard.source ||
                  (standard as Standard & { source_url?: string }).source_url;

                return (
                  <motion.div
                    key={standard.standard_code || standard.id || index}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.2, delay: index * 0.04 }}
                  >
                    <Card className="p-5 space-y-4 hover:border-border-strong transition-colors">
                      {/* Standard Header */}
                      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                        <div className="space-y-1.5 flex-1 min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="font-mono text-sm md:text-base font-bold text-brand-600 dark:text-brand-400">
                              {standard.standard_code}
                            </span>
                            <button
                              type="button"
                              onClick={() => handleCopy(standard.standard_code)}
                              title="Copy Standard Code"
                              className="p-1 rounded text-text-tertiary hover:text-text-primary transition-colors"
                              aria-label={`Copy ${standard.standard_code}`}
                            >
                              {copiedCode === standard.standard_code ? (
                                <Check size={13} className="text-emerald-500" />
                              ) : (
                                <Copy size={13} />
                              )}
                            </button>

                            {/* Category Badge */}
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

                            {/* Verification Status Badge */}
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
                          <h3 className="text-sm md:text-base font-semibold leading-snug text-text-primary">
                            {standard.title}
                          </h3>
                        </div>

                        {/* Relevance Score Pill */}
                        <div className="flex flex-col items-end flex-shrink-0 p-2 rounded border border-border-subtle bg-bg-secondary text-right">
                          <span className="text-[10px] font-medium uppercase tracking-wider text-text-tertiary">
                            Match Score
                          </span>
                          <span className="text-sm font-bold text-brand-600 dark:text-brand-400">
                            {relevancePct}%
                          </span>
                          <div className="w-16 h-1 rounded-full bg-bg-tertiary overflow-hidden mt-1">
                            <div
                              className="h-full rounded-full bg-brand-500 transition-all duration-300"
                              style={{ width: `${Math.min(100, Math.max(0, relevancePct))}%` }}
                            />
                          </div>
                        </div>
                      </div>

                      {/* Scope Description */}
                      {standard.scope && (
                        <div className="space-y-1">
                          <h4 className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">
                            Scope of Standard
                          </h4>
                          <p className="text-xs md:text-sm text-text-secondary leading-relaxed">
                            {standard.scope}
                          </p>
                        </div>
                      )}

                      {/* Testing Parameters Box */}
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

                      {/* Additional Details Grid */}
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-1">
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
                              Reference & Clauses
                            </span>
                            <span className="text-text-secondary">
                              {standard.page_section_clause || standard.reference_document}
                            </span>
                          </div>
                        )}
                      </div>

                      {/* Applicable Products Tags */}
                      {Array.isArray(standard.applicable_products) && standard.applicable_products.length > 0 && (
                        <div className="space-y-1.5 pt-1">
                          <span className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary block">
                            Applicable Products:
                          </span>
                          <div className="flex flex-wrap gap-1.5">
                            {standard.applicable_products.map((p, idx) => (
                              <span
                                key={idx}
                                className="text-[11px] px-2 py-0.5 rounded border border-border-subtle bg-bg-secondary text-text-secondary"
                              >
                                {p}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Card Footer: Source Link */}
                      <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-border-subtle">
                        <div className="text-[11px] text-text-tertiary font-mono">
                          ID: {standard.id || standard.standard_code}
                        </div>

                        {sourceUrl && (
                          <a
                            href={sourceUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1.5 text-xs font-medium text-brand-600 dark:text-brand-400 hover:underline"
                          >
                            <span>Official Gazette Documentation</span>
                            <ExternalLink size={12} />
                          </a>
                        )}
                      </div>
                    </Card>
                  </motion.div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default FindStandardPage;
