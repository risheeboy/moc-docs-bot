/**
 * VoiceButton Component
 * Voice recording and speech-to-text
 */

import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useVoice } from '../hooks/useVoice'
import { LanguageCode } from '../types'
import '../styles/widget.css'

interface Props {
  onTranscription: (text: string) => void
  language: LanguageCode
  disabled?: boolean
}

export const VoiceButton: React.FC<Props> = ({
  onTranscription,
  language,
  disabled = false
}) => {
  const { t } = useTranslation()
  const { isRecording, recordingTime, error, startRecording, recordAndTranscribe } =
    useVoice()
  const [isProcessing, setIsProcessing] = useState(false)

  const handleVoiceClick = async () => {
    if (isRecording) {
      setIsProcessing(true)
      const text = await recordAndTranscribe(language)
      setIsProcessing(false)
      if (text) {
        onTranscription(text)
      }
    } else {
      await startRecording()
    }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="voice-button-wrapper">
      <button
        type="button"
        onClick={handleVoiceClick}
        disabled={disabled || isProcessing}
        aria-label={isRecording ? t('chat.listening') : t('chat.voice_input')}
        className={`voice-button ${isRecording ? 'recording' : ''}`}
        title={isRecording ? t('chat.listening') : t('chat.voice_input')}
      >
        {isRecording ? (
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <circle cx="12" cy="12" r="8" fill="currentColor" />
          </svg>
        ) : (
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M12 15c1.66 0 3-1.34 3-3V6c0-1.66-1.34-3-3-3S9 4.34 9 6v6c0 1.66 1.34 3 3 3z" />
            <path d="M17 16.91c-1.48 1.46-3.51 2.36-5.77 2.36-2.26 0-4.29-.9-5.77-2.36M19 12h2c0 2.04-.78 3.89-2.05 5.28M5 12H3c0-2.04.78-3.89 2.05-5.28" />
          </svg>
        )}
      </button>

      {isRecording && (
        <div className="recording-indicator">
          <span className="pulse" />
          <span className="time">{formatTime(recordingTime)}</span>
        </div>
      )}

      {isProcessing && (
        <div className="processing-indicator" aria-live="polite">
          {t('chat.processing')}
        </div>
      )}

      {error && (
        <div className="voice-error" role="alert">
          {error}
        </div>
      )}
    </div>
  )
}
