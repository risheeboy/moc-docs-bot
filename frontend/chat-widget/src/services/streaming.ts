/**
 * SSE (Server-Sent Events) Streaming Service
 * Handles streaming responses from the API
 */

export interface StreamEvent {
  type: 'token' | 'sources' | 'complete' | 'error' | 'metadata'
  data: unknown
  timestamp: string
}

export class StreamingService {
  private eventSource: EventSource | null = null

  /**
   * Open a streaming connection and handle events
   */
  openStream(
    url: string,
    requestBody: Record<string, unknown>,
    handlers: {
      onToken?: (token: string) => void
      onSources?: (sources: any[]) => void
      onComplete?: () => void
      onError?: (error: string) => void
      onMetadata?: (data: unknown) => void
    }
  ): void {
    // SSE doesn't support POST directly, so we need to use fetch with response streaming
    this.streamWithFetch(url, requestBody, handlers)
  }

  /**
   * Stream response using fetch
   */
  private streamWithFetch(
    url: string,
    requestBody: Record<string, unknown>,
    handlers: {
      onToken?: (token: string) => void
      onSources?: (sources: any[]) => void
      onComplete?: () => void
      onError?: (error: string) => void
      onMetadata?: (data: unknown) => void
    }
  ): void {
    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream'
      },
      body: JSON.stringify(requestBody)
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }

        const reader = response.body?.getReader()
        if (!reader) {
          handlers.onError?.('No response body')
          return
        }

        this.processStream(reader, handlers)
      })
      .catch((error) => {
        handlers.onError?.(error.message || 'Stream error')
      })
  }

  /**
   * Process streaming data
   */
  private async processStream(
    reader: ReadableStreamDefaultReader<Uint8Array>,
    handlers: {
      onToken?: (token: string) => void
      onSources?: (sources: any[]) => void
      onComplete?: () => void
      onError?: (error: string) => void
      onMetadata?: (data: unknown) => void
    }
  ): Promise<void> {
    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) {
          handlers.onComplete?.()
          break
        }

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              this.handleStreamEvent(data, handlers)
            } catch (e) {
              console.error('Error parsing stream data:', e)
            }
          }
        }
      }
    } catch (error) {
      handlers.onError?.(
        error instanceof Error ? error.message : 'Unknown error'
      )
    } finally {
      reader.releaseLock()
    }
  }

  /**
   * Handle individual stream events
   */
  private handleStreamEvent(
    data: unknown,
    handlers: {
      onToken?: (token: string) => void
      onSources?: (sources: any[]) => void
      onComplete?: () => void
      onError?: (error: string) => void
      onMetadata?: (data: unknown) => void
    }
  ): void {
    if (typeof data !== 'object' || data === null) return

    const event = data as Record<string, unknown>
    const type = event.type as string

    switch (type) {
      case 'token':
        if (typeof event.content === 'string') {
          handlers.onToken?.(event.content)
        }
        break

      case 'sources':
        if (Array.isArray(event.sources)) {
          handlers.onSources?.(event.sources)
        }
        break

      case 'complete':
        handlers.onComplete?.()
        break

      case 'error':
        if (typeof event.message === 'string') {
          handlers.onError?.(event.message)
        }
        break

      case 'metadata':
        handlers.onMetadata?.(event.data)
        break
    }
  }

  /**
   * Close the stream
   */
  closeStream(): void {
    if (this.eventSource) {
      this.eventSource.close()
      this.eventSource = null
    }
  }
}

// Singleton instance
export const streamingService = new StreamingService()
