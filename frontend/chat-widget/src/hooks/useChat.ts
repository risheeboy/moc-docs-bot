/**
 * useChat Hook
 * Manages chat state, multi-turn context, and SSE streaming
 */

import { useState, useCallback, useRef, useEffect } from 'react'
import { Message, ChatSession, LanguageCode, Source } from '../types'
import { apiClient } from '../services/api'
import { streamingService } from '../services/streaming'
import { CHAT_CONFIG, FALLBACK_MESSAGES } from '../utils/constants'

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [session, setSession] = useState<ChatSession | null>(null)
  const [currentLanguage, setCurrentLanguage] = useState<LanguageCode>('hi')
  const [error, setError] = useState<string | null>(null)
  const streamAbortController = useRef<AbortController | null>(null)

  /**
   * Initialize session
   */
  const initializeSession = useCallback(async (language: LanguageCode) => {
    try {
      setCurrentLanguage(language)
      const sessionData = await apiClient.getOrCreateSession(language)
      setSession({
        id: sessionData.id,
        created_at: sessionData.created_at,
        updated_at: sessionData.updated_at,
        language: sessionData.language || language,
        messages: [],
        is_active: sessionData.is_active
      })
      apiClient.setSessionId(sessionData.id)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to initialize session'
      setError(message)
    }
  }, [])

  /**
   * Send message (non-streaming)
   */
  const sendMessage = useCallback(
    async (query: string) => {
      if (!query.trim()) return
      if (!session) {
        setError('Session not initialized')
        return
      }

      const userMessage: Message = {
        id: `msg-${Date.now()}`,
        role: 'user',
        content: query,
        language: currentLanguage,
        created_at: new Date().toISOString()
      }

      setMessages((prev) => [...prev, userMessage])
      setIsLoading(true)
      setError(null)

      try {
        const chatHistory = messages.map((m) => ({
          role: m.role,
          content: m.content
        }))

        const response = await apiClient.sendChatQuery(
          query,
          currentLanguage,
          chatHistory
        )

        const assistantMessage: Message = {
          id: response.id,
          role: 'assistant',
          content: response.content,
          language: response.language,
          created_at: response.created_at,
          sources: response.sources,
          has_fallback: response.has_fallback
        }

        setMessages((prev) => [...prev, assistantMessage])
        setSession((prev) => {
          if (!prev) return prev
          return { ...prev, updated_at: new Date().toISOString() }
        })
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to send message'
        setError(message)
      } finally {
        setIsLoading(false)
      }
    },
    [messages, session, currentLanguage]
  )

  /**
   * Send message with streaming
   */
  const sendMessageStream = useCallback(
    (
      query: string,
      onToken?: (token: string) => void,
      onSources?: (sources: Source[]) => void
    ) => {
      if (!query.trim()) return
      if (!session) {
        setError('Session not initialized')
        return
      }

      const userMessage: Message = {
        id: `msg-${Date.now()}`,
        role: 'user',
        content: query,
        language: currentLanguage,
        created_at: new Date().toISOString()
      }

      setMessages((prev) => [...prev, userMessage])
      setIsLoading(true)
      setError(null)

      const chatHistory = messages.map((m) => ({
        role: m.role,
        content: m.content
      }))

      let fullContent = ''
      let responseSources: Source[] = []

      streamAbortController.current = apiClient.streamChatResponse(
        query,
        currentLanguage,
        chatHistory,
        (token) => {
          fullContent += token
          onToken?.(token)
        },
        (sources) => {
          responseSources = sources
          onSources?.(sources)
        },
        (errorMsg) => {
          setError(errorMsg)
          setIsLoading(false)
        }
      )

      // Wait for stream to complete (simplified - in real impl, need proper stream completion)
      setTimeout(() => {
        if (fullContent) {
          const assistantMessage: Message = {
            id: `msg-${Date.now()}-response`,
            role: 'assistant',
            content: fullContent,
            language: currentLanguage,
            created_at: new Date().toISOString(),
            sources: responseSources,
            has_fallback: false
          }

          setMessages((prev) => [...prev, assistantMessage])
          setSession((prev) => {
            if (!prev) return prev
            return { ...prev, updated_at: new Date().toISOString() }
          })
        }
        setIsLoading(false)
      }, 100)
    },
    [messages, session, currentLanguage]
  )

  /**
   * Change language
   */
  const changeLanguage = useCallback(async (language: LanguageCode) => {
    setCurrentLanguage(language)
    setMessages([])
    await initializeSession(language)
    localStorage.setItem('language', language)
  }, [initializeSession])

  /**
   * Clear messages
   */
  const clearMessages = useCallback(() => {
    setMessages([])
    setError(null)
  }, [])

  /**
   * Stop streaming
   */
  const stopStreaming = useCallback(() => {
    if (streamAbortController.current) {
      streamAbortController.current.abort()
      streamAbortController.current = null
    }
    setIsLoading(false)
  }, [])

  /**
   * Add context window management
   */
  const contextMessages = messages.slice(-CHAT_CONFIG.MAX_CONTEXT_MESSAGES)

  /**
   * Load session from localStorage if exists
   */
  useEffect(() => {
    const savedLanguage = localStorage.getItem('language') as LanguageCode || 'hi'
    initializeSession(savedLanguage)
  }, [initializeSession])

  return {
    messages,
    contextMessages,
    isLoading,
    session,
    currentLanguage,
    error,
    sendMessage,
    sendMessageStream,
    changeLanguage,
    clearMessages,
    stopStreaming,
    initializeSession
  }
}
