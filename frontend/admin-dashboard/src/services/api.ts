import axios, { AxiosInstance, AxiosError } from 'axios';
import {
  LoginRequest,
  LoginResponse,
  DashboardMetrics,
  AnalyticsData,
  DocumentListResponse,
  DocumentUploadResponse,
  ScrapeJob,
  ScrapeJobTriggerRequest,
  ScrapeJobTriggerResponse,
  ConversationListResponse,
  ConversationDetail,
  FeedbackListResponse,
  FeedbackSentimentSummary,
  SystemConfig,
  SystemConfigUpdateRequest,
  SystemConfigResponse,
  ModelMonitoringData,
  AuditLogListResponse,
  ErrorResponse,
  Document,
} from '../types/index';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

class ApiClient {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Response interceptor to handle errors
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ErrorResponse>) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          localStorage.removeItem('access_token');
          localStorage.removeItem('user');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );

    // Load token from localStorage
    const token = localStorage.getItem('access_token');
    if (token) {
      this.token = token;
    }
  }

  setToken(token: string): void {
    this.token = token;
    localStorage.setItem('access_token', token);
  }

  clearToken(): void {
    this.token = null;
    localStorage.removeItem('access_token');
  }

  // Auth
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await this.client.post<LoginResponse>('/auth/login', credentials);
    this.setToken(response.data.access_token);
    localStorage.setItem('user', JSON.stringify(response.data.user));
    return response.data;
  }

  async logout(): Promise<void> {
    try {
      await this.client.post('/auth/logout');
    } finally {
      this.clearToken();
      localStorage.removeItem('user');
    }
  }

  // Dashboard
  async getDashboardMetrics(): Promise<DashboardMetrics> {
    const response = await this.client.get<DashboardMetrics>('/admin/dashboard/metrics');
    return response.data;
  }

  // Analytics
  async getAnalytics(period: string = '7d'): Promise<AnalyticsData> {
    const response = await this.client.get<AnalyticsData>('/admin/analytics', {
      params: { period },
    });
    return response.data;
  }

  // Documents
  async listDocuments(page: number = 1, pageSize: number = 20): Promise<DocumentListResponse> {
    const response = await this.client.get<DocumentListResponse>('/admin/documents', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  }

  async uploadDocument(formData: FormData): Promise<DocumentUploadResponse> {
    const response = await this.client.post<DocumentUploadResponse>(
      '/admin/documents/upload',
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    );
    return response.data;
  }

  async deleteDocument(documentId: string): Promise<void> {
    await this.client.delete(`/admin/documents/${documentId}`);
  }

  async getDocumentStatus(documentId: string): Promise<Document> {
    const response = await this.client.get<Document>(`/admin/documents/${documentId}`);
    return response.data;
  }

  // Scrape Jobs
  async listScrapeJobs(page: number = 1, pageSize: number = 20): Promise<PaginatedResponse<ScrapeJob>> {
    const response = await this.client.get<PaginatedResponse<ScrapeJob>>('/admin/scrape-jobs', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  }

  async triggerScrapeJob(request: ScrapeJobTriggerRequest): Promise<ScrapeJobTriggerResponse> {
    const response = await this.client.post<ScrapeJobTriggerResponse>(
      '/admin/scrape-jobs/trigger',
      request
    );
    return response.data;
  }

  async getScrapeJobStatus(jobId: string): Promise<ScrapeJob> {
    const response = await this.client.get<ScrapeJob>(`/admin/scrape-jobs/${jobId}`);
    return response.data;
  }

  async cancelScrapeJob(jobId: string): Promise<void> {
    await this.client.post(`/admin/scrape-jobs/${jobId}/cancel`);
  }

  // Conversations
  async listConversations(page: number = 1, pageSize: number = 20): Promise<ConversationListResponse> {
    const response = await this.client.get<ConversationListResponse>('/admin/conversations', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  }

  async getConversationDetail(sessionId: string): Promise<ConversationDetail> {
    const response = await this.client.get<ConversationDetail>(
      `/admin/conversations/${sessionId}`
    );
    return response.data;
  }

  // Feedback
  async listFeedback(page: number = 1, pageSize: number = 20): Promise<FeedbackListResponse> {
    const response = await this.client.get<FeedbackListResponse>('/admin/feedback', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  }

  async getFeedbackSentimentSummary(period: string = '30d'): Promise<FeedbackSentimentSummary> {
    const response = await this.client.get<FeedbackSentimentSummary>(
      '/admin/feedback/sentiment-summary',
      {
        params: { period },
      }
    );
    return response.data;
  }

  // System Config
  async getSystemConfig(): Promise<SystemConfig> {
    const response = await this.client.get<SystemConfig>('/admin/config');
    return response.data;
  }

  async updateSystemConfig(update: SystemConfigUpdateRequest): Promise<SystemConfigResponse> {
    const response = await this.client.put<SystemConfigResponse>('/admin/config', update);
    return response.data;
  }

  // Model Monitoring
  async getModelMetrics(period: string = '7d'): Promise<ModelMonitoringData> {
    const response = await this.client.get<ModelMonitoringData>('/admin/model-monitoring', {
      params: { period },
    });
    return response.data;
  }

  // Audit Log
  async listAuditLog(
    page: number = 1,
    pageSize: number = 50,
    filters?: { action?: string; resource_type?: string; user_id?: string }
  ): Promise<AuditLogListResponse> {
    const response = await this.client.get<AuditLogListResponse>('/admin/audit-log', {
      params: {
        page,
        page_size: pageSize,
        ...filters,
      },
    });
    return response.data;
  }

  // Health check
  async healthCheck(): Promise<{ status: string; service: string }> {
    const response = await this.client.get('/health');
    return response.data;
  }
}

export default new ApiClient();

// Helper type for paginated responses
interface PaginatedResponse<T> {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  items: T[];
}
