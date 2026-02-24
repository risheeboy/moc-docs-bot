import { describe, it, expect, vi, beforeEach } from 'vitest'
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

describe('useSearch', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
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
    const mockSearch = vi.spyOn(api.apiClient, 'search').mockResolvedValue(mockSearchResponse)
    const { result } = renderHook(() => useSearch({ debounceMs: 300 }))

    act(() => {
      result.current.handleQueryChange('test query', 'en')
    })

    expect(mockSearch).not.toHaveBeenCalled()

    act(() => {
      vi.advanceTimersByTime(300)
    })

    await waitFor(() => {
      expect(mockSearch).toHaveBeenCalled()
    })
  })

  it('handles search errors', async () => {
    const mockError = new Error('Search failed')
    vi.spyOn(api.apiClient, 'search').mockRejectedValue(mockError)
    const { result } = renderHook(() => useSearch())

    act(() => {
      result.current.handleQueryChange('test query', 'en')
      vi.advanceTimersByTime(300)
    })

    await waitFor(() => {
      expect(result.current.error).toBe('Search failed')
      expect(result.current.results).toBeNull()
    })
  })

  it('updates page on handlePageChange', async () => {
    const mockSearch = vi.spyOn(api.apiClient, 'search').mockResolvedValue(mockSearchResponse)
    const { result } = renderHook(() => useSearch())

    act(() => {
      result.current.handleQueryChange('test query', 'en')
      vi.advanceTimersByTime(300)
    })

    await waitFor(() => {
      expect(result.current.currentPage).toBe(1)
    })

    act(() => {
      result.current.handlePageChange(2, 'en')
    })

    expect(mockSearch).toHaveBeenLastCalledWith(
      expect.objectContaining({
        page: 2,
      })
    )
  })

  it('clears results when query is empty', async () => {
    const { result } = renderHook(() => useSearch())

    act(() => {
      result.current.handleQueryChange('', 'en')
    })

    expect(result.current.results).toBeNull()
  })
})
