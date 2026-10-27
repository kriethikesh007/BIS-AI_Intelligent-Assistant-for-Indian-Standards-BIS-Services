/* ─── API Response Types ─── */

/** Generic wrapper returned by most endpoints */
export interface ApiResponse<T = unknown> {
  status: 'success' | 'error';
  data?: T;
  error?: string;
  details?: string;
}

/** Legacy-style response (some endpoints use direct jsonify) */
export interface LegacyApiResponse<T = unknown> {
  status: 'success' | 'error';
  data?: T;
  error?: string;
  detail?: string;
}

/* ─── Chat ─── */
export interface ChatRequest {
  query: string;
  preferred_language?: string;
  language?: string;
  history?: ChatHistoryItem[];
  conversation_history?: ChatHistoryItem[];
}

export interface ChatHistoryItem {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatResponseData {
  answer: string;
  recommended_standard?: string | null;
  relevant_standard?: string | null;
  source?: string | null;
  source_url?: string | null;
  source_title?: string | null;
  mandatory_status_source?: string | null;
  supporting_excerpt?: string | null;
  edition_or_year?: string | null;
  verification_level?: string | null;
  reference?: string | null;
  reference_document?: string | null;
  reason?: string | null;
  why?: string | null;
  confidence?: string | null;
  confidence_score?: number | null;
  retrieval_relevance?: number | null;
  classifier_confidence?: number | null;
  detected_intent?: string | null;
  intent?: string | null;
  router_intent?: string | null;
  detected_language?: string | null;
  answer_language?: string | null;
  original_query?: string | null;
  processed_query?: string | null;
  match_type?: string | null;
  verification_status?: string | null;
  clause_verification?: string | null;
  page_section_clause?: string | null;
  llm_model?: string | null;
  ai_generated?: boolean;
  retrieval_scores?: Record<string, number> | null;
}

/* ─── Standards ─── */
export interface Standard {
  id?: string;
  standard_code: string;
  standard_number?: string;
  title: string;
  category?: string;
  product?: string;
  scope?: string;
  applicable_products?: string[];
  product_categories?: string[];
  certification_scheme?: string;
  compliance_status?: string;
  mandatory_status?: string;
  mandatory_status_source?: string;
  testing_parameters?: string;
  page_section_clause?: string;
  reference_document?: string;
  source?: string;
  source_url?: string;
  source_title?: string;
  supporting_excerpt?: string;
  verification_status?: string;
  verified_at?: string;
  last_checked_at?: string;
  effective_date?: string;
  superseded_by?: string | null;
  language?: string;
  metadata?: Record<string, unknown>;
  relevance_score?: number;
}

export interface StandardsListResponse {
  total: number;
  standards: Standard[];
}

/* ─── Recommendation ─── */
export interface RecommendRequest {
  product_description: string;
}

export interface RecommendResponse {
  status: string;
  product_description: string;
  extracted_analysis: Record<string, unknown>;
  count: number;
  recommendations: Standard[];
}

/* ─── Intent ─── */
export interface PredictIntentRequest {
  query: string;
}

export interface PredictIntentResponse {
  intent: string;
  confidence: number;
  model?: string;
  all_probabilities?: Record<string, number>;
}

/* ─── Certification ─── */
export interface CertificationScheme {
  id?: string;
  scheme_name?: string;
  name?: string;
  description?: string;
  applicable_to?: string;
  eligibility?: string;
  process?: string;
  fees?: string;
  reference?: string;
  source?: string;
  [key: string]: unknown;
}

export interface CertificationResponse {
  total: number;
  schemes: CertificationScheme[];
}

/* ─── Hallmarking ─── */
export interface HallmarkingResponse {
  standards: Standard[];
  guidelines_and_faqs: FAQ[];
  key_requirements: string[];
}

/* ─── Laboratory ─── */
export interface Laboratory {
  id?: string;
  name?: string;
  lab_name?: string;
  type?: string;
  city?: string;
  state?: string;
  address?: string;
  contact?: string;
  phone?: string;
  email?: string;
  website?: string;
  disciplines?: string[];
  accreditation?: string;
  [key: string]: unknown;
}

export interface LaboratoriesResponse {
  total: number;
  laboratories: Laboratory[];
}

/* ─── FAQ ─── */
export interface FAQ {
  id?: string;
  question?: string;
  answer?: string;
  topic?: string;
  category?: string;
  source?: string;
  [key: string]: unknown;
}

/* ─── Consumer ─── */
export interface ConsumerResponse {
  faqs?: FAQ[];
  consumer_resources?: FAQ[];
  resources?: Record<string, unknown>[];
  total?: number;
  total_faqs?: number;
  verification_tools?: {
    mobile_app?: string;
    web_portal?: string;
    standards_portal?: string;
    [key: string]: unknown;
  };
}

/* ─── Diagnostics ─── */
export interface DiagnosticsData {
  status: string;
  grok_api: {
    available: boolean;
    model?: string;
    base_url?: string;
    [key: string]: unknown;
  };
  database: {
    mode: string;
    is_connected: boolean;
    standards_count: number;
    schemes_count: number;
    laboratories_count: number;
    faqs_count: number;
    [key: string]: unknown;
  };
}

/* ─── Admin Analytics ─── */
export interface AdminAnalyticsData {
  knowledge_counts: {
    total_standards: number;
    total_certification_records: number;
    total_laboratory_records: number;
    total_hallmarking_records: number;
    total_faqs: number;
  };
  ml_statistics: {
    training_samples?: number;
    test_samples?: number;
    accuracy?: number;
    precision?: number;
    recall?: number;
    f1?: number;
    f1_score?: number;
    best_model?: string;
    ensemble_performance?: ModelComparison[];
    [key: string]: unknown;
  };
  model_comparison?: ModelComparison[];
  model_benchmarks?: ModelComparison[];
  retrieval_statistics?: {
    total_queries?: number;
    queries?: number;
    total_queries_logged?: number;
    successful_retrievals?: number;
    low_confidence_queries?: number;
    top_categories?: string[];
    top_requested_categories?: { category: string; count: number }[];
    intent_distribution?: Record<string, number>;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

export interface ModelComparison {
  Model: string;
  Accuracy: string;
  Precision: string;
  Recall: string;
  'Macro F1': string;
  'Weighted F1': string;
}

/* ─── Search / Catalog ─── */
export interface SearchStandardsParams {
  category?: string;
  query?: string;
}

/* ─── Admin Ingest ─── */
export interface IngestResponse {
  message: string;
  total_ingested: number;
}

export interface RetrainResponse {
  message: string;
  metrics?: Record<string, unknown>;
}
