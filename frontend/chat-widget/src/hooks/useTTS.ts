/**
 * useTTS Hook
 * Manages text-to-speech playback
 */

import { useState, useCallback } from 'react'
import { LanguageCode } from '../types'
import { audioService } from '../services/audio'
import { apiClient } from '../services/api'

export function useTTS() {
  const [isPlaying, setIsPlaying] = useState(false)
  const [isSynthesizing, setIsSynthesizing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [duration, setDuration] = useState(0)

  /**
   * Synthesize and play text
   */
  const speak = useCallback(
    async (text: string, language: LanguageCode) => {
      try {
        setIsSynthesizing(true)
        setError(null)

        const audioBlob = await apiClient.synthesizeSpeech(text, language)
        const duration = await audioService.getAudioDuration(audioBlob)
        setDuration(duration)

        setIsPlaying(true)
        await audioService.playAudio(audioBlob)
        setIsPlaying(false)
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to synthesize speech'
        setError(message)
        setIsPlaying(false)
      } finally {
        setIsSynthesizing(false)
      }
    },
    []
  )

  /**
   * Stop playback
   */
  const stop = useCallback(() => {
    audioService.stopAudio()
    setIsPlaying(false)
  }, [])

  /**
   * Play audio from blob
   */
  const playAudio = useCallback(async (audioBlob: Blob) => {
    try {
      setIsPlaying(true)
      setError(null)

      const duration = await audioService.getAudioDuration(audioBlob)
      setDuration(duration)

      await audioService.playAudio(audioBlob)
      setIsPlaying(false)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to play audio'
      setError(message)
      setIsPlaying(false)
    }
  }, [])

  return {
    isPlaying,
    isSynthesizing,
    error,
    duration,
    speak,
    stop,
    playAudio
  }
}
