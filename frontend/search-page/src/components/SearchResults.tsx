import { useTranslation } from 'react-i18next'
import { SearchResponse } from '../types'
import ResultCard from './ResultCard'
import MultimediaResult from './MultimediaResult'
import EventCard from './EventCard'
import Pagination from './Pagination'
import RelatedQueries from './RelatedQueries'
import '../styles/search.css'

interface SearchResultsProps {
  results: SearchResponse | null
  isLoading: boolean
  currentPage: number
  onPageChange: (page: number) => void
  onResultFeedback?: (resultId: string, isHelpful: boolean) => void
}

export default function SearchResults({
  results,
  isLoading,
  currentPage,
  onPageChange,
  onResultFeedback,
}: SearchResultsProps) {
  const { t } = useTranslation()

  if (!results && !isLoading) {
    return (
      <div className="empty-state">
        <svg
          width="48"
          height="48"
          viewBox="0 0 48 48"
          fill="none"
          aria-hidden="true"
        >
          <path
            d="M20 4C11.1634 4 4 11.1634 4 20C4 28.8366 11.1634 36 20 36C24.4183 36 28.5218 34.5 31.7 31.8M20 4C28.8366 4 36 11.1634 36 20C36 28.8366 28.8366 36 20 36"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
          />
          <path
            d="M44 44L35 35"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
          />
        </svg>
        <h2>{t('search:no_results_title')}</h2>
        <p>{t('search:no_results_message')}</p>
      </div>
    )
  }

  if (isLoading && !results) {
    return (
      <div className="results-loading">
        <div className="loading-skeleton">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="skeleton-card">
              <div className="skeleton-line"></div>
              <div className="skeleton-line short"></div>
              <div className="skeleton-line"></div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="search-results-container">
      {results && (
        <>
          {/* Results Info */}
          <div className="results-info">
            <p>
              {t('search:found_results', {
                count: results.total_results,
              })}
            </p>
          </div>

          {/* Multimedia Results */}
          {results.multimedia && results.multimedia.length > 0 && (
            <section className="multimedia-section" aria-label={t('search:aria_multimedia')}>
              <h2>{t('search:images_and_videos')}</h2>
              <div className="multimedia-grid">
                {results.multimedia.map((media, idx) => (
                  <MultimediaResult key={idx} result={media} />
                ))}
              </div>
            </section>
          )}

          {/* Events */}
          {results.events && results.events.length > 0 && (
            <section className="events-section" aria-label={t('search:aria_events')}>
              <h2>{t('search:upcoming_events')}</h2>
              <div className="events-list">
                {results.events.map((event, idx) => (
                  <EventCard key={idx} event={event} />
                ))}
              </div>
            </section>
          )}

          {/* Main Results */}
          <section className="results-section" aria-label={t('search:aria_results')}>
            <div className="results-list">
              {results.results.map((result) => (
                <ResultCard
                  key={result.url}
                  result={result}
                  onFeedback={(isHelpful) => {
                    onResultFeedback?.(result.url, isHelpful)
                  }}
                />
              ))}
            </div>
          </section>

          {/* Pagination */}
          {results.total_results > results.page_size && (
            <Pagination
              currentPage={currentPage}
              totalPages={Math.ceil(results.total_results / results.page_size)}
              onPageChange={onPageChange}
            />
          )}

          {/* Related Queries */}
          <RelatedQueries />

          {/* Cached Indicator */}
          {results.cached && (
            <div className="cached-indicator">
              <svg
                width="16"
                height="16"
                viewBox="0 0 16 16"
                fill="currentColor"
                aria-hidden="true"
              >
                <path d="M8 1C4.134 1 1 4.134 1 8s3.134 7 7 7 7-3.134 7-7-3.134-7-7-7zm0 2c2.757 0 5 2.243 5 5s-2.243 5-5 5-5-2.243-5-5 2.243-5 5-5z" />
              </svg>
              <span>{t('search:from_cache')}</span>
            </div>
          )}
        </>
      )}
    </div>
  )
}
