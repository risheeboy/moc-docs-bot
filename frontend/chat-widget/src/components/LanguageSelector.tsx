/**
 * LanguageSelector Component
 * Dropdown to switch between languages
 */

import React from 'react'
import { useTranslation } from 'react-i18next'
import { LanguageCode } from '../types'
import { SUPPORTED_LANGUAGES } from '../utils/constants'
import '../styles/widget.css'

interface Props {
  currentLanguage: LanguageCode
  onLanguageChange: (language: LanguageCode) => void
}

export const LanguageSelector: React.FC<Props> = ({
  currentLanguage,
  onLanguageChange
}) => {
  const { t } = useTranslation()

  return (
    <div className="language-selector">
      <label htmlFor="language-select">{t('language.select')}:</label>
      <select
        id="language-select"
        value={currentLanguage}
        onChange={(e) => onLanguageChange(e.target.value as LanguageCode)}
        aria-label={t('language.select')}
        className="language-dropdown"
      >
        {SUPPORTED_LANGUAGES.map((lang) => (
          <option key={lang.code} value={lang.code}>
            {lang.label}
          </option>
        ))}
      </select>
    </div>
  )
}
