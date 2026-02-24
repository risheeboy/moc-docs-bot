import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useVoiceSearch } from '../hooks/useVoiceSearch'
import '../styles/search.css'

interface VoiceSearchButtonProps {
  onTranscript: (text: string) => void
  language: string
}

export default function VoiceSearchButton({
  onTranscript,
  language,
}: VoiceSearchButtonProps) {
  const { t } = useTranslation()
  const {
    isListening,
    isProcessing,
    error,
    transcript,
    startListening,
    stopListening,
    cancelListening,
  } = useVoiceSearch()

  useEffect(() => {
    if (transcript) {
      onTranscript(transcript)
    }
  }, [transcript, onTranscript])

  const handleClick = async () => {
    if (isListening) {
      await stopListening(language)
    } else {
      await startListening(language)
    }
  }

  const handleCancel = () => {
    cancelListening()
  }

  if (!('mediaDevices' in navigator)) {
    return null
  }

  return (
    <div className="voice-search-wrapper">
      <button
        type="button"
        onClick={handleClick}
        className={`voice-button ${isListening ? 'active' : ''} ${isProcessing ? 'processing' : ''}`}
        aria-pressed={isListening}
        aria-label={
          isListening
            ? t('search:aria_stop_listening')
            : t('search:aria_start_listening')
        }
        disabled={isProcessing}
        title={isListening ? t('search:stop_listening') : t('search:start_listening')}
      >
        <svg
          width="20"
          height="20"
          viewBox="0 0 20 20"
          fill="currentColor"
          aria-hidden="true"
        >
          <path d="M10 1C8.34315 1 7 2.34315 7 4V10C7 11.6569 8.34315 13 10 13C11.6569 13 13 11.6569 13 10V4C13 2.34315 11.6569 1 10 1Z" />
          <path d="M5 10C5 10.5523 4.55228 11 4 11C3.44772 11 3 10.5523 3 10C3 6.13401 6.13401 3 10 3C13.866 3 17 6.13401 17 10C17 10.5523 16.5523 11 16 11C15.4477 11 15 10.5523 15 10C15 7.23858 12.7614 5 10 5C7.23858 5 5 7.23858 5 10Z" />
          <path d="M10 14C10.5523 14 11 14.4477 11 15V18C11 18.5523 10.5523 19 10 19C9.44772 19 9 18.5523 9 18V15C9 14.4477 9.44772 14 10 14Z" />
        </svg>
      </button>

      {isListening && (
        <button
          type="button"
          onClick={handleCancel}
          className="cancel-listening-button"
          aria-label={t('search:aria_cancel')}
        >
          {t('search:cancel')}
        </button>
      )}

      {error && (
        <div className="voice-error" role="alert">
          {error}
        </div>
      )}
    </div>
  )
}
