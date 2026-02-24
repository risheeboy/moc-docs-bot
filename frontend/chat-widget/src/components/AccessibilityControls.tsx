/**
 * AccessibilityControls Component
 * Font size, contrast, and other accessibility settings
 */

import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useAccessibility } from '../hooks/useAccessibility'
import '../styles/accessibility.css'

export const AccessibilityControls: React.FC = () => {
  const { t } = useTranslation()
  const { preferences, updatePreference } = useAccessibility()
  const [isOpen, setIsOpen] = useState(false)

  const fontSizes = ['small', 'normal', 'large', 'xlarge'] as const

  return (
    <div className="accessibility-controls">
      <button
        className="accessibility-toggle"
        onClick={() => setIsOpen(!isOpen)}
        aria-label={t('accessibility.menu') || 'Accessibility menu'}
        aria-expanded={isOpen}
      >
        <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
          <circle cx="12" cy="8" r="1" />
          <circle cx="12" cy="12" r="1" />
          <circle cx="12" cy="16" r="1" />
        </svg>
      </button>

      {isOpen && (
        <div className="accessibility-menu" role="dialog" aria-label="Accessibility options">
          <div className="accessibility-option">
            <label>{t('accessibility.font_size')}</label>
            <div className="font-size-buttons">
              {fontSizes.map((size) => (
                <button
                  key={size}
                  className={`size-btn ${preferences.font_size === size ? 'active' : ''}`}
                  onClick={() => updatePreference('font_size', size)}
                  style={{
                    fontSize: size === 'small' ? '12px' : size === 'normal' ? '14px' : size === 'large' ? '16px' : '18px'
                  }}
                >
                  A
                </button>
              ))}
            </div>
          </div>

          <div className="accessibility-option">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={preferences.high_contrast}
                onChange={(e) => updatePreference('high_contrast', e.target.checked)}
              />
              <span>{t('accessibility.high_contrast')}</span>
            </label>
          </div>

          <div className="accessibility-option">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={preferences.screen_reader_mode}
                onChange={(e) => updatePreference('screen_reader_mode', e.target.checked)}
              />
              <span>{t('accessibility.screen_reader')}</span>
            </label>
          </div>
        </div>
      )}
    </div>
  )
}
