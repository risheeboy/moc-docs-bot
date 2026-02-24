export interface SearchResult {
  title: string
  url: string
  snippet: string
  score: number
  source_site: string
  language: string
  content_type: string
  thumbnail_url?: string
  published_date?: string
}

export interface MultimediaResult {
  type: 'image' | 'video'
  url: string
  alt_text: string
  source_site: string
  thumbnail_url?: string
}

export interface EventResult {
  title: string
  date: string
  venue: string
  description: string
  source_url: string
  language: string
}

export interface AISummary {
  summary: string
  confidence: number
  sources: string[]
}

export interface SearchResponse {
  results: SearchResult[]
  multimedia: MultimediaResult[]
  events: EventResult[]
  ai_summary?: AISummary
  total_results: number
  page: number
  page_size: number
  cached: boolean
  request_id?: string
}

export interface SearchRequest {
  query: string
  language: string
  page: number
  page_size: number
  filters: SearchFilters
}

export interface SearchFilters {
  source_sites: string[]
  content_type?: string
  date_from?: string
  date_to?: string
  language?: string
}

export interface SearchSuggestion {
  text: string
  category: 'history' | 'trending' | 'related'
  language: string
}

export interface SuggestResponse {
  suggestions: SearchSuggestion[]
}

export interface FeedbackRequest {
  result_id: string
  query: string
  is_helpful: boolean
  feedback_text?: string
  language: string
}

export interface TranslateRequest {
  text: string
  source_language: string
  target_language: string
}

export interface TranslateResponse {
  translated_text: string
  source_language: string
  target_language: string
  cached: boolean
}
