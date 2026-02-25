import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useSearch } from '../src/hooks/useSearch'
import * as api from '../src/services/api'

vi.mock('../src/services/api')

const mockSearchResponse = {
  results: [
    {
      title: 'Test Result',
      url: 'https://example.com',
      snippet: 'Test snippet',
      score: 0.95,
      source_site: 'culture.gov.in',
      language: 'en',
      content_type: 'webpage',
    },
  ],
  multimedia: [],
  events: [],
  total_results: 1,
  page: 1,
  page_size: 20,
  cached: false,
}

const mockSuggestionsResponse = {
  suggestions: [
    { text: 'test suggestion', confidence: 0.9 }
  ]
}

describe('useSearch', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Mock the API methods
    vi.mocked(api.apiClient.search).mockResolvedValue(mockSearchResponse)
    vi.mocked(api.apiClient.getSuggestions).mockResolvedValue(mockSuggestionsResponse)
  })

  it('initializes with empty state', () => {
    const { result } = renderHook(() => useSearch())
    expect(result.current.query).toBe('')
    expect(result.current.results).toBeNull()
    expect(result.current.isLoading).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('updates query on handleQueryChange', () => {
    const { result } = renderHook(() => useSearch())
    act(() => {
      result.current.handleQueryChange('test query', 'en')
    })
    expect(result.current.query).toBe('test query')
  })

  it('performs search with debounce', async () => {
    const { result } = renderHook(() => useSearch({ debounceMs: 100 }))

    act(() => {
      result.current.handleQueryChange('test query', 'en')
    })

    // Mock should be called after debounce
    await waitFor(() => {
      expect(vi.mocked(api.apiClient.search)).toHaveBeenCalled()
    }, { timeout: 2000 })
  })

  it('handles search errors', async () => {
    const mockError = new Error('Search failed')
    vi.mocked(api.apiClient.search).mockRejectedValueOnce(mockError)
    const { result } = renderHook(() => useSearch())

    act(() => {
      result.current.handleQueryChange('test query', 'en')
    })

    await waitFor(() => {
      expect(result.current.error).toBe('Search failed')
    }, { timeout: 2000 })
  })

  it('updates page on handlePageChange', async () => {
    const { result } = renderHook(() => useSearch())

    act(() => {
      result.current.handleQueryChange('test query', 'en')
    })

    await waitFor(() => {
      expect(result.current.currentPage).toBe(1)
    }, { timeout: 2000 })

    vi.clearAllMocks()
    vi.mocked(api.apiClient.search).mockResolvedValue(mockSearchResponse)

    act(() => {
      result.current.handlePageChange(2, 'en')
    })

    await waitFor(() => {
      expect(vi.mocked(api.apiClient.search)).toHaveBeenCalledWith(
        expect.objectContaining({
          page: 2,
        })
      )
    }, { timeout: 2000 })
  })

  it('clears results when query is empty', async () => {
    const { result } = renderHook(() => useSearch())

    act(() => {
      result.current.handleQueryChange('', 'en')
    })

    expect(result.current.results).toBeNull()
  })
})
