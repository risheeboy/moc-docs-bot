/**
 * API Client Service
 * Handles all HTTP communication with backend API
 */

import {
  ChatRequest,
  ChatQueryResponse,
  ErrorResponse,
  STTResponse,
  TTSResponse,
  TranslationResponse,
  FeedbackResponse,
  SessionResponse,
  FeedbackData,
  LanguageCode
} from '../types'
import { API_BASE_URL } from '../utils/constants'

/**
 * Error handling utility
 */
function handleApiError(response: Response): never {
  throw new Error(`API Error: ${response.status} ${response.statusText}`)
}

/**
 * Check if response contains error
 */
async function checkErrorResponse(response: Response) {
  if (!response.ok) {
    try {
      const errorData = (await response.json()) as ErrorResponse
      throw new Error(errorData.error?.message || 'API Error')
    } catch (e) {
      if (e instanceof Error) throw e
      throw new Error(`HTTP ${response.status}`)
    }
  }
}

/**
 * API Client class
 */
export class ApiClient {
  private baseUrl: string
  private sessionId: string = ''
  private requestIdCounter: number = 0

  constructor() {
    this.baseUrl = API_BASE_URL
  }

  /**
   * Set session ID for requests
   */
  setSessionId(sessionId: string): void {
    this.sessionId = sessionId
  }

  /**
   * Generate request ID
   */
  private getRequestId(): string {
    return `${Date.now()}-${++this.requestIdCounter}`
  }

  /**
   * Send chat query (non-streaming)
   */
  async sendChatQuery(
    query: string,
    language: LanguageCode,
    chatHistory?: Array<{ role: 'user' | 'assistant'; content: string }>
  ): Promise<ChatQueryResponse> {
    const request: ChatRequest = {
      query,
      language,
      session_id: this.sessionId || undefined,
      chat_history: chatHistory,
      top_k: 10,
      rerank_top_k: 5,
      filters: {
        source_sites: [],
        content_type: null,
        date_from: null,
        date_to: null
      }
    }

    const response = await fetch(`${this.baseUrl}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Request-ID': this.getRequestId()
      },
      body: JSON.stringify(request)
    })

    await checkErrorResponse(response)
    return response.json()
  }

  /**
   * Stream chat response via SSE
   */
  streamChatResponse(
    query: string,
    language: LanguageCode,
    chatHistory?: Array<{ role: 'user' | 'assistant'; content: string }>,
    onToken?: (token: string) => void,
    onSources?: (sources: any[]) => void,
    onError?: (error: string) => void
  ): AbortController {
    const controller = new AbortController()

    const request: ChatRequest = {
      query,
      language,
      session_id: this.sessionId || undefined,
      chat_history: chatHistory,
      top_k: 10,
      rerank_top_k: 5,
      filters: {
        source_sites: [],
        content_type: null,
        date_from: null,
        date_to: null
      }
    }

    fetch(`${this.baseUrl}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Request-ID': this.getRequestId()
      },
      body: JSON.stringify(request),
      signal: controller.signal
    })
      .then(async (response) => {
        if (!response.ok) {
          const error = await response.json()
          onError?.(error.error?.message || 'Stream error')
          return
        }

        const reader = response.body?.getReader()
        if (!reader) return

        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6))
                if (data.type === 'token' && onToken) {
                  onToken(data.content)
                } else if (data.type === 'sources' && onSources) {
                  onSources(data.sources)
                } else if (data.type === 'error' && onError) {
                  onError(data.message)
                }
              } catch (e) {
                console.error('Error parsing SSE data:', e)
              }
            }
          }
        }
      })
      .catch((error) => {
        if (error.name !== 'AbortError') {
          onError?.(error.message)
        }
      })

    return controller
  }

  /**
   * Speech-to-text
   */
  async transcribeAudio(
    audioBlob: Blob,
    language: LanguageCode
  ): Promise<STTResponse> {
    const formData = new FormData()
    formData.append('audio', audioBlob)
    formData.append('language', language)

    const response = await fetch(`${this.baseUrl}/speech/stt`, {
      method: 'POST',
      headers: {
        'X-Request-ID': this.getRequestId()
      },
      body: formData
    })

    await checkErrorResponse(response)
    return response.json()
  }

  /**
   * Text-to-speech
   */
  async synthesizeSpeech(
    text: string,
    language: LanguageCode,
    format: 'mp3' | 'wav' = 'mp3'
  ): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/speech/tts`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Request-ID': this.getRequestId()
      },
      body: JSON.stringify({
        text,
        language,
        format,
        voice: 'default'
      })
    })

    await checkErrorResponse(response)
    return response.blob()
  }

  /**
   * Translate text
   */
  async translateText(
    text: string,
    sourceLanguage: LanguageCode,
    targetLanguage: LanguageCode
  ): Promise<TranslationResponse> {
    const response = await fetch(`${this.baseUrl}/translate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Request-ID': this.getRequestId()
      },
      body: JSON.stringify({
        text,
        source_language: sourceLanguage,
        target_language: targetLanguage
      })
    })

    await checkErrorResponse(response)
    return response.json()
  }

  /**
   * Submit feedback
   */
  async submitFeedback(feedback: FeedbackData): Promise<FeedbackResponse> {
    const response = await fetch(`${this.baseUrl}/feedback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Request-ID': this.getRequestId()
      },
      body: JSON.stringify(feedback)
    })

    await checkErrorResponse(response)
    return response.json()
  }

  /**
   * Get or create session
   */
  async getOrCreateSession(language: LanguageCode): Promise<SessionResponse> {
    const response = await fetch(`${this.baseUrl}/session`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Request-ID': this.getRequestId()
      },
      body: JSON.stringify({ language })
    })

    await checkErrorResponse(response)
    const session = await response.json()
    this.sessionId = session.id
    return session
  }

  /**
   * Upload file for OCR
   */
  async uploadFile(file: File): Promise<{ document_id: string; text: string }> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${this.baseUrl}/ocr/upload`, {
      method: 'POST',
      headers: {
        'X-Request-ID': this.getRequestId()
      },
      body: formData
    })

    await checkErrorResponse(response)
    return response.json()
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/health`)
      return response.ok
    } catch {
      return false
    }
  }
}

// Singleton instance
export const apiClient = new ApiClient()
