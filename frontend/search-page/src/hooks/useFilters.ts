import { useState, useCallback } from 'react'
import { SearchFilters } from '../types'

export interface FilterState extends SearchFilters {
  contentTypes?: string[]
}

export function useFilters(initialFilters: FilterState = {}) {
  const [filters, setFilters] = useState<FilterState>(initialFilters)

  const updateSourceSites = useCallback((sites: string[]) => {
    setFilters((prev) => ({
      ...prev,
      source_sites: sites,
    }))
  }, [])

  const updateContentTypes = useCallback((types: string[]) => {
    setFilters((prev) => ({
      ...prev,
      contentTypes: types,
      content_type: types.length === 1 ? types[0] : undefined,
    }))
  }, [])

  const updateLanguage = useCallback((language: string) => {
    setFilters((prev) => ({
      ...prev,
      language: language || undefined,
    }))
  }, [])

  const updateDateRange = useCallback(
    (dateFrom?: string, dateTo?: string) => {
      setFilters((prev) => ({
        ...prev,
        date_from: dateFrom,
        date_to: dateTo,
      }))
    },
    []
  )

  const clearFilters = useCallback(() => {
    setFilters({
      source_sites: [],
    })
  }, [])

  const toggleSourceSite = useCallback((site: string) => {
    setFilters((prev) => {
      const sites = prev.source_sites || []
      return {
        ...prev,
        source_sites: sites.includes(site)
          ? sites.filter((s) => s !== site)
          : [...sites, site],
      }
    })
  }, [])

  const toggleContentType = useCallback((type: string) => {
    setFilters((prev) => {
      const types = prev.contentTypes || []
      const newTypes = types.includes(type)
        ? types.filter((t) => t !== type)
        : [...types, type]

      return {
        ...prev,
        contentTypes: newTypes,
        content_type: newTypes.length === 1 ? newTypes[0] : undefined,
      }
    })
  }, [])

  return {
    filters,
    updateSourceSites,
    updateContentTypes,
    updateLanguage,
    updateDateRange,
    clearFilters,
    toggleSourceSite,
    toggleContentType,
  }
}
