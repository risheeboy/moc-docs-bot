/**
 * SourceCard Component
 * Displays individual source citation with clickable link
 */

import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Source } from '../types'
import { truncateText } from '../utils/markdown'
import '../styles/widget.css'

interface Props {
  source: Source
}

export const SourceCard: React.FC<Props> = ({ source }) => {
  const { t } = useTranslation()
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <div className="source-card">
      <div className="source-header">
        <div className="source-info">
          <h5 className="source-title">{truncateText(source.title, 60)}</h5>
          <p className="source-site">{source.source_site}</p>
          <div className="source-meta">
            <span className="source-type">{source.content_type}</span>
            <span className="source-score">
              {Math.round(source.score * 100)}% match
            </span>
          </div>
        </div>
        <button
          className="source-expand-btn"
          onClick={() => setIsExpanded(!isExpanded)}
          aria-expanded={isExpanded}
          aria-label={`Toggle details for ${source.title}`}
        >
          {isExpanded ? '−' : '+'}
        </button>
      </div>

      {isExpanded && (
        <div className="source-details">
          <p className="source-snippet">{source.snippet}</p>
          {source.published_date && (
            <p className="source-date">
              Published: {new Date(source.published_date).toLocaleDateString()}
            </p>
          )}
          <a
            href={source.url}
            target="_blank"
            rel="noopener noreferrer"
            className="source-link"
            aria-label={`Visit source: ${source.title}`}
          >
            {t('sources.view')} →
          </a>
        </div>
      )}
    </div>
  )
}
