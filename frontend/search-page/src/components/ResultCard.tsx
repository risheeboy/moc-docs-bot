import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { SearchResult } from '../types'
import SourceBadge from './SourceBadge'
import '../styles/search.css'

interface ResultCardProps {
  result: SearchResult
  onFeedback?: (isHelpful: boolean) => void
}

export default function ResultCard({ result, onFeedback }: ResultCardProps) {
  const { t, i18n } = useTranslation()
  const [showFeedback, setShowFeedback] = useState(false)
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false)

  const handleFeedback = (isHelpful: boolean) => {
    onFeedback?.(isHelpful)
    setFeedbackSubmitted(true)
    setTimeout(() => {
      setShowFeedback(false)
      setFeedbackSubmitted(false)
    }, 2000)
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return null
    const date = new Date(dateString)
    return new Intl.DateTimeFormat(i18n.language, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    }).format(date)
  }

  return (
    <article className="result-card" role="article">
      {result.thumbnail_url && (
        <div className="result-thumbnail">
          <img
            src={result.thumbnail_url}
            alt={result.title}
            loading="lazy"
            onError={(e) => {
              e.currentTarget.style.display = 'none'
            }}
          />
        </div>
      )}

      <div className="result-content">
        <h3 className="result-title">
          <a
            href={result.url}
            target="_blank"
            rel="noopener noreferrer"
            className="result-link"
          >
            {result.title}
          </a>
        </h3>

        <div className="result-meta">
          <SourceBadge
            sourceSite={result.source_site}
            language={result.language}
          />
          {result.content_type && (
            <span className="content-type-badge">{result.content_type}</span>
          )}
          {result.published_date && (
            <time className="published-date">
              {formatDate(result.published_date)}
            </time>
          )}
        </div>

        <p className="result-snippet">{result.snippet}</p>

        <div className="result-footer">
          <a
            href={result.url}
            target="_blank"
            rel="noopener noreferrer"
            className="result-url"
          >
            {result.url.replace(/^https?:\/\//, '')}
          </a>

          <div className="result-actions">
            <div className="feedback-widget">
              {feedbackSubmitted ? (
                <span className="feedback-thanks">
                  {t('search:thanks')}
                </span>
              ) : (
                <>
                  <button
                    type="button"
                    onClick={() => setShowFeedback(!showFeedback)}
                    className="feedback-toggle"
                    aria-label={t('search:aria_feedback')}
                    title={t('search:was_helpful')}
                  >
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 16 16"
                      fill="none"
                      aria-hidden="true"
                    >
                      <path
                        d="M1.5 8.5L3 7V2C3 1.44772 3.44772 1 4 1H12C12.5523 1 13 1.44772 13 2V7L14.5 8.5"
                        stroke="currentColor"
                        strokeWidth="1"
                      />
                    </svg>
                  </button>

                  {showFeedback && (
                    <div className="feedback-options">
                      <button
                        type="button"
                        onClick={() => handleFeedback(true)}
                        className="feedback-button helpful"
                        aria-label={t('search:aria_helpful')}
                      >
                        👍
                      </button>
                      <button
                        type="button"
                        onClick={() => handleFeedback(false)}
                        className="feedback-button unhelpful"
                        aria-label={t('search:aria_not_helpful')}
                      >
                        👎
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </article>
  )
}
