/**
 * Audio Service
 * Handles recording, playback, and audio-related operations
 */

export class AudioService {
  private mediaRecorder: MediaRecorder | null = null
  private audioChunks: Blob[] = []
  private audioContext: AudioContext | null = null
  private audioElement: HTMLAudioElement | null = null

  /**
   * Check browser audio support
   */
  static isSupported(): boolean {
    return !!(
      navigator.mediaDevices &&
      navigator.mediaDevices.getUserMedia &&
      typeof AudioContext !== 'undefined'
    )
  }

  /**
   * Start recording audio
   */
  async startRecording(): Promise<void> {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

      const mimeType = this.getSupportedMimeType()
      this.mediaRecorder = new MediaRecorder(stream, { mimeType })
      this.audioChunks = []

      this.mediaRecorder.ondataavailable = (event) => {
        this.audioChunks.push(event.data)
      }

      this.mediaRecorder.start()
    } catch (error) {
      if (error instanceof DOMException) {
        if (error.name === 'NotAllowedError') {
          throw new Error('Microphone permission denied')
        } else if (error.name === 'NotFoundError') {
          throw new Error('Microphone not found')
        }
      }
      throw error
    }
  }

  /**
   * Stop recording and return audio blob
   */
  stopRecording(): Promise<Blob> {
    return new Promise((resolve, reject) => {
      if (!this.mediaRecorder) {
        reject(new Error('Recording not started'))
        return
      }

      this.mediaRecorder.onstop = () => {
        const audioBlob = new Blob(this.audioChunks, {
          type: this.mediaRecorder?.mimeType
        })
        this.stopStream()
        resolve(audioBlob)
      }

      this.mediaRecorder.onerror = (error) => {
        reject(error)
      }

      this.mediaRecorder.stop()
    })
  }

  /**
   * Stop the media stream
   */
  private stopStream(): void {
    if (this.mediaRecorder) {
      this.mediaRecorder.stream.getTracks().forEach((track) => {
        track.stop()
      })
    }
  }

  /**
   * Get supported MIME type
   */
  private getSupportedMimeType(): string {
    const types = [
      'audio/webm',
      'audio/webm;codecs=opus',
      'audio/ogg;codecs=opus',
      'audio/mp4'
    ]

    for (const type of types) {
      if (MediaRecorder.isTypeSupported(type)) {
        return type
      }
    }

    return 'audio/webm'
  }

  /**
   * Play audio from blob or URL
   */
  async playAudio(source: Blob | string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        if (!this.audioElement) {
          this.audioElement = new Audio()
        }

        if (source instanceof Blob) {
          const url = URL.createObjectURL(source)
          this.audioElement.src = url
        } else {
          this.audioElement.src = source
        }

        this.audioElement.onended = () => {
          if (source instanceof Blob) {
            URL.revokeObjectURL(this.audioElement!.src)
          }
          resolve()
        }

        this.audioElement.onerror = () => {
          reject(new Error('Failed to play audio'))
        }

        this.audioElement.play().catch(reject)
      } catch (error) {
        reject(error)
      }
    })
  }

  /**
   * Stop audio playback
   */
  stopAudio(): void {
    if (this.audioElement) {
      this.audioElement.pause()
      this.audioElement.currentTime = 0
    }
  }

  /**
   * Get recording duration
   */
  getRecordingDuration(): number {
    if (this.mediaRecorder) {
      return this.mediaRecorder.state === 'recording'
        ? Date.now() - (this.mediaRecorder.startTime || 0)
        : 0
    }
    return 0
  }

  /**
   * Check if currently recording
   */
  isRecording(): boolean {
    return this.mediaRecorder?.state === 'recording'
  }

  /**
   * Check if currently playing
   */
  isPlaying(): boolean {
    return this.audioElement ? !this.audioElement.paused : false
  }

  /**
   * Convert blob to WAV format
   */
  async blobToWav(blob: Blob): Promise<Blob> {
    const arrayBuffer = await blob.arrayBuffer()
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer)

    const numberOfChannels = audioBuffer.numberOfChannels
    const sampleRate = audioBuffer.sampleRate
    const format = 1 // PCM
    const bitDepth = 16

    const bytesPerSample = bitDepth / 8
    const blockAlign = numberOfChannels * bytesPerSample

    const framesToEncode = audioBuffer.length
    const byteRate = sampleRate * blockAlign

    const headerSize = 44
    const fileSize = headerSize + framesToEncode * blockAlign

    const arrayBuffer2 = new ArrayBuffer(fileSize)
    const view = new DataView(arrayBuffer2)

    const channels: Float32Array[] = []
    for (let i = 0; i < numberOfChannels; i++) {
      channels.push(audioBuffer.getChannelData(i))
    }

    // WAV header
    const writeString = (offset: number, string: string) => {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i))
      }
    }

    writeString(0, 'RIFF')
    view.setUint32(4, fileSize - 8, true)
    writeString(8, 'WAVE')
    writeString(12, 'fmt ')
    view.setUint32(16, 16, true)
    view.setUint16(20, format, true)
    view.setUint16(22, numberOfChannels, true)
    view.setUint32(24, sampleRate, true)
    view.setUint32(28, byteRate, true)
    view.setUint16(32, blockAlign, true)
    view.setUint16(34, bitDepth, true)
    writeString(36, 'data')
    view.setUint32(40, framesToEncode * blockAlign, true)

    // PCM data
    const offset = 44
    const volume = 0.8
    let index = 0
    const volume32Bit = volume
    for (let i = 0; i < framesToEncode; i++) {
      for (let channel = 0; channel < numberOfChannels; channel++) {
        const s = Math.max(-1, Math.min(1, channels[channel][i]))
        view.setInt16(
          offset + index,
          s < 0 ? s * 0x8000 : s * 0x7fff,
          true
        )
        index += 2
      }
    }

    return new Blob([arrayBuffer2], { type: 'audio/wav' })
  }

  /**
   * Get audio duration from blob
   */
  async getAudioDuration(blob: Blob): Promise<number> {
    return new Promise((resolve, reject) => {
      const url = URL.createObjectURL(blob)
      const audio = new Audio()

      audio.onloadedmetadata = () => {
        URL.revokeObjectURL(url)
        resolve(audio.duration)
      }

      audio.onerror = () => {
        URL.revokeObjectURL(url)
        reject(new Error('Failed to load audio'))
      }

      audio.src = url
    })
  }
}

// Singleton instance
export const audioService = new AudioService()
