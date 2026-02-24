/**
 * useVoice Hook
 * Manages voice recording and speech-to-text
 */

import { useState, useCallback } from 'react'
import { LanguageCode } from '../types'
import { audioService } from '../services/audio'
import { apiClient } from '../services/api'

export function useVoice() {
  const [isRecording, setIsRecording] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const [isTranscribing, setIsTranscribing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const recordingInterval = React.useRef<NodeJS.Timeout | null>(null)

  /**
   * Start recording
   */
  const startRecording = useCallback(async () => {
    try {
      setError(null)
      if (!AudioService.isSupported()) {
        throw new Error('Voice input is not supported in your browser')
      }

      await audioService.startRecording()
      setIsRecording(true)
      setRecordingTime(0)

      recordingInterval.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1)
      }, 1000)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to start recording'
      setError(message)
    }
  }, [])

  /**
   * Stop recording
   */
  const stopRecording = useCallback(async (): Promise<Blob | null> => {
    try {
      setIsRecording(false)
      if (recordingInterval.current) {
        clearInterval(recordingInterval.current)
        recordingInterval.current = null
      }

      const audioBlob = await audioService.stopRecording()
      setRecordingTime(0)
      return audioBlob
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to stop recording'
      setError(message)
      return null
    }
  }, [])

  /**
   * Transcribe audio to text
   */
  const transcribeAudio = useCallback(
    async (audioBlob: Blob, language: LanguageCode): Promise<string | null> => {
      try {
        setIsTranscribing(true)
        setError(null)

        const response = await apiClient.transcribeAudio(audioBlob, language)
        return response.text
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to transcribe audio'
        setError(message)
        return null
      } finally {
        setIsTranscribing(false)
      }
    },
    []
  )

  /**
   * Record and transcribe in one step
   */
  const recordAndTranscribe = useCallback(
    async (language: LanguageCode): Promise<string | null> => {
      const audioBlob = await stopRecording()
      if (!audioBlob) return null
      return transcribeAudio(audioBlob, language)
    },
    [stopRecording, transcribeAudio]
  )

  return {
    isRecording,
    recordingTime,
    isTranscribing,
    error,
    startRecording,
    stopRecording,
    transcribeAudio,
    recordAndTranscribe
  }
}

import React from 'react'
import { AudioService } from '../services/audio'
