/**
 * useChat Hook Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useChat } from '../src/hooks/useChat'
import * as api from '../src/services/api'

vi.mock('../src/services/api')

describe('useChat Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('initializes with default state', () => {
    const { result } = renderHook(() => useChat())
    expect(result.current.messages).toEqual([])
    expect(result.current.isLoading).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('initializes session on mount', async () => {
    const mockSession = {
      id: 'session-1',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      language: 'hi' as const,
      message_count: 0,
      is_active: true
    }

    vi.mocked(api.apiClient.getOrCreateSession).mockResolvedValueOnce(mockSession)

    const { result } = renderHook(() => useChat())

    await waitFor(() => {
      expect(result.current.session).not.toBeNull()
    })

    expect(result.current.session?.id).toBe('session-1')
  })

  it('sends message successfully', async () => {
    const mockSession = {
      id: 'session-1',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      language: 'hi' as const,
      message_count: 0,
      is_active: true
    }

    const mockResponse = {
      id: 'msg-1',
      content: 'Response text',
      language: 'hi' as const,
      sources: [],
      confidence: 0.9,
      has_fallback: false,
      created_at: new Date().toISOString(),
      session_id: 'session-1'
    }

    vi.mocked(api.apiClient.getOrCreateSession).mockResolvedValueOnce(mockSession)
    vi.mocked(api.apiClient.sendChatQuery).mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(() => useChat())

    await waitFor(() => {
      expect(result.current.session).not.toBeNull()
    })

    await act(async () => {
      await result.current.sendMessage('Hello')
    })

    expect(result.current.messages).toHaveLength(2) // User + Assistant
  })

  it('handles errors gracefully', async () => {
    const mockSession = {
      id: 'session-1',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      language: 'hi' as const,
      message_count: 0,
      is_active: true
    }

    vi.mocked(api.apiClient.getOrCreateSession).mockResolvedValueOnce(mockSession)
    vi.mocked(api.apiClient.sendChatQuery).mockRejectedValueOnce(
      new Error('API Error')
    )

    const { result } = renderHook(() => useChat())

    await waitFor(() => {
      expect(result.current.session).not.toBeNull()
    })

    await act(async () => {
      await result.current.sendMessage('Hello')
    })

    expect(result.current.error).toBe('API Error')
  })

  it('changes language', async () => {
    const mockSession = {
      id: 'session-1',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      language: 'en' as const,
      message_count: 0,
      is_active: true
    }

    vi.mocked(api.apiClient.getOrCreateSession).mockResolvedValueOnce(mockSession)

    const { result } = renderHook(() => useChat())

    await waitFor(() => {
      expect(result.current.session).not.toBeNull()
    })

    await act(async () => {
      await result.current.changeLanguage('en')
    })

    expect(result.current.currentLanguage).toBe('en')
    expect(result.current.messages).toHaveLength(0)
  })

  it('clears messages', async () => {
    const mockSession = {
      id: 'session-1',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      language: 'hi' as const,
      message_count: 0,
      is_active: true
    }

    const mockResponse = {
      id: 'msg-1',
      content: 'Response',
      language: 'hi' as const,
      sources: [],
      confidence: 0.9,
      has_fallback: false,
      created_at: new Date().toISOString(),
      session_id: 'session-1'
    }

    vi.mocked(api.apiClient.getOrCreateSession).mockResolvedValueOnce(mockSession)
    vi.mocked(api.apiClient.sendChatQuery).mockResolvedValueOnce(mockResponse)

    const { result } = renderHook(() => useChat())

    await waitFor(() => {
      expect(result.current.session).not.toBeNull()
    })

    await act(async () => {
      await result.current.sendMessage('Hello')
    })

    expect(result.current.messages.length).toBeGreaterThan(0)

    act(() => {
      result.current.clearMessages()
    })

    expect(result.current.messages).toHaveLength(0)
  })

  it('maintains context window', async () => {
    const mockSession = {
      id: 'session-1',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      language: 'hi' as const,
      message_count: 0,
      is_active: true
    }

    vi.mocked(api.apiClient.getOrCreateSession).mockResolvedValueOnce(mockSession)

    const { result } = renderHook(() => useChat())

    await waitFor(() => {
      expect(result.current.session).not.toBeNull()
    })

    expect(result.current.contextMessages).toEqual(result.current.messages)
  })
})
