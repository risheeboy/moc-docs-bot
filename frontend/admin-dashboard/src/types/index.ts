// Pagination
export interface PaginatedResponse<T> {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  items: T[];
}

// Auth
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: {
    user_id: string;
    username: string;
    email: string;
    role: 'admin' | 'editor' | 'viewer';
    created_at: string;
  };
}

export interface AuthState {
  user: LoginResponse['user'] | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

// Dashboard KPIs
export interface DashboardMetrics {
  query_volume_today: number;
  query_volume_change_percent: number;
  avg_response_time_ms: number;
  response_time_change_percent: number;
  active_sessions: number;
  sessions_change_percent: number;
  user_satisfaction_score: number;
  satisfaction_change_percent: number;
  timestamp: string;
}

// Analytics
export interface LanguageDistribution {
  language: string;
  query_count: number;
  percentage: number;
}

export interface TopicDistribution {
  topic: string;
  query_count: number;
  percentage: number;
}

export interface ModelUsageMetric {
  model_name: string;
  usage_count: number;
  avg_latency_ms: number;
  cost_usd: number;
}

export interface SatisfactionTrend {
  date: string;
  avg_score: number;
  sample_count: number;
}

export interface AnalyticsData {
  language_distribution: LanguageDistribution[];
  topic_distribution: TopicDistribution[];
  model_usage: ModelUsageMetric[];
  satisfaction_trends: SatisfactionTrend[];
  period: string;
}

// Document Management
export interface Document {
  document_id: string;
  title: string;
  source_url: string;
  source_site: string;
  content_type: string;
  language: string;
  file_size_bytes: number;
  uploaded_at: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  chunk_count: number;
  error_message?: string;
}

export interface DocumentListResponse extends PaginatedResponse<Document> {}

export interface DocumentUploadResponse {
  document_id: string;
  title: string;
  status: string;
  message: string;
}

// Scrape Jobs
export interface ScrapeJob {
  job_id: string;
  status: 'started' | 'running' | 'completed' | 'failed';
  target_urls: string[];
  progress: {
    pages_crawled: number;
    pages_total: number;
    documents_ingested: number;
    errors: number;
  };
  started_at: string;
  completed_at?: string;
  elapsed_seconds: number;
  error_message?: string;
}

export interface ScrapeJobTriggerRequest {
  target_urls: string[];
  spider_type: string;
  force_rescrape: boolean;
}

export interface ScrapeJobTriggerResponse {
  job_id: string;
  status: string;
  target_count: number;
  started_at: string;
}

// Conversations
export interface Conversation {
  session_id: string;
  user_id: string;
  language: string;
  query_count: number;
  created_at: string;
  last_interaction_at: string;
  satisfaction_score?: number;
  satisfaction_feedback?: string;
}

export interface ConversationDetail extends Conversation {
  turns: ConversationTurn[];
}

export interface ConversationTurn {
  turn_id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

export interface ConversationListResponse extends PaginatedResponse<Conversation> {}

// Feedback
export interface Feedback {
  feedback_id: string;
  session_id: string;
  user_id: string;
  rating: number;
  sentiment: 'positive' | 'negative' | 'neutral';
  comment?: string;
  created_at: string;
  language: string;
}

export interface FeedbackListResponse extends PaginatedResponse<Feedback> {}

export interface FeedbackSentimentSummary {
  period: string;
  total_feedback: number;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  avg_rating: number;
}

// System Configuration
export interface SystemConfig {
  rag_confidence_threshold: number;
  rag_top_k: number;
  rag_rerank_top_k: number;
  rag_cache_ttl_seconds: number;
  session_idle_timeout_seconds: number;
  session_max_turns: number;
  llm_temperature: number;
  llm_max_tokens: number;
  enable_voice_input: boolean;
  enable_translation: boolean;
  enable_ocr: boolean;
  enable_sentiment_analysis: boolean;
}

export interface SystemConfigUpdateRequest {
  config: Partial<SystemConfig>;
}

export interface SystemConfigResponse {
  config: SystemConfig;
  updated_at: string;
  updated_by: string;
}

// Model Monitoring (Langfuse)
export interface ModelMetric {
  model_name: string;
  total_requests: number;
  avg_latency_ms: number;
  total_tokens_generated: number;
  total_cost_usd: number;
  error_rate: number;
  success_rate: number;
}

export interface ModelMonitoringData {
  metrics: ModelMetric[];
  period: string;
  timestamp: string;
}

// Audit Log
export interface AuditLogEntry {
  log_id: string;
  user_id: string;
  username: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  details: Record<string, unknown>;
  status: 'success' | 'failure';
  ip_address: string;
  timestamp: string;
}

export interface AuditLogListResponse extends PaginatedResponse<AuditLogEntry> {}

// Error Response
export interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
    request_id?: string;
  };
}

// API Response wrapper
export interface ApiResponse<T> {
  data?: T;
  error?: ErrorResponse['error'];
}
