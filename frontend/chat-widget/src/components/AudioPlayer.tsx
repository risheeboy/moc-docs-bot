/**
 * AudioPlayer Component
 * Play TTS audio responses
 */

import React, { useRef, useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useTTS } from '../hooks/useTTS'
import '../styles/widget.css'

interface Props {
  text: string
  language: string
}

export const AudioPlayer: React.FC<Props> = ({ text, language }) => {
  const { t } = useTranslation()
  const { isPlaying, isSynthesizing, speak, stop } = useTTS()
  const [duration, setDuration] = useState(0)
  const [isVisible, setIsVisible] = useState(true)

  const handlePlay = async () => {
    await speak(text, language as any)
  }

  if (!isVisible) return null

  return (
    <div className="audio-player">
      {isPlaying ? (
        <button
          type="button"
          onClick={stop}
          className="audio-btn playing"
          aria-label={t('audio.stop')}
          title={t('audio.stop')}
        >
          <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
            <rect x="6" y="4" width="4" height="16" />
            <rect x="14" y="4" width="4" height="16" />
          </svg>
        </button>
      ) : (
        <button
          type="button"
          onClick={handlePlay}
          disabled={isSynthesizing}
          className="audio-btn"
          aria-label={t('audio.play')}
          title={t('audio.play')}
        >
          {isSynthesizing ? (
            <svg className="loading-spinner" viewBox="0 0 24 24" width="18" height="18">
              <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" />
            </svg>
          ) : (
            <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
              <polygon points="5 3 19 12 5 21 5 3" />
            </svg>
          )}
        </button>
      )}
    </div>
  )
}
