import { useTranslation } from 'react-i18next'
import '../styles/search.css'

interface RelatedQueriesProps {
  queries?: string[]
  onQuerySelect?: (query: string) => void
}

export default function RelatedQueries({
  queries,
  onQuerySelect,
}: RelatedQueriesProps) {
  const { t } = useTranslation()

  // Default related queries
  const defaultQueries = [
    t('search:related_query_1'),
    t('search:related_query_2'),
    t('search:related_query_3'),
  ].filter(Boolean)

  const displayQueries = queries || defaultQueries

  if (!displayQueries.length) {
    return null
  }

  return (
    <div className="related-queries-section">
      <h3>{t('search:people_also_searched')}</h3>
      <div className="related-queries-list">
        {displayQueries.map((query, idx) => (
          <button
            key={idx}
            className="related-query-button"
            onClick={() => onQuerySelect?.(query)}
            type="button"
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              aria-hidden="true"
            >
              <circle cx="6" cy="6" r="4" stroke="currentColor" strokeWidth="1" />
              <path d="M10 10L13 13" stroke="currentColor" strokeWidth="1" strokeLinecap="round" />
            </svg>
            {query}
          </button>
        ))}
      </div>
    </div>
  )
}
