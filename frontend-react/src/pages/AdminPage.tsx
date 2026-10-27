import { useState, useEffect } from 'react';
import {
  Shield,
  Database,
  RefreshCw,
  Plus,
  Trash2,
  AlertTriangle,
  CheckCircle2,
  Lock,
  Server,
  Brain,
  BookOpen,
} from 'lucide-react';
import { Button, Card, Badge, Input, Dialog, Skeleton, EmptyState } from '../components/ui';
import { getDiagnostics, getStandards } from '../services/api/endpoints';
import apiClient from '../services/api/client';
import type { DiagnosticsData, Standard } from '../types/api';

export default function AdminPage() {
  const [apiKey, setApiKey] = useState(() => {
    return sessionStorage.getItem('bis_admin_api_key') || '';
  });
  const [authenticated, setAuthenticated] = useState(() => {
    return Boolean(sessionStorage.getItem('bis_admin_api_key'));
  });
  const [keyInput, setKeyInput] = useState('');
  const [diagnostics, setDiagnostics] = useState<DiagnosticsData | null>(null);
  const [diagLoading, setDiagLoading] = useState(true);
  const [standards, setStandards] = useState<Standard[]>([]);
  const [stdLoading, setStdLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [actionResult, setActionResult] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [addForm, setAddForm] = useState({
    title: '',
    standard_code: '',
    category: '',
    product: '',
    certification_scheme: '',
    mandatory_status: 'Mandatory',
    source_url: '',
  });

  // Load diagnostics (no auth needed)
  useEffect(() => {
    getDiagnostics()
      .then(setDiagnostics)
      .catch(() => {})
      .finally(() => setDiagLoading(false));
  }, []);

  const loadStandards = async () => {
    setStdLoading(true);
    try {
      const data = await getStandards();
      setStandards(data.standards || []);
    } catch {
      /* ignore */
    }
    setStdLoading(false);
  };

  useEffect(() => {
    if (authenticated) {
      loadStandards();
    }
  }, [authenticated]);

  const authenticate = () => {
    const trimmed = keyInput.trim();
    if (trimmed) {
      setApiKey(trimmed);
      sessionStorage.setItem('bis_admin_api_key', trimmed);
      setAuthenticated(true);
    }
  };

  const handleAction = async (
    action: string,
    endpoint: string,
    method: 'POST' | 'GET' | 'DELETE' = 'POST',
    body?: unknown
  ) => {
    setActionLoading(action);
    setActionResult(null);
    try {
      const res = await (method === 'POST'
        ? apiClient.post<{ status: string; message?: string; data?: unknown }>(endpoint, body || {}, {
            headers: { 'X-Admin-API-Key': apiKey },
          })
        : method === 'DELETE'
        ? apiClient.delete<{ status: string; message?: string; data?: unknown }>(endpoint, {
            headers: { 'X-Admin-API-Key': apiKey },
          })
        : apiClient.get<{ status: string; data?: unknown }>(endpoint, {
            headers: { 'X-Admin-API-Key': apiKey },
          }));
      setActionResult({
        type: 'success',
        message: (res as { message?: string }).message || `${action} completed successfully`,
      });
      if (
        action === 'Rebuild Index' ||
        action === 'Retrain' ||
        action === 'Add Record' ||
        action === 'Delete' ||
        action === 'Ingest Catalog'
      ) {
        await loadStandards();
      }
    } catch (err) {
      setActionResult({
        type: 'error',
        message: err instanceof Error ? err.message : 'Action failed',
      });
    }
    setActionLoading(null);
  };

  const handleAddRecord = () => {
    handleAction('Add Record', '/api/admin/knowledge', 'POST', {
      collection: 'standards',
      standard_code: addForm.standard_code,
      standard_number: addForm.standard_code,
      title: addForm.title,
      category: addForm.category,
      product: addForm.product,
      certification_scheme: addForm.certification_scheme,
      mandatory_status: addForm.mandatory_status,
      source_url: addForm.source_url,
    });
    setShowAddForm(false);
    setAddForm({
      title: '',
      standard_code: '',
      category: '',
      product: '',
      certification_scheme: '',
      mandatory_status: 'Mandatory',
      source_url: '',
    });
  };

  const handleDeleteRecord = async (id: string) => {
    if (!confirm('Are you sure you want to delete this record?')) return;
    handleAction('Delete', `/api/admin/knowledge/${encodeURIComponent(id)}?collection=standards`, 'DELETE');
  };

  // Auth gate
  if (!authenticated) {
    return (
      <div className="flex items-center justify-center min-h-[70vh] p-4">
        <Card className="max-w-md w-full p-6 sm:p-8 space-y-6 border border-border-default shadow-md bg-bg-secondary">
          <div className="flex flex-col items-center text-center space-y-2.5">
            <div className="w-12 h-12 rounded-xl bg-brand-500/10 border border-brand-500/20 text-brand-600 dark:text-brand-400 flex items-center justify-center">
              <Lock size={22} />
            </div>
            <h2 className="text-xl font-bold text-text-primary">
              Admin Console Authentication
            </h2>
            <p className="text-xs text-text-secondary max-w-xs leading-relaxed">
              Enter your authorized BIS-AI administrator API key to access live operations, model retraining, and knowledge base management.
            </p>
          </div>
          <div className="space-y-3.5">
            <Input
              type="password"
              placeholder="Enter Admin API Key..."
              value={keyInput}
              onChange={(e) => setKeyInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && authenticate()}
              className="bg-bg-primary"
            />
            <Button
              className="w-full"
              variant="primary"
              onClick={authenticate}
              disabled={!keyInput.trim()}
              icon={<Shield size={15} />}
            >
              Authenticate Session
            </Button>
            <p className="text-[11px] text-center text-text-tertiary">
              Configured via <code className="px-1 py-0.5 rounded bg-bg-tertiary text-text-secondary font-mono">ADMIN_API_KEY</code> environment variable
            </p>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Badge variant="brand" className="px-2 py-0.5 text-xs font-medium">
              <Shield size={11} className="mr-1 inline" />
              Operations Console
            </Badge>
            <Badge variant="success" className="px-2 py-0.5 text-xs font-medium">
              Authenticated
            </Badge>
          </div>
          <h1 className="text-2xl font-semibold tracking-tight text-text-primary">
            Admin Operations & Management
          </h1>
          <p className="text-xs text-text-secondary">
            Manage repository entries, model retraining, and vector search indices
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            sessionStorage.removeItem('bis_admin_api_key');
            setApiKey('');
            setAuthenticated(false);
          }}
          className="text-xs"
        >
          Sign Out
        </Button>
      </div>

      {/* Action Result Notification */}
      {actionResult && (
        <div
          className={`flex items-center gap-2.5 p-3 rounded-md text-xs border ${
            actionResult.type === 'success'
              ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20'
              : 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20'
          }`}
        >
          {actionResult.type === 'success' ? (
            <CheckCircle2 size={15} className="shrink-0" />
          ) : (
            <AlertTriangle size={15} className="shrink-0" />
          )}
          <span>{actionResult.message}</span>
        </div>
      )}

      {/* System Status */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <Card className="p-4 space-y-1.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-text-tertiary">
              <Server size={14} className="text-brand-600 dark:text-brand-400" />
              <span className="text-[10px] font-semibold uppercase tracking-wider">Service Health</span>
            </div>
            {diagLoading ? (
              <Skeleton className="h-4 w-16" />
            ) : (
              <Badge variant={diagnostics?.status === 'healthy' || diagnostics?.status === 'online' ? 'success' : 'default'} className="text-[10px]">
                {diagnostics?.status || 'Active'}
              </Badge>
            )}
          </div>
          <div className="text-sm font-semibold text-text-primary">
            Flask Backend Core
          </div>
          <p className="text-[11px] text-text-secondary">
            Port 5000 REST API
          </p>
        </Card>

        <Card className="p-4 space-y-1.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-text-tertiary">
              <Database size={14} className="text-brand-600 dark:text-brand-400" />
              <span className="text-[10px] font-semibold uppercase tracking-wider">Knowledge DB</span>
            </div>
            <Badge variant="brand" className="text-[10px]">
              {diagnostics?.database?.mode || 'Active'}
            </Badge>
          </div>
          <div className="text-sm font-semibold text-text-primary">
            {diagnostics?.database?.standards_count || 0} Standards
          </div>
          <p className="text-[11px] text-text-secondary">
            Indexed and queryable
          </p>
        </Card>

        <Card className="p-4 space-y-1.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-text-tertiary">
              <Brain size={14} className="text-brand-600 dark:text-brand-400" />
              <span className="text-[10px] font-semibold uppercase tracking-wider">AI Service</span>
            </div>
            <Badge variant={diagnostics?.grok_api?.available ? 'success' : 'default'} className="text-[10px]">
              {diagnostics?.grok_api?.available ? 'Online' : 'Fallback'}
            </Badge>
          </div>
          <div className="text-sm font-semibold text-text-primary truncate">
            {diagnostics?.grok_api?.model || 'Grok-2-Latest'}
          </div>
          <p className="text-[11px] text-text-secondary">
            Generative synthesis
          </p>
        </Card>
      </div>

      {/* Admin Actions */}
      <Card className="p-4 md:p-5 space-y-3">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-text-tertiary">
          Administrative Operations
        </h3>
        <div className="flex flex-wrap gap-2.5">
          <Button
            variant="secondary"
            size="sm"
            icon={<RefreshCw size={13} />}
            loading={actionLoading === 'Rebuild Index'}
            onClick={() => handleAction('Rebuild Index', '/api/admin/rebuild-index')}
          >
            Rebuild Search Index
          </Button>
          <Button
            variant="secondary"
            size="sm"
            icon={<Database size={13} />}
            loading={actionLoading === 'Ingest Catalog'}
            onClick={() => handleAction('Ingest Catalog', '/api/admin/ingest')}
          >
            Ingest Knowledge Base
          </Button>
          <Button
            variant="secondary"
            size="sm"
            icon={<Brain size={13} />}
            loading={actionLoading === 'Retrain'}
            onClick={() => {
              if (confirm('This will retrain all ML models on latest dataset. Continue?')) {
                handleAction('Retrain', '/api/admin/retrain');
              }
            }}
          >
            Retrain ML Models
          </Button>
          <Button
            variant="primary"
            size="sm"
            icon={<Plus size={13} />}
            onClick={() => setShowAddForm(true)}
          >
            Add New Standard
          </Button>
        </div>
      </Card>

      {/* Standards Management */}
      <Card padding="none" className="overflow-hidden">
        <div className="flex items-center justify-between p-3.5 border-b border-border-subtle bg-bg-secondary">
          <div className="flex items-center gap-2">
            <BookOpen size={15} className="text-brand-600 dark:text-brand-400" />
            <h3 className="text-xs font-semibold uppercase tracking-wider text-text-primary">
              Standards Catalog Records ({standards.length})
            </h3>
          </div>
          <Button
            variant="ghost"
            size="sm"
            icon={<RefreshCw size={12} />}
            onClick={() => loadStandards()}
            loading={stdLoading}
            className="h-7 text-xs px-2"
          >
            Refresh
          </Button>
        </div>

        {stdLoading ? (
          <div className="p-4 space-y-2">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : standards.length === 0 ? (
          <div className="p-6">
            <EmptyState
              title="No standards loaded"
              description="Standards data is not currently loaded in the admin session."
            />
          </div>
        ) : (
          <div className="divide-y divide-border-subtle">
            {standards.slice(0, 20).map((std, i) => (
              <div
                key={std.id || i}
                className="flex items-center justify-between p-3 hover:bg-bg-secondary/40 transition-colors text-xs"
              >
                <div className="min-w-0 flex-1 pr-4">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-text-primary">
                      {std.standard_code}
                    </span>
                    <Badge
                      variant={
                        std.mandatory_status?.toLowerCase().includes('mandatory')
                          ? 'warning'
                          : 'default'
                      }
                      className="text-[10px]"
                    >
                      {std.mandatory_status || 'N/A'}
                    </Badge>
                  </div>
                  <p className="text-text-secondary truncate mt-0.5">
                    {std.title}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  icon={<Trash2 size={13} />}
                  onClick={() => std.id && handleDeleteRecord(std.id)}
                  className="text-rose-500 hover:text-rose-600 hover:bg-rose-500/10 h-7 w-7 p-0 shrink-0"
                  title="Delete record"
                />
              </div>
            ))}
            {standards.length > 20 && (
              <div className="p-3 text-center text-xs text-text-tertiary bg-bg-secondary/20">
                Showing first 20 of {standards.length} records
              </div>
            )}
          </div>
        )}
      </Card>

      {/* Add Record Dialog */}
      <Dialog
        open={showAddForm}
        onClose={() => setShowAddForm(false)}
        title="Add New Standard Record"
      >
        <div className="space-y-3 pt-1 text-xs">
          <div>
            <label className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary block mb-1">
              Standard Code *
            </label>
            <Input
              placeholder="e.g. IS 1234:2024"
              value={addForm.standard_code}
              onChange={(e) => setAddForm((p) => ({ ...p, standard_code: e.target.value }))}
            />
          </div>

          <div>
            <label className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary block mb-1">
              Title *
            </label>
            <Input
              placeholder="e.g. Specification for Electric Vehicles Safety"
              value={addForm.title}
              onChange={(e) => setAddForm((p) => ({ ...p, title: e.target.value }))}
            />
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary block mb-1">
                Category
              </label>
              <Input
                placeholder="e.g. Automotive"
                value={addForm.category}
                onChange={(e) => setAddForm((p) => ({ ...p, category: e.target.value }))}
              />
            </div>
            <div>
              <label className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary block mb-1">
                Product
              </label>
              <Input
                placeholder="e.g. Electric Scooter"
                value={addForm.product}
                onChange={(e) => setAddForm((p) => ({ ...p, product: e.target.value }))}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary block mb-1">
                Certification Scheme
              </label>
              <Input
                placeholder="e.g. Scheme I (ISI Mark)"
                value={addForm.certification_scheme}
                onChange={(e) => setAddForm((p) => ({ ...p, certification_scheme: e.target.value }))}
              />
            </div>
            <div>
              <label className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary block mb-1">
                Status
              </label>
              <select
                value={addForm.mandatory_status}
                onChange={(e) => setAddForm((p) => ({ ...p, mandatory_status: e.target.value }))}
                className="w-full h-9 px-3 rounded-md border border-border-default bg-bg-primary text-text-primary text-xs outline-none"
              >
                <option value="Mandatory">Mandatory</option>
                <option value="Voluntary">Voluntary</option>
              </select>
            </div>
          </div>

          <div>
            <label className="text-[11px] font-semibold uppercase tracking-wider text-text-tertiary block mb-1">
              Source URL
            </label>
            <Input
              placeholder="e.g. https://www.services.bis.gov.in/..."
              value={addForm.source_url}
              onChange={(e) => setAddForm((p) => ({ ...p, source_url: e.target.value }))}
            />
          </div>
        </div>

        <div className="mt-4 flex justify-end gap-2 pt-2 border-t border-border-subtle">
          <Button variant="secondary" size="sm" onClick={() => setShowAddForm(false)}>
            Cancel
          </Button>
          <Button
            size="sm"
            onClick={handleAddRecord}
            disabled={!addForm.standard_code || !addForm.title}
          >
            Add Record
          </Button>
        </div>
      </Dialog>
    </div>
  );
}
