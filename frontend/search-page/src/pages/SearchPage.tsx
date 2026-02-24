import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import SearchBar from '../components/SearchBar'
import SearchResults from '../components/SearchResults'
import FacetFilters from '../components/FacetFilters'
import LanguageToggle from '../components/LanguageToggle'
import AccessibilityControls from '../components/AccessibilityControls'
import AISummaryPanel from '../components/AISummaryPanel'
import { useSearch } from '../hooks/useSearch'
import { useFilters } from '../hooks/useFilters'
import { apiClient } from '../services/api'
import { SearchResponse } from '../types'
import '../styles/search.css'

export default function SearchPage() {
  const { t, i18n } = useTranslation()
  const {
    query,
    results,
    isLoading,
    error,
    currentPage,
    filters,
    handleQueryChange,
    handlePageChange,
    updateFilters,
  } = useSearch({
    debounceMs: 300,
    pageSize: 20,
  })

  const { filters: filterState, toggleSourceSite, toggleContentType, updateDateRange } = useFilters()
  const [displayResults, setDisplayResults] = useState<SearchResponse | null>(null)

  useEffect(() => {
    setDisplayResults(results)
  }, [results])

  const handleSearch = (searchQuery: string) => {
    handleQueryChange(searchQuery, i18n.language)
  }

  const handleFilterChange = (newFilters: typeof filterState) => {
    updateFilters(newFilters, i18n.language)
  }

  const handlePageChange_ = (page: number) => {
    handlePageChange(page, i18n.language)
  }

  const handleTranslate = (translatedResults: SearchResponse) => {
    setDisplayResults(translatedResults)
  }

  const handleFeedback = async (resultUrl: string, isHelpful: boolean) => {
    try {
      await apiClient.submitFeedback({
        result_id: resultUrl,
        query: query,
        is_helpful: isHelpful,
        language: i18n.language,
      })
    } catch (error) {
      console.error('Feedback submission failed:', error)
    }
  }

  return (
    <div className="search-page">
      {/* GIGW Header */}
      <header className="page-header" role="banner">
        <div className="header-top">
          <div className="government-emblem">
            <svg width="40" height="40" viewBox="0 0 200 200" fill="none">
              <circle cx="100" cy="100" r="95" stroke="#1f3a93" strokeWidth="3" />
              <text
                x="100"
                y="110"
                textAnchor="middle"
                fontSize="40"
                fontWeight="bold"
                fill="#1f3a93"
              >
                🇮🇳
              </text>
            </svg>
          </div>

          <div className="ministry-header">
            <h1 className="ministry-title">
              <span lang="en">Ministry of Culture</span>
              <span lang="hi">संस्कृति मंत्रालय</span>
            </h1>
            <p className="ministry-subtitle">Government of India</p>
          </div>

          <div className="header-controls">
            <LanguageToggle
              results={displayResults}
              currentLanguage={i18n.language}
              onLanguageChange={(lang) => {
                i18n.changeLanguage(lang)
                localStorage.setItem('language', lang)
              }}
              onResultsTranslate={handleTranslate}
            />
            <AccessibilityControls />
          </div>
        </div>
      </header>

      {/* Skip to content link */}
      <a href="#main-content" className="skip-to-content">
        {t('search:skip_to_content')}
      </a>

      {/* Main Search Section */}
      <div className="search-section">
        <div className="search-container">
          <SearchBar
            query={query}
            isLoading={isLoading}
            onQueryChange={handleSearch}
            onSubmit={handleSearch}
          />

          {error && (
            <div className="error-message" role="alert">
              <p>{error}</p>
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <main id="main-content" className="main-content" role="main">
        {/* AI Summary */}
        {displayResults && (
          <AISummaryPanel
            summary={displayResults.ai_summary}
            isLoading={isLoading}
          />
        )}

        <div className="search-body">
          {/* Filters Sidebar */}
          <FacetFilters
            filters={filterState}
            onFiltersChange={handleFilterChange}
          />

          {/* Results */}
          <SearchResults
            results={displayResults}
            isLoading={isLoading}
            currentPage={currentPage}
            onPageChange={handlePageChange_}
            onResultFeedback={handleFeedback}
          />
        </div>
      </main>

      {/* GIGW Footer */}
      <footer className="page-footer" role="contentinfo">
        <div className="footer-content">
          <div className="footer-section">
            <p>{t('search:content_managed_by')}</p>
            <p>{t('search:designed_by')}</p>
            <p>
              {t('search:last_updated')}: {new Date().toLocaleDateString()}
            </p>
          </div>

          <div className="footer-links">
            <a href="/sitemap">{t('search:sitemap')}</a>
            <a href="/feedback">{t('search:feedback')}</a>
            <a href="/terms">{t('search:terms')}</a>
            <a href="/privacy">{t('search:privacy')}</a>
            <a href="/copyright">{t('search:copyright')}</a>
            <a href="/hyperlinking">{t('search:hyperlinking')}</a>
            <a href="/accessibility">{t('search:accessibility_statement')}</a>
          </div>
        </div>

        <div className="footer-bottom">
          <p>© {new Date().getFullYear()} Ministry of Culture. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}
