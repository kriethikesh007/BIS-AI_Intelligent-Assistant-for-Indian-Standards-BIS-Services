/** API service functions for all Flask endpoints. */
import apiClient from './client';
import type {
  ApiResponse,
  ChatRequest,
  ChatResponseData,
  StandardsListResponse,
  CertificationResponse,
  HallmarkingResponse,
  LaboratoriesResponse,
  ConsumerResponse,
  DiagnosticsData,
  AdminAnalyticsData,
  RecommendResponse,
  PredictIntentResponse,
  Standard,
  IngestResponse,
  RetrainResponse,
} from '../../types/api';

/* ─── Chat ─── */
export async function sendChatMessage(
  query: string,
  options?: {
    preferred_language?: string;
    history?: { role: string; content: string }[];
    signal?: AbortSignal;
  }
): Promise<ChatResponseData> {
  const body: ChatRequest = {
    query,
    preferred_language: options?.preferred_language,
    history: options?.history as ChatRequest['history'],
  };
  const res = await apiClient.post<ApiResponse<ChatResponseData>>(
    '/api/chat',
    body,
    { signal: options?.signal }
  );
  if (res.status === 'error' || !res.data) {
    throw new Error(res.error || 'Failed to get response');
  }
  return res.data;
}

/* ─── Standards ─── */
export async function getStandards(category?: string): Promise<StandardsListResponse> {
  const params = category ? `?category=${encodeURIComponent(category)}` : '';
  const res = await apiClient.get<ApiResponse<StandardsListResponse>>(`/api/standards${params}`);
  return res.data!;
}

export async function getStandardById(id: string): Promise<Standard> {
  const res = await apiClient.get<ApiResponse<Standard>>(`/api/standards/${encodeURIComponent(id)}`);
  return res.data!;
}

/* ─── Recommendations ─── */
export async function getRecommendations(
  productDescription: string,
  signal?: AbortSignal
): Promise<RecommendResponse> {
  const res = await apiClient.post<RecommendResponse>(
    '/api/recommend',
    { product_description: productDescription },
    { signal }
  );
  return res;
}

/* ─── Intent Classification ─── */
export async function predictIntent(query: string): Promise<PredictIntentResponse> {
  const res = await apiClient.post<ApiResponse<PredictIntentResponse>>(
    '/api/predict-intent',
    { query }
  );
  return res.data!;
}

/* ─── Certification ─── */
export async function getCertificationSchemes(): Promise<CertificationResponse> {
  const res = await apiClient.get<ApiResponse<CertificationResponse>>('/api/certification');
  return res.data!;
}

/* ─── Hallmarking ─── */
export async function getHallmarkingData(): Promise<HallmarkingResponse> {
  const res = await apiClient.get<ApiResponse<HallmarkingResponse>>('/api/hallmarking');
  return res.data!;
}

/* ─── Laboratories ─── */
export async function getLaboratories(filters?: {
  state?: string;
  city?: string;
}): Promise<LaboratoriesResponse> {
  const params = new URLSearchParams();
  if (filters?.state) params.set('state', filters.state);
  if (filters?.city) params.set('city', filters.city);
  const qs = params.toString() ? `?${params.toString()}` : '';
  const res = await apiClient.get<ApiResponse<LaboratoriesResponse>>(`/api/laboratories${qs}`);
  return res.data!;
}

/* ─── Consumer ─── */
export async function getConsumerData(): Promise<ConsumerResponse> {
  const res = await apiClient.get<ApiResponse<ConsumerResponse>>('/api/consumer');
  return res.data!;
}

/* ─── Diagnostics ─── */
export async function getDiagnostics(): Promise<DiagnosticsData> {
  const res = await apiClient.get<ApiResponse<DiagnosticsData>>('/api/diagnostics');
  return res.data!;
}

/* ─── Public ML Metrics ─── */
export interface PublicMetricsResponse {
  status: string;
  metrics: {
    machine_learning_metrics?: {
      accuracy?: number;
      precision_weighted?: number;
      recall_weighted?: number;
      f1_weighted?: number;
      confusion_matrix?: number[][];
      classes?: string[];
      [key: string]: unknown;
    };
    [key: string]: unknown;
  };
  data: {
    comparison_table?: import('../../types/api').ModelComparison[];
    models?: Record<string, unknown>;
    classes?: string[];
    [key: string]: unknown;
  };
  database_status: Record<string, unknown>;
}

export async function getPublicMetrics(): Promise<PublicMetricsResponse> {
  const res = await apiClient.get<PublicMetricsResponse>('/api/metrics');
  return res;
}

/* ─── Admin (requires X-Admin-API-Key header) ─── */
export async function getAdminAnalytics(apiKey: string): Promise<AdminAnalyticsData> {
  const res = await apiClient.get<ApiResponse<AdminAnalyticsData>>(
    '/api/admin/analytics',
    { headers: { 'X-Admin-API-Key': apiKey } }
  );
  if (res.status === 'error' || !res.data) {
    throw new Error(res.error || 'Failed to fetch admin analytics');
  }
  return res.data;
}

export async function adminIngestData(apiKey: string): Promise<IngestResponse> {
  const res = await apiClient.post<ApiResponse<IngestResponse>>(
    '/api/admin/ingest',
    {},
    { headers: { 'X-Admin-API-Key': apiKey } }
  );
  return res.data!;
}

export async function adminRetrain(apiKey: string): Promise<RetrainResponse> {
  const res = await apiClient.post<ApiResponse<RetrainResponse>>(
    '/api/admin/retrain',
    {},
    { headers: { 'X-Admin-API-Key': apiKey } }
  );
  return res.data!;
}

export async function getAdminAnalyticsWithKey(apiKey: string): Promise<AdminAnalyticsData> {
  return getAdminAnalytics(apiKey);
}
