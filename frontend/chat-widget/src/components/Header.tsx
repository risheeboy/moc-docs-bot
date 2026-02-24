/**
 * Header Component
 * GIGW compliant header with emblem, ministry name, and close button
 */

import React from 'react'
import { useTranslation } from 'react-i18next'
import { AccessibilityControls } from './AccessibilityControls'
import '../styles/widget.css'

interface Props {
  onClose: () => void
}

export const Header: React.FC<Props> = ({ onClose }) => {
  const { t, i18n } = useTranslation()
  const isHindi = i18n.language === 'hi'

  return (
    <header className="chat-header" role="banner">
      <div className="header-content">
        <div className="emblem-section">
          {/* Government Emblem */}
          <div className="emblem" aria-label={t('footer.emblem') || 'National Emblem of India'}>
            <svg viewBox="0 0 100 100" width="40" height="40" fill="currentColor">
              <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" strokeWidth="2" />
              <path d="M50 20 L60 40 L80 40 Q50 60 20 40 L40 40 Z" />
            </svg>
          </div>

          <div className="ministry-info">
            <h1 className="ministry-name">
              {isHindi ? t('header.ministry') : t('header.ministry')}
            </h1>
            <p className="government-text">{t('header.gov')}</p>
          </div>
        </div>

        <div className="header-controls">
          <AccessibilityControls />
          <button
            className="close-button"
            onClick={onClose}
            aria-label={t('chat.close') || 'Close chat'}
            title={t('chat.close') || 'Close chat'}
          >
            <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z" />
            </svg>
          </button>
        </div>
      </div>
    </header>
  )
}
