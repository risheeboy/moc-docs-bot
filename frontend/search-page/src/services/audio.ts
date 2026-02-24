const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export interface AudioRecorderOptions {
  sampleRate?: number
  channelCount?: number
}

export class AudioRecorder {
  private mediaRecorder: MediaRecorder | null = null
  private audioChunks: Blob[] = []
  private stream: MediaStream | null = null

  async startRecording(options?: AudioRecorderOptions): Promise<void> {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: options?.sampleRate || 16000,
          channelCount: options?.channelCount || 1,
        },
      })

      this.mediaRecorder = new MediaRecorder(this.stream, {
        mimeType: 'audio/webm;codecs=opus',
      })

      this.audioChunks = []

      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data)
        }
      }

      this.mediaRecorder.start()
    } catch (error) {
      console.error('Failed to start audio recording:', error)
      throw error
    }
  }

  async stopRecording(): Promise<Blob> {
    return new Promise((resolve, reject) => {
      if (!this.mediaRecorder) {
        reject(new Error('No recording in progress'))
        return
      }

      this.mediaRecorder.onstop = () => {
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' })
        this.cleanup()
        resolve(audioBlob)
      }

      this.mediaRecorder.onerror = (event) => {
        this.cleanup()
        reject(event.error)
      }

      this.mediaRecorder.stop()
    })
  }

  private cleanup(): void {
    if (this.stream) {
      this.stream.getTracks().forEach((track) => track.stop())
    }
    this.mediaRecorder = null
    this.stream = null
    this.audioChunks = []
  }

  isRecording(): boolean {
    return this.mediaRecorder?.state === 'recording'
  }
}

export async function transcribeAudio(
  audioBlob: Blob,
  language: string = 'auto'
): Promise<{ text: string; language: string; confidence: number }> {
  const formData = new FormData()
  formData.append('audio', audioBlob)
  formData.append('language', language)

  const response = await fetch(`${API_BASE_URL}/speech/stt`, {
    method: 'POST',
    body: formData,
    headers: {
      'X-Request-ID': `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    },
  })

  if (!response.ok) {
    throw new Error('Failed to transcribe audio')
  }

  return response.json()
}

export async function synthesizeSpeech(
  text: string,
  language: string
): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/speech/tts`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Request-ID': `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    },
    body: JSON.stringify({
      text: text,
      language: language,
      format: 'mp3',
      voice: 'default',
    }),
  })

  if (!response.ok) {
    throw new Error('Failed to synthesize speech')
  }

  return response.blob()
}
