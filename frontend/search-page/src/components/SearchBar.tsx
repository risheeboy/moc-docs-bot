import { useState, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import VoiceSearchButton from './VoiceSearchButton'
import '../styles/search.css'

interface SearchBarProps {
  query: string
  isLoading: boolean
  onQueryChange: (query: string) => void
  onSubmit: (query: string) => void
  onVoiceInput?: (transcript: string) => void
}

export default function SearchBar({
  query,
  isLoading,
  onQueryChange,
  onSubmit,
  onVoiceInput,
}: SearchBarProps) {
  const { t } = useTranslation()
  const [isFocused, setIsFocused] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      onSubmit(query)
    }
  }

  const handleVoiceInput = (transcript: string) => {
    onQueryChange(transcript)
    if (onVoiceInput) {
      onVoiceInput(transcript)
    }
  }

  const handleClearQuery = () => {
    onQueryChange('')
    inputRef.current?.focus()
  }

  return (
    <div className="search-bar-container">
      <form onSubmit={handleSubmit} className="search-form">
        <div
          className={`search-bar ${isFocused ? 'focused' : ''} ${isLoading ? 'loading' : ''}`}
          role="search"
        >
          <svg
            className="search-icon"
            width="20"
            height="20"
            viewBox="0 0 20 20"
            fill="none"
            aria-hidden="true"
          >
            <path
              d="M9 17C13.4183 17 17 13.4183 17 9C17 4.58172 13.4183 1 9 1C4.58172 1 1 4.58172 1 9C1 13.4183 4.58172 17 9 17Z"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M19 19L14.65 14.65"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>

          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder={t('search:placeholder')}
            className="search-input"
            disabled={isLoading}
            aria-label={t('search:aria_search_input')}
            autoComplete="off"
          />

          {query && (
            <button
              type="button"
              onClick={handleClearQuery}
              className="clear-button"
              aria-label={t('search:aria_clear')}
              title={t('search:clear')}
            >
              <svg
                width="20"
                height="20"
                viewBox="0 0 20 20"
                fill="none"
                aria-hidden="true"
              >
                <path
                  d="M15 5L5 15M5 5L15 15"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </button>
          )}

          <VoiceSearchButton
            onTranscript={handleVoiceInput}
            language="auto"
          />

          <button
            type="submit"
            className="search-button"
            disabled={isLoading || !query.trim()}
            aria-label={t('search:aria_search_button')}
          >
            {isLoading ? (
              <span className="spinner" aria-hidden="true"></span>
            ) : (
              t('search:search')
            )}
          </button>
        </div>
      </form>

      <p className="search-hint">{t('search:hint')}</p>
    </div>
  )
}
