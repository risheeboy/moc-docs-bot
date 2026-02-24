import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { SearchFilters } from '../types'
import '../styles/search.css'

interface FacetFiltersProps {
  filters: SearchFilters & { contentTypes?: string[] }
  onFiltersChange: (filters: SearchFilters) => void
  availableSites?: string[]
}

const DEFAULT_SITES = [
  'culture.gov.in',
  'asi.nic.in',
  'ncert.nic.in',
  'nift.ac.in',
  'iccr.gov.in',
]

const CONTENT_TYPES = ['webpage', 'document', 'event', 'multimedia']

export default function FacetFilters({
  filters,
  onFiltersChange,
  availableSites = DEFAULT_SITES,
}: FacetFiltersProps) {
  const { t } = useTranslation()
  const [isExpanded, setIsExpanded] = useState(false)

  const handleSiteToggle = (site: string) => {
    const newSites = filters.source_sites?.includes(site)
      ? filters.source_sites.filter((s) => s !== site)
      : [...(filters.source_sites || []), site]

    onFiltersChange({
      ...filters,
      source_sites: newSites,
    })
  }

  const handleContentTypeToggle = (type: string) => {
    const currentTypes = filters.contentTypes || []
    const newTypes = currentTypes.includes(type)
      ? currentTypes.filter((t) => t !== type)
      : [...currentTypes, type]

    onFiltersChange({
      ...filters,
      contentTypes: newTypes,
      content_type: newTypes.length === 1 ? newTypes[0] : undefined,
    })
  }

  const handleDateFromChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFiltersChange({
      ...filters,
      date_from: e.target.value,
    })
  }

  const handleDateToChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFiltersChange({
      ...filters,
      date_to: e.target.value,
    })
  }

  const handleClearFilters = () => {
    onFiltersChange({
      source_sites: [],
    })
  }

  const activeFilterCount = [
    filters.source_sites?.length || 0,
    filters.contentTypes?.length || 0,
    filters.date_from ? 1 : 0,
    filters.date_to ? 1 : 0,
  ].reduce((a, b) => a + b, 0)

  return (
    <aside className="facet-filters">
      <div className="filters-header">
        <h2>{t('search:filters')}</h2>
        <button
          className="filters-toggle"
          onClick={() => setIsExpanded(!isExpanded)}
          aria-expanded={isExpanded}
          aria-label={t('search:aria_toggle_filters')}
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <path d="M3 5a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-.293.707l-5.414 5.414a1 1 0 00-.293.707v3.172a1 1 0 01-.578.894l-2 1A1 1 0 018 17v-5.172a1 1 0 00-.293-.707L2.293 7.707A1 1 0 012 7V5z" />
          </svg>
          {activeFilterCount > 0 && (
            <span className="filter-badge">{activeFilterCount}</span>
          )}
        </button>
      </div>

      {isExpanded && (
        <div className="filters-content">
          {/* Source Sites */}
          <fieldset className="filter-group">
            <legend>{t('search:source_sites')}</legend>
            <div className="filter-options">
              {availableSites.map((site) => (
                <label key={site} className="filter-checkbox">
                  <input
                    type="checkbox"
                    checked={filters.source_sites?.includes(site) || false}
                    onChange={() => handleSiteToggle(site)}
                  />
                  <span>{site}</span>
                </label>
              ))}
            </div>
          </fieldset>

          {/* Content Types */}
          <fieldset className="filter-group">
            <legend>{t('search:content_type')}</legend>
            <div className="filter-options">
              {CONTENT_TYPES.map((type) => (
                <label key={type} className="filter-checkbox">
                  <input
                    type="checkbox"
                    checked={filters.contentTypes?.includes(type) || false}
                    onChange={() => handleContentTypeToggle(type)}
                  />
                  <span>{t(`search:content_${type}`)}</span>
                </label>
              ))}
            </div>
          </fieldset>

          {/* Date Range */}
          <fieldset className="filter-group">
            <legend>{t('search:date_range')}</legend>
            <div className="date-inputs">
              <label>
                <span>{t('search:from')}</span>
                <input
                  type="date"
                  value={filters.date_from || ''}
                  onChange={handleDateFromChange}
                />
              </label>
              <label>
                <span>{t('search:to')}</span>
                <input
                  type="date"
                  value={filters.date_to || ''}
                  onChange={handleDateToChange}
                />
              </label>
            </div>
          </fieldset>

          {/* Clear Filters */}
          {activeFilterCount > 0 && (
            <button
              className="clear-filters-button"
              onClick={handleClearFilters}
              type="button"
            >
              {t('search:clear_filters')}
            </button>
          )}
        </div>
      )}
    </aside>
  )
}
