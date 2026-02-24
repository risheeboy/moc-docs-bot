import { useTranslation } from 'react-i18next'
import { AISummary } from '../types'
import '../styles/search.css'

interface AISummaryPanelProps {
  summary: AISummary | undefined
  isLoading: boolean
}

export default function AISummaryPanel({
  summary,
  isLoading,
}: AISummaryPanelProps) {
  const { t } = useTranslation()

  if (!summary && !isLoading) {
    return null
  }

  return (
    <div
      className="ai-summary-panel"
      role="region"
      aria-label={t('search:aria_ai_answer')}
    >
      <div className="ai-summary-header">
        <svg
          className="ai-icon"
          width="20"
          height="20"
          viewBox="0 0 20 20"
          fill="none"
          aria-hidden="true"
        >
          <path
            d="M10 2C5.58172 2 2 5.58172 2 10C2 14.4183 5.58172 18 10 18C14.4183 18 18 14.4183 18 10C18 5.58172 14.4183 2 10 2Z"
            stroke="currentColor"
            strokeWidth="1.5"
          />
          <path
            d="M10 7V13M7 10H13"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
          />
        </svg>
        <span className="ai-badge">{t('search:ai_overview')}</span>
      </div>

      {isLoading ? (
        <div className="ai-summary-content loading">
          <div className="skeleton-line"></div>
          <div className="skeleton-line short"></div>
          <div className="skeleton-line"></div>
        </div>
      ) : summary ? (
        <div className="ai-summary-content">
          <p className="summary-text">{summary.summary}</p>
          {summary.sources && summary.sources.length > 0 && (
            <div className="summary-sources">
              <p className="sources-label">{t('search:sources')}:</p>
              <ul className="sources-list">
                {summary.sources.map((source, idx) => (
                  <li key={idx}>{source}</li>
                ))}
              </ul>
            </div>
          )}
          {summary.confidence && (
            <div className="confidence-badge">
              {t('search:confidence')}: {Math.round(summary.confidence * 100)}%
            </div>
          )}
        </div>
      ) : null}
    </div>
  )
}
