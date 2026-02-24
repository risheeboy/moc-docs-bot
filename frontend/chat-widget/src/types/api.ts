/**
 * API Response Type Definitions
 * Matches Shared Contracts §4, §8
 */

import { Message, Source, LanguageCode } from './chat'

// Error responses from §4
export interface ErrorDetail {
  code: string
  message: string
  details?: Record<string, unknown>
  request_id?: string
}

export interface ErrorResponse {
  error: ErrorDetail
}

// Chat query response
export interface ChatQueryResponse {
  id: string
  content: string
  language: LanguageCode
  sources: Source[]
  confidence: number
  has_fallback: boolean
  created_at: string
  session_id: string
  model_version?: string
}

// Chat stream events (SSE)
export interface ChatStreamEvent {
  type: 'token' | 'sources' | 'complete' | 'error'
  data: unknown
  timestamp: string
}

// Speech-to-Text response
export interface STTResponse {
  text: string
  language: LanguageCode
  confidence: number
  duration_seconds: number
}

// Text-to-Speech response (audio/mpeg)
export interface TTSResponse {
  audio_url: string
  duration_seconds: number
  language: LanguageCode
}

// Translation response
export interface TranslationResponse {
  translated_text: string
  source_language: LanguageCode
  target_language: LanguageCode
  cached: boolean
}

// Feedback submission response
export interface FeedbackResponse {
  id: string
  message_id: string
  session_id: string
  rating: 'helpful' | 'not_helpful'
  comment?: string
  created_at: string
}

// Session info response
export interface SessionResponse {
  id: string
  created_at: string
  updated_at: string
  language: LanguageCode
  message_count: number
  is_active: boolean
}

// Health check response
export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy'
  service: string
  version: string
  uptime_seconds: number
  timestamp: string
  dependencies: Record<string, {
    status: 'healthy' | 'degraded' | 'unhealthy'
    latency_ms: number
  }>
}

// Chat history for context
export interface ChatHistoryRequest {
  messages: Array<{
    role: 'user' | 'assistant'
    content: string
  }>
}

// API request/response for chat
export interface ChatRequest {
  query: string
  language: LanguageCode
  session_id?: string
  chat_history?: ChatMessage[]
  top_k?: number
  rerank_top_k?: number
  filters?: {
    source_sites?: string[]
    content_type?: string | null
    date_from?: string | null
    date_to?: string | null
  }
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

// Pagination types
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}
