import {
  SearchRequest,
  SearchResponse,
  SuggestResponse,
  TranslateRequest,
  TranslateResponse,
  FeedbackRequest,
  ErrorResponse,
} from '../types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  private getRequestId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const errorData: ErrorResponse = await response.json().catch(() => ({
        error: {
          code: `HTTP_${response.status}`,
          message: response.statusText,
        },
      }))
      throw new Error(errorData.error.message || 'API request failed')
    }
    return response.json()
  }

  async search(request: SearchRequest): Promise<SearchResponse> {
    const response = await fetch(`${this.baseUrl}/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Request-ID': this.getRequestId(),
      },
      body: JSON.stringify(request),
    })
    return this.handleResponse<SearchResponse>(response)
  }

  async getSuggestions(
    query: string,
    language: string
  ): Promise<SuggestResponse> {
    const params = new URLSearchParams({
      q: query,
      language: language,
    })
    const response = await fetch(`${this.baseUrl}/search/suggest?${params}`, {
      method: 'GET',
      headers: {
        'X-Request-ID': this.getRequestId(),
      },
    })
    return this.handleResponse<SuggestResponse>(response)
  }

  async translate(request: TranslateRequest): Promise<TranslateResponse> {
    const response = await fetch(`${this.baseUrl}/translate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Request-ID': this.getRequestId(),
      },
      body: JSON.stringify(request),
    })
    return this.handleResponse<TranslateResponse>(response)
  }

  async submitFeedback(request: FeedbackRequest): Promise<{ success: boolean }> {
    const response = await fetch(`${this.baseUrl}/feedback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Request-ID': this.getRequestId(),
      },
      body: JSON.stringify(request),
    })
    return this.handleResponse<{ success: boolean }>(response)
  }

  async healthCheck(): Promise<{
    status: string
    service: string
    version: string
  }> {
    const response = await fetch(`${this.baseUrl.replace('/v1', '')}/health`, {
      method: 'GET',
      headers: {
        'X-Request-ID': this.getRequestId(),
      },
    })
    return this.handleResponse(response)
  }
}

export const apiClient = new ApiClient()
