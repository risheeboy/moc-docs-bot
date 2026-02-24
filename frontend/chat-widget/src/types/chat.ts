/**
 * Chat Widget Type Definitions
 * Matches API contracts from Shared Contracts §8 and §10
 */

export type LanguageCode =
  | 'hi' | 'en' | 'bn' | 'te' | 'mr' | 'ta'
  | 'ur' | 'gu' | 'kn' | 'ml' | 'or' | 'pa'
  | 'as' | 'mai' | 'sa' | 'ne' | 'sd' | 'kok'
  | 'doi' | 'mni' | 'sat' | 'bo' | 'ks'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  language: LanguageCode
  created_at: string
  sources?: Source[]
  has_fallback?: boolean
}

export interface Source {
  title: string
  url: string
  snippet: string
  score: number
  source_site: string
  language: LanguageCode
  content_type: 'webpage' | 'pdf' | 'document' | 'image' | 'video'
  chunk_id?: string
  published_date?: string
}

export interface ChatSession {
  id: string
  created_at: string
  updated_at: string
  language: LanguageCode
  messages: Message[]
  is_active: boolean
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface VoiceInput {
  audio_data: Blob
  language: LanguageCode
}

export interface FeedbackData {
  message_id: string
  session_id: string
  rating: 'helpful' | 'not_helpful'
  comment?: string
  language: LanguageCode
}

export interface AccessibilityPreferences {
  font_size: 'small' | 'normal' | 'large' | 'xlarge'
  high_contrast: boolean
  reduce_motion: boolean
  screen_reader_mode: boolean
}
