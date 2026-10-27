import { useState, useEffect, useMemo, useCallback } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import {
  BarChart3,
  Brain,
  Cpu,
  Activity,
  AlertCircle,
  KeyRound,
  Lock,
  LogOut,
  RefreshCw,
  FileText,
  Award,
  FlaskConical,
  Gem,
  HelpCircle,
  Sparkles,
} from 'lucide-react';
import {
  Card,
  Badge,
  Input,
  Button,
  Dialog,
  PageLoader,
} from '../components/ui';
import { getAdminAnalytics, getDiagnostics, getPublicMetrics, type PublicMetricsResponse } from '../services/api/endpoints';
import type {
  AdminAnalyticsData,
  DiagnosticsData,
  ModelComparison,
} from '../types/api';

const SESSION_KEY_NAME = 'bis_admin_api_key';

/* Helper to parse percentage string ("54.55%") or decimal (0.5455) to float (54.55) */
function parsePercentage(value?: string | number | null): number {
  if (value === undefined || value === null) return 0;
  if (typeof value === 'number') {
    return value <= 1 ? +(value * 100).toFixed(2) : +value.toFixed(2);
  }
  const clean = value.replace('%', '').trim();
  const parsed = parseFloat(clean);
  return isNaN(parsed) ? 0 : parsed;
}

/* Helper to format decimal or percentage as percentage string */
function formatPercentDisplay(value?: string | number | null): string {
  if (value === undefined || value === null) return 'N/A';
  if (typeof value === 'string') {
    if (value.includes('%')) return value;
    const num = parseFloat(value);
    if (!isNaN(num)) {
      return num <= 1 ? `${(num * 100).toFixed(2)}%` : `${num.toFixed(2)}%`;
    }
    return value;
  }
  return value <= 1 ? `${(value * 100).toFixed(2)}%` : `${value.toFixed(2)}%`;
}

