import { useTranslation } from 'react-i18next'
import { SearchResponse } from '../types'
import { apiClient } from '../services/api'
import { useState } from 'react'
import '../styles/search.css'

interface LanguageToggleProps {
  results: SearchResponse | null
  currentLanguage: string
  onLanguageChange: (language: string) => void
  onResultsTranslate?: (translatedResults: SearchResponse) => void
}

const LANGUAGE_OPTIONS = [
  { code: 'en', label: 'English', native: 'English' },
  { code: 'hi', label: 'Hindi', native: 'हिंदी' },
  { code: 'bn', label: 'Bengali', native: 'বাংলা' },
  { code: 'te', label: 'Telugu', native: 'తెలుగు' },
  { code: 'mr', label: 'Marathi', native: 'मराठी' },
  { code: 'ta', label: 'Tamil', native: 'தமிழ்' },
  { code: 'gu', label: 'Gujarati', native: 'ગુજરાતી' },
  { code: 'kn', label: 'Kannada', native: 'ಕನ್ನಡ' },
  { code: 'ml', label: 'Malayalam', native: 'മലയാളം' },
  { code: 'or', label: 'Odia', native: 'ଓଡ଼ିଆ' },
  { code: 'pa', label: 'Punjabi', native: 'ਪੰਜਾਬੀ' },
]

export default function LanguageToggle({
  results,
  currentLanguage,
  onLanguageChange,
  onResultsTranslate,
}: LanguageToggleProps) {
  const { t } = useTranslation()
  const [isTranslating, setIsTranslating] = useState(false)
  const [translateError, setTranslateError] = useState<string | null>(null)

  const handleLanguageChange = async (langCode: string) => {
    if (langCode === currentLanguage) {
      return
    }

    onLanguageChange(langCode)

    // Translate results if available
    if (results && results.results.length > 0) {
      setIsTranslating(true)
      setTranslateError(null)

      try {
        const translatedResults = await Promise.all(
          results.results.map(async (result) => ({
            ...result,
            title: (
              await apiClient.translate({
                text: result.title,
                source_language: result.language || 'en',
                target_language: langCode,
              })
            ).translated_text,
            snippet: (
              await apiClient.translate({
                text: result.snippet,
                source_language: result.language || 'en',
                target_language: langCode,
              })
            ).translated_text,
          }))
        )

        const translatedResponse: SearchResponse = {
          ...results,
          results: translatedResults,
        }

        onResultsTranslate?.(translatedResponse)
      } catch (error) {
        setTranslateError(
          error instanceof Error ? error.message : 'Translation failed'
        )
        console.error('Translation error:', error)
      } finally {
        setIsTranslating(false)
      }
    }
  }

  return (
    <div className="language-toggle-container">
      <div className="language-toggle">
        <label htmlFor="language-select" className="language-label">
          {t('search:language')}:
        </label>
        <select
          id="language-select"
          value={currentLanguage}
          onChange={(e) => handleLanguageChange(e.target.value)}
          disabled={isTranslating}
          className="language-select"
          aria-label={t('search:aria_language_select')}
        >
          {LANGUAGE_OPTIONS.map((lang) => (
            <option key={lang.code} value={lang.code}>
              {lang.native} ({lang.label})
            </option>
          ))}
        </select>

        {isTranslating && (
          <span className="translating-indicator" aria-live="polite">
            {t('search:translating')}...
          </span>
        )}
      </div>

      {translateError && (
        <div className="translate-error" role="alert">
          {translateError}
        </div>
      )}
    </div>
  )
}
