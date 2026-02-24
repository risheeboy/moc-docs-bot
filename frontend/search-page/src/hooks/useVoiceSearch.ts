import { useState, useRef, useCallback } from 'react'
import { AudioRecorder, transcribeAudio } from '../services/audio'

export interface VoiceSearchState {
  isListening: boolean
  isProcessing: boolean
  error: string | null
  transcript: string
}

export function useVoiceSearch() {
  const [state, setState] = useState<VoiceSearchState>({
    isListening: false,
    isProcessing: false,
    error: null,
    transcript: '',
  })

  const recorderRef = useRef<AudioRecorder | null>(null)

  const startListening = useCallback(async (language: string = 'auto') => {
    setState((prev) => ({ ...prev, error: null, isListening: true }))

    try {
      recorderRef.current = new AudioRecorder()
      await recorderRef.current.startRecording()
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'Failed to start recording'
      setState((prev) => ({
        ...prev,
        error: message,
        isListening: false,
      }))
    }
  }, [])

  const stopListening = useCallback(async (language: string = 'auto') => {
    if (!recorderRef.current) {
      return ''
    }

    setState((prev) => ({
      ...prev,
      isListening: false,
      isProcessing: true,
    }))

    try {
      const audioBlob = await recorderRef.current.stopRecording()
      const result = await transcribeAudio(audioBlob, language)

      setState((prev) => ({
        ...prev,
        transcript: result.text,
        error: null,
        isProcessing: false,
      }))

      return result.text
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : 'Failed to transcribe audio'
      setState((prev) => ({
        ...prev,
        error: message,
        isProcessing: false,
      }))
      return ''
    } finally {
      recorderRef.current = null
    }
  }, [])

  const cancelListening = useCallback(() => {
    if (recorderRef.current?.isRecording()) {
      recorderRef.current = null
    }
    setState((prev) => ({
      ...prev,
      isListening: false,
      isProcessing: false,
      error: null,
    }))
  }, [])

  const clearTranscript = useCallback(() => {
    setState((prev) => ({
      ...prev,
      transcript: '',
    }))
  }, [])

  return {
    ...state,
    startListening,
    stopListening,
    cancelListening,
    clearTranscript,
  }
}