export default function AnalyticsPage() {
  // Diagnostics data (public, no auth needed)
  const [diagnostics, setDiagnostics] = useState<DiagnosticsData | null>(null);
  const [publicMetrics, setPublicMetrics] = useState<PublicMetricsResponse | null>(null);
  const [diagLoading, setDiagLoading] = useState(true);
  const [diagError, setDiagError] = useState<string | null>(null);

  // Admin Analytics data (requires API key)
  const [analytics, setAnalytics] = useState<AdminAnalyticsData | null>(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [analyticsError, setAnalyticsError] = useState<string | null>(null);

  // Admin Auth state
  const [apiKey, setApiKey] = useState<string>(() => {
    return sessionStorage.getItem(SESSION_KEY_NAME) || '';
  });
  const [keyInput, setKeyInput] = useState('');
  const [isAuthDialogOpen, setIsAuthDialogOpen] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);

  // Active chart metric filter
  const [chartMetric, setChartMetric] = useState<'Accuracy' | 'Precision' | 'Recall' | 'Weighted F1'>('Accuracy');

  // Load diagnostics and public ML benchmarks unconditionally
  const loadDiagnostics = useCallback(async () => {
    setDiagLoading(true);
    setDiagError(null);
    try {
      const [diagData, metricsData] = await Promise.all([
        getDiagnostics().catch(() => null),
        getPublicMetrics().catch(() => null),
      ]);
      if (diagData) setDiagnostics(diagData);
      if (metricsData) setPublicMetrics(metricsData);
    } catch (err) {
      setDiagError(err instanceof Error ? err.message : 'Failed to reach diagnostic health endpoint');
    } finally {
      setDiagLoading(false);
    }
  }, []);

  // Fetch admin analytics using the provided key
  const fetchAnalytics = useCallback(async (keyToUse: string) => {
    if (!keyToUse) return;
    setAnalyticsLoading(true);
    setAnalyticsError(null);
    setAuthError(null);
    try {
      const data = await getAdminAnalytics(keyToUse);
      setAnalytics(data);
      sessionStorage.setItem(SESSION_KEY_NAME, keyToUse);
      setIsAuthDialogOpen(false);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Authentication failed';
      setAnalyticsError(message);
      setAuthError(message);
    } finally {
      setAnalyticsLoading(false);
    }
  }, []);

  // On mount: fetch diagnostics & public benchmarks; if session key exists, fetch admin metrics
  useEffect(() => {
    loadDiagnostics();
    if (apiKey) {
      fetchAnalytics(apiKey);
    }
  }, [loadDiagnostics, fetchAnalytics, apiKey]);

  // Handle key submission from dialog
  const handleKeySubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const trimmed = keyInput.trim();
    if (!trimmed) {
      setAuthError('Please enter a valid administrative API key.');
      return;
    }
    setApiKey(trimmed);
    fetchAnalytics(trimmed);
  };

  // Clear session key
  const handleLogout = () => {
    sessionStorage.removeItem(SESSION_KEY_NAME);
    setApiKey('');
    setKeyInput('');
    setAnalytics(null);
    setAnalyticsError(null);
    setAuthError(null);
  };

  // Extract model comparison data (falls back to public benchmarks)
  const modelComparisonList: ModelComparison[] = useMemo(() => {
    if (analytics?.model_comparison || analytics?.model_benchmarks || analytics?.ml_statistics?.ensemble_performance) {
      return (
        analytics.model_comparison ||
        analytics.model_benchmarks ||
        analytics.ml_statistics?.ensemble_performance ||
        []
      );
    }
    if (publicMetrics?.data?.comparison_table) {
      return publicMetrics.data.comparison_table;
    }
    return [];
  }, [analytics, publicMetrics]);

  // Chart data formatted from model comparisons
  const chartData = useMemo(() => {
    return modelComparisonList.map((item) => ({
      name: item.Model,
      Accuracy: parsePercentage(item.Accuracy),
      Precision: parsePercentage(item.Precision),
      Recall: parsePercentage(item.Recall),
      'Macro F1': parsePercentage(item['Macro F1']),
      'Weighted F1': parsePercentage(item['Weighted F1']),
    }));
  }, [modelComparisonList]);

  // Knowledge aggregates: uses admin counts if available, otherwise diagnostics database counts
  const knowledgeCounts = useMemo(() => {
    if (analytics?.knowledge_counts) return analytics.knowledge_counts;
    if (diagnostics?.database) {
      const db = diagnostics.database;
      return {
        total_standards: Number(db.standards_count) || 0,
        total_certification_records: Number(db.schemes_count) || 0,
        total_laboratory_records: Number(db.laboratories_count) || 0,
        total_hallmarking_records: 6,
        total_faqs: Number(db.faqs_count) || 0,
      };
    }
    return undefined;
  }, [analytics, diagnostics]);

  // ML stats: uses admin analytics if available, otherwise public model metrics
  const mlStats: AdminAnalyticsData['ml_statistics'] | undefined = useMemo(() => {
    if (analytics?.ml_statistics) return analytics.ml_statistics;
    const m = (publicMetrics?.metrics as Record<string, unknown>)?.machine_learning_metrics || publicMetrics?.metrics;
    if (m && typeof m === 'object') {
      const rec = m as Record<string, unknown>;
      const f1Val = (rec.f1_weighted ?? rec.ensemble_f1_weighted) as number | undefined;
      return {
        accuracy: (rec.accuracy ?? rec.ensemble_accuracy) as number | undefined,
        precision: (rec.precision_weighted ?? rec.ensemble_precision_weighted) as number | undefined,
        recall: (rec.recall_weighted ?? rec.ensemble_recall_weighted) as number | undefined,
        f1: f1Val,
        f1_score: f1Val,
        training_samples: 88,
        test_samples: 22,
        best_model: 'Voting Ensemble (Soft Voting)',
        classes: rec.classes as string[] | undefined,
        confusion_matrix: rec.confusion_matrix as number[][] | undefined,
      };
    }
    return undefined;
  }, [analytics, publicMetrics]);

  const retrievalStats = analytics?.retrieval_statistics;

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-10">
      {/* ─── Page Header ─── */}
      <header className="space-y-2">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="brand" className="gap-1 py-0.5 px-2 text-xs font-medium">
              <Brain className="w-3 h-3" />
              Machine Learning Telemetry
            </Badge>
            <Badge variant="info" className="py-0.5 px-2 text-xs font-medium">
              Model Performance Benchmarks
            </Badge>
          </div>

          {/* Admin Session Actions */}
          <div className="flex items-center gap-2">
            {apiKey && !analyticsError ? (
              <div className="flex items-center gap-2">
                <Badge variant="success" className="gap-1 text-xs">
                  <KeyRound className="w-3 h-3" />
                  Authenticated
                </Badge>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleLogout}
                  icon={<LogOut className="w-3 h-3" />}
                  className="h-7 text-xs"
                >
                  Clear Key
                </Button>
              </div>
            ) : (
              <Button
                variant="primary"
                size="sm"
                onClick={() => setIsAuthDialogOpen(true)}
                icon={<Lock className="w-3 h-3" />}
                className="h-7 text-xs"
              >
                Authenticate Admin
              </Button>
            )}

            <Button
              variant="secondary"
              size="sm"
              onClick={() => {
                loadDiagnostics();
                if (apiKey) fetchAnalytics(apiKey);
              }}
              icon={<RefreshCw className="w-3 h-3" />}
              className="h-7 text-xs"
              title="Refresh all metrics"
            >
              Refresh
            </Button>
          </div>
        </div>

        <div>
          <h1 className="text-2xl md:text-3xl font-semibold tracking-tight text-text-primary">
            ML Analytics & Engine Performance
          </h1>
          <p className="mt-1 text-sm md:text-base text-text-secondary max-w-3xl leading-relaxed">
            Real-time diagnostics, repository statistics, multi-model evaluation benchmarks, and
            retrieval confidence metrics for the BIS-AI query intent classifier.
          </p>
        </div>
      </header>

      {/* ─── SECTION 1: System Health from Diagnostics (No Auth Needed) ─── */}
      <section className="space-y-3.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <Activity className="w-4 h-4 text-brand-600 dark:text-brand-400" />
            <h2 className="text-base font-semibold text-text-primary">
              System Health & Diagnostics
            </h2>
          </div>
          <span className="text-xs text-text-tertiary">
            Public Telemetry
          </span>
        </div>

        {diagLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {[1, 2, 3, 4].map((n) => (
              <div key={n} className="h-24 rounded-lg bg-bg-secondary animate-pulse border border-border-subtle" />
            ))}
          </div>
        ) : diagError || !diagnostics ? (
          <Card className="p-4 border-l-4 border-l-rose-500">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-rose-500 shrink-0" />
              <div>
                <h4 className="text-xs font-semibold text-text-primary">
                  Diagnostics Endpoint Unreachable
                </h4>
                <p className="text-xs text-text-secondary">
                  {diagError || 'Failed to retrieve diagnostics telemetry.'}
                </p>
              </div>
            </div>
          </Card>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {/* Core Service Status */}
            <Card className="p-4 space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-text-tertiary">
                  Core Service
                </span>
                <Badge
                  variant={diagnostics.status?.toLowerCase() === 'healthy' ? 'success' : 'warning'}
                  className="text-[10px]"
                >
                  {diagnostics.status || 'Active'}
                </Badge>
              </div>
              <div className="text-base font-semibold text-text-primary">
                BIS-AI Engine
              </div>
              <p className="text-xs text-text-secondary">
                Online & serving API requests
              </p>
            </Card>

            {/* Database Engine */}
            <Card className="p-4 space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-text-tertiary">
                  Database Store
                </span>
                <Badge
                  variant={diagnostics.database?.is_connected ? 'success' : 'default'}
                  className="text-[10px]"
                >
                  {diagnostics.database?.is_connected ? 'Connected' : 'Offline'}
                </Badge>
              </div>
              <div className="text-base font-semibold capitalize text-text-primary">
                {diagnostics.database?.mode || 'JSON Memory DB'}
              </div>
              <p className="text-xs text-text-secondary">
                {diagnostics.database?.standards_count || 0} standards loaded
              </p>
            </Card>

            {/* LLM Reasoning API */}
            <Card className="p-4 space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-text-tertiary">
                  LLM Intelligence
                </span>
                <Badge
                  variant={diagnostics.grok_api?.available ? 'success' : 'default'}
                  className="text-[10px]"
                >
                  {diagnostics.grok_api?.available ? 'Available' : 'Fallback Mode'}
                </Badge>
              </div>
              <div className="text-base font-semibold truncate text-text-primary">
                {diagnostics.grok_api?.model || 'Grok-2-Latest'}
              </div>
              <p className="text-xs text-text-secondary">
                {diagnostics.grok_api?.available ? 'AI inference operational' : 'Rule router fallback'}
              </p>
            </Card>

            {/* Knowledge Base Footprint */}
            <Card className="p-4 space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-text-tertiary">
                  Indexed Records
                </span>
                <Badge variant="brand" className="text-[10px]">Active Cache</Badge>
              </div>
              <div className="text-base font-semibold text-text-primary">
                {(diagnostics.database?.standards_count || 0) +
                  (diagnostics.database?.schemes_count || 0) +
                  (diagnostics.database?.laboratories_count || 0) +
                  (diagnostics.database?.faqs_count || 0)}
              </div>
              <p className="text-xs text-text-secondary">
                Across all core collections
              </p>
            </Card>
          </div>
        )}
      </section>

      {/* ─── SECTION 2: Admin Auth Gate Notification / Alert ─── */}
      {!apiKey && (
        <Card className="p-4 md:p-5 border-dashed border-border-default bg-bg-secondary flex flex-col sm:flex-row items-center justify-between gap-4 text-center sm:text-left">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-md bg-brand-500/10 text-brand-600 dark:text-brand-400 shrink-0">
              <Lock className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-text-primary">
                Administrative Audit Access (Optional)
              </h3>
              <p className="text-xs text-text-secondary mt-0.5">
                Model benchmarks and evaluation metrics are displayed below. Authenticate with an Admin API key to inspect query audit logs and internal retrieval telemetry.
              </p>
            </div>
          </div>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsAuthDialogOpen(true)}
            icon={<KeyRound className="w-3.5 h-3.5" />}
            className="shrink-0"
          >
            Enter Admin Key
          </Button>
        </Card>
      )}

      {/* Auth Error Display */}
      {apiKey && analyticsError && (
        <Card className="p-4 border-l-4 border-l-rose-500">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-rose-500 shrink-0" />
              <div>
                <h4 className="text-xs font-semibold text-text-primary">
                  Authentication Error
                </h4>
                <p className="text-xs text-text-secondary">
                  {analyticsError}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsAuthDialogOpen(true)}
              >
                Re-enter API Key
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleLogout}
              >
                Clear Key
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* ─── SECTION 3: Knowledge Counts ─── */}
      <section className="space-y-3.5">
        <div>
          <h2 className="text-base font-semibold text-text-primary">
            Knowledge Base Aggregates
          </h2>
          <p className="text-xs text-text-secondary">
            Current repository metrics across standards, schemes, laboratories, and consumer help
          </p>
        </div>

        {knowledgeCounts && (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            {/* Standards */}
            <Card className="p-3.5 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-text-tertiary">
                  Standards
                </span>
                <FileText className="w-3.5 h-3.5 text-brand-600 dark:text-brand-400" />
              </div>
              <div className="text-xl font-bold text-text-primary">
                {knowledgeCounts.total_standards?.toLocaleString() ?? 'N/A'}
              </div>
              <span className="text-[11px] text-text-secondary block truncate">
                Indian Standards indexed
              </span>
            </Card>

            {/* Schemes */}
            <Card className="p-3.5 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-text-tertiary">
                  Schemes
                </span>
                <Award className="w-3.5 h-3.5 text-brand-600 dark:text-brand-400" />
              </div>
              <div className="text-xl font-bold text-text-primary">
                {knowledgeCounts.total_certification_records?.toLocaleString() ?? 'N/A'}
              </div>
              <span className="text-[11px] text-text-secondary block truncate">
                Conformity schemes (ISI, CRS)
              </span>
            </Card>

            {/* Laboratories */}
            <Card className="p-3.5 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-text-tertiary">
                  Laboratories
                </span>
                <FlaskConical className="w-3.5 h-3.5 text-brand-600 dark:text-brand-400" />
              </div>
              <div className="text-xl font-bold text-text-primary">
                {knowledgeCounts.total_laboratory_records?.toLocaleString() ?? 'N/A'}
              </div>
              <span className="text-[11px] text-text-secondary block truncate">
                Testing laboratories
              </span>
            </Card>

            {/* Hallmarking */}
            <Card className="p-3.5 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-text-tertiary">
                  Hallmarking
                </span>
                <Gem className="w-3.5 h-3.5 text-brand-600 dark:text-brand-400" />
              </div>
              <div className="text-xl font-bold text-text-primary">
                {knowledgeCounts.total_hallmarking_records?.toLocaleString() ?? 'N/A'}
              </div>
              <span className="text-[11px] text-text-secondary block truncate">
                Karat purity rules
              </span>
            </Card>

            {/* FAQs */}
            <Card className="p-3.5 space-y-1 col-span-2 sm:col-span-1">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-text-tertiary">
                  FAQs & Help
                </span>
                <HelpCircle className="w-3.5 h-3.5 text-brand-600 dark:text-brand-400" />
              </div>
              <div className="text-xl font-bold text-text-primary">
                {knowledgeCounts.total_faqs?.toLocaleString() ?? 'N/A'}
              </div>
              <span className="text-[11px] text-text-secondary block truncate">
                Consumer Q&A articles
              </span>
            </Card>
          </div>
        )}
      </section>

      {/* ─── SECTION 4: ML Statistics Cards ─── */}
      <section className="space-y-3.5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-base font-semibold text-text-primary">
              ML Intent Classifier Telemetry
            </h2>
            <p className="text-xs text-text-secondary">
              Evaluation metrics on test dataset split (Ensemble Soft Voting Model)
            </p>
          </div>
          {mlStats?.best_model && (
            <Badge variant="brand" className="gap-1 text-[11px]">
              <Sparkles className="w-3 h-3" />
              Production: {mlStats.best_model}
            </Badge>
          )}
        </div>

        {mlStats && (
          <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {/* Accuracy */}
            <Card className="p-4 space-y-1">
              <span className="text-[10px] font-semibold uppercase tracking-wider block text-text-tertiary">
                Accuracy
              </span>
              <div className="text-2xl font-bold text-text-primary">
                {formatPercentDisplay(mlStats.accuracy)}
              </div>
              <p className="text-[11px] text-text-secondary">
                Intent classification success rate
              </p>
            </Card>

            {/* Precision */}
            <Card className="p-4 space-y-1">
              <span className="text-[10px] font-semibold uppercase tracking-wider block text-text-tertiary">
                Weighted Precision
              </span>
              <div className="text-2xl font-bold text-text-primary">
                {formatPercentDisplay(mlStats.precision)}
              </div>
              <p className="text-[11px] text-text-secondary">
                True positive ratio across classes
              </p>
            </Card>

            {/* Recall */}
            <Card className="p-4 space-y-1">
              <span className="text-[10px] font-semibold uppercase tracking-wider block text-text-tertiary">
                Weighted Recall
              </span>
              <div className="text-2xl font-bold text-text-primary">
                {formatPercentDisplay(mlStats.recall)}
              </div>
              <p className="text-[11px] text-text-secondary">
                Sensitivity across intent categories
              </p>
            </Card>

            {/* F1 Score */}
            <Card className="p-4 space-y-1">
              <span className="text-[10px] font-semibold uppercase tracking-wider block text-text-tertiary">
                Weighted F1 Score
              </span>
              <div className="text-2xl font-bold text-text-primary">
                {formatPercentDisplay(mlStats.f1 ?? (mlStats as Record<string, unknown>).f1_score as number | undefined)}
              </div>
              <p className="text-[11px] text-text-secondary">
                Harmonic mean of precision & recall
              </p>
            </Card>
          </div>
        )}

        {/* Training & Retrieval Secondary Info */}
        {mlStats && (
          <div className="p-3 rounded-lg border border-border-subtle bg-bg-secondary flex flex-wrap items-center justify-between gap-3 text-xs text-text-secondary">
            <div className="flex flex-wrap items-center gap-3">
              <span>Training Samples: <strong className="text-text-primary">{mlStats.training_samples ?? 'N/A'}</strong></span>
              <span>•</span>
              <span>Test Samples: <strong className="text-text-primary">{mlStats.test_samples ?? 'N/A'}</strong></span>
              {retrievalStats?.successful_retrievals !== undefined && (
                <>
                  <span>•</span>
                  <span>Successful Retrievals: <strong className="text-text-primary">{retrievalStats.successful_retrievals}</strong></span>
                </>
              )}
            </div>

            {retrievalStats?.low_confidence_queries !== undefined && (
              <div className="flex items-center gap-1.5 text-amber-600 dark:text-amber-400">
                <AlertCircle className="w-3.5 h-3.5" />
                <span>Low-Confidence Queries: <strong>{retrievalStats.low_confidence_queries}</strong></span>
              </div>
            )}
          </div>
        )}
      </section>

      {/* ─── SECTION 5: Bar Chart comparing model metrics ─── */}
      <section className="space-y-3.5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-text-primary">
              Model Benchmark Comparison
            </h2>
            <p className="text-xs text-text-secondary">
              Performance metrics across trained intent classification models
            </p>
          </div>

          {/* Metric Selector Tabs */}
          <div className="flex items-center gap-1 p-0.5 rounded-md border border-border-default bg-bg-secondary text-xs">
            {(['Accuracy', 'Precision', 'Recall', 'Weighted F1'] as const).map((metric) => (
              <button
                key={metric}
                type="button"
                onClick={() => setChartMetric(metric)}
                className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                  chartMetric === metric
                    ? 'bg-bg-primary text-text-primary shadow-xs'
                    : 'text-text-secondary hover:text-text-primary'
                }`}
              >
                {metric}
              </button>
            ))}
          </div>
        </div>

        <Card className="p-5 space-y-4">
          {analyticsLoading ? (
            <div className="h-64 flex items-center justify-center">
              <PageLoader />
            </div>
          ) : chartData.length === 0 ? (
            <div className="h-56 flex flex-col items-center justify-center text-center text-xs text-text-tertiary">
              <BarChart3 className="w-7 h-7 mb-2 opacity-50" />
              <span>Model benchmark data is loading or unavailable.</span>
            </div>
          ) : (
            <div className="w-full h-72 pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                  <XAxis
                    dataKey="name"
                    tick={{ fontSize: 11, fill: 'currentColor' }}
                    className="text-text-secondary"
                    tickLine={false}
                  />
                  <YAxis
                    domain={[0, 100]}
                    tick={{ fontSize: 11, fill: 'currentColor' }}
                    className="text-text-secondary"
                    tickLine={false}
                    unit="%"
                  />
                  <Tooltip
                    formatter={(val: unknown) => {
                      const num = typeof val === 'number' ? val : Number(val);
                      return [`${isNaN(num) ? '0' : num.toFixed(2)}%`, chartMetric];
                    }}
                    contentStyle={{
                      backgroundColor: 'var(--color-bg-primary)',
                      borderColor: 'var(--color-border-default)',
                      borderRadius: '6px',
                      color: 'var(--color-text-primary)',
                      fontSize: '12px',
                    }}
                  />
                  <Bar
                    dataKey={chartMetric}
                    fill="#2563EB"
                    radius={[4, 4, 0, 0]}
                    maxBarSize={48}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </Card>
      </section>

      {/* ─── SECTION 6: Model Comparison Table (All 4 Models) ─── */}
      <section className="space-y-3.5">
        <div>
          <h2 className="text-base font-semibold text-text-primary">
            Model Performance Comparison Matrix
          </h2>
          <p className="text-xs text-text-secondary">
            Full validation metrics comparing Random Forest, Extra Trees, Gradient Boosting, and
            the Voting Ensemble
          </p>
        </div>

        {modelComparisonList.length > 0 && (
          <div className="overflow-x-auto rounded-lg border border-border-default bg-bg-primary">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-border-subtle bg-bg-secondary text-[10px] uppercase tracking-wider font-semibold text-text-tertiary">
                  <th className="py-2.5 px-3.5">Model Architecture</th>
                  <th className="py-2.5 px-3.5">Accuracy</th>
                  <th className="py-2.5 px-3.5">Precision</th>
                  <th className="py-2.5 px-3.5">Recall</th>
                  <th className="py-2.5 px-3.5">Macro F1</th>
                  <th className="py-2.5 px-3.5">Weighted F1</th>
                  <th className="py-2.5 px-3.5">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle">
                {modelComparisonList.map((model, idx) => {
                  const isEnsemble =
                    model.Model.toLowerCase().includes('voting') ||
                    model.Model.toLowerCase().includes('ensemble');
                  return (
                    <tr
                      key={model.Model || idx}
                      className={`transition-colors ${
                        isEnsemble ? 'bg-brand-500/5' : 'hover:bg-bg-secondary/40'
                      }`}
                    >
                      <td className="py-2.5 px-3.5 font-semibold text-text-primary">
                        <div className="flex items-center gap-1.5">
                          <Cpu className="w-3.5 h-3.5 text-brand-600 dark:text-brand-400 shrink-0" />
                          <span>{model.Model}</span>
                        </div>
                      </td>
                      <td className="py-2.5 px-3.5 font-mono font-medium text-text-primary">
                        {model.Accuracy || 'N/A'}
                      </td>
                      <td className="py-2.5 px-3.5 font-mono text-text-secondary">
                        {model.Precision || 'N/A'}
                      </td>
                      <td className="py-2.5 px-3.5 font-mono text-text-secondary">
                        {model.Recall || 'N/A'}
                      </td>
                      <td className="py-2.5 px-3.5 font-mono text-text-secondary">
                        {model['Macro F1'] || 'N/A'}
                      </td>
                      <td className="py-2.5 px-3.5 font-mono font-semibold text-brand-600 dark:text-brand-400">
                        {model['Weighted F1'] || 'N/A'}
                      </td>
                      <td className="py-2.5 px-3.5">
                        {isEnsemble ? (
                          <Badge variant="brand" className="text-[10px]">Production Active</Badge>
                        ) : (
                          <Badge variant="default" className="text-[10px]">Candidate Model</Badge>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* ─── Admin Key Prompt Dialog ─── */}
      <Dialog
        open={isAuthDialogOpen}
        onClose={() => setIsAuthDialogOpen(false)}
        title="Admin API Key Authentication"
      >
        <form onSubmit={handleKeySubmit} className="space-y-4">
          <p className="text-xs text-text-secondary leading-relaxed">
            Administrative endpoints are protected under the BIS-AI security protocol. Please enter
            your secret <code>X-Admin-API-Key</code>. This credential is stored in session memory only
            and is never written to disk.
          </p>

          <div className="space-y-1.5">
            <label
              htmlFor="admin-key-input"
              className="text-[11px] font-semibold uppercase tracking-wider block text-text-tertiary"
            >
              Administrator API Key
            </label>
            <Input
              id="admin-key-input"
              type="password"
              placeholder="e.g. bis-admin-secret-key-2024"
              value={keyInput}
              onChange={(e) => {
                setKeyInput(e.target.value);
                setAuthError(null);
              }}
              autoFocus
            />
          </div>

          {authError && (
            <div className="p-2.5 rounded border border-rose-500/20 bg-rose-500/10 text-xs text-rose-600 dark:text-rose-400 flex items-center gap-2">
              <AlertCircle className="w-3.5 h-3.5 shrink-0" />
              <span>{authError}</span>
            </div>
          )}

          <div className="flex items-center justify-end gap-2 pt-2">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setIsAuthDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              loading={analyticsLoading}
              disabled={!keyInput.trim()}
              icon={<KeyRound className="w-3.5 h-3.5" />}
            >
              Authenticate & Load
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
