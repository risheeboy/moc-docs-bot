import { useState, useCallback, useRef, useEffect } from 'react'
import { apiClient } from '../services/api'
import {
  SearchRequest,
  SearchResponse,
  SearchFilters,
  SearchSuggestion,
} from '../types'

interface UseSearchOptions {
  debounceMs?: number
  pageSize?: number
}

export function useSearch(options: UseSearchOptions = {}) {
  const { debounceMs = 300, pageSize = 20 } = options

  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResponse | null>(null)
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [filters, setFilters] = useState<SearchFilters>({
    source_sites: [],
  })

  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null)

  const performSearch = useCallback(
    async (
      searchQuery: string,
      language: string,
      page: number = 1,
      searchFilters: SearchFilters = filters
    ) => {
      if (!searchQuery.trim()) {
        setResults(null)
        setSuggestions([])
        return
      }

      setIsLoading(true)
      setError(null)

      try {
        const request: SearchRequest = {
          query: searchQuery,
          language: language,
          page: page,
          page_size: pageSize,
          filters: searchFilters,
        }

        const response = await apiClient.search(request)
        setResults(response)
        setCurrentPage(page)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Search failed')
        setResults(null)
      } finally {
        setIsLoading(false)
      }
    },
    [filters, pageSize]
  )

  const fetchSuggestions = useCallback(
    async (searchQuery: string, language: string) => {
      if (!searchQuery.trim()) {
        setSuggestions([])
        return
      }

      try {
        const response = await apiClient.getSuggestions(searchQuery, language)
        setSuggestions(response.suggestions)
      } catch (err) {
        console.error('Failed to fetch suggestions:', err)
        setSuggestions([])
      }
    },
    []
  )

  const handleQueryChange = useCallback(
    (newQuery: string, language: string) => {
      setQuery(newQuery)
      setCurrentPage(1)

      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }

      debounceTimerRef.current = setTimeout(() => {
        performSearch(newQuery, language, 1, filters)
      }, debounceMs)

      fetchSuggestions(newQuery, language)
    },
    [debounceMs, performSearch, filters, fetchSuggestions]
  )

  const handlePageChange = useCallback(
    (page: number, language: string) => {
      performSearch(query, language, page, filters)
    },
    [query, filters, performSearch]
  )

  const updateFilters = useCallback(
    (newFilters: Partial<SearchFilters>, language: string) => {
      const updatedFilters = { ...filters, ...newFilters }
      setFilters(updatedFilters)
      setCurrentPage(1)
      performSearch(query, language, 1, updatedFilters)
    },
    [filters, query, performSearch]
  )

  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }
    }
  }, [])

  return {
    query,
    results,
    suggestions,
    isLoading,
    error,
    currentPage,
    filters,
    handleQueryChange,
    handlePageChange,
    updateFilters,
    performSearch,
  }
}
