/**
 * Vitest Setup
 * Global test configuration
 */

import '@testing-library/jest-dom'
import { afterEach, beforeAll, afterAll, vi } from 'vitest'
import { cleanup } from '@testing-library/react'

// Cleanup after each test
afterEach(() => {
  cleanup()
})

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn()
  }))
})

// Mock scrollIntoView
Element.prototype.scrollIntoView = vi.fn()

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
}
global.localStorage = localStorageMock as any

// Mock AudioContext
class MockAudioContext {
  createMediaStreamSource = vi.fn()
  decodeAudioData = vi.fn()
  createGain = vi.fn()
  get destination() {
    return {}
  }
}

global.AudioContext = MockAudioContext as any
;(global as any).webkitAudioContext = MockAudioContext

// Mock MediaRecorder
class MockMediaRecorder {
  state = 'inactive'
  mimeType = 'audio/webm'
  stream: any
  ondataavailable: ((event: any) => void) | null = null
  onstop: (() => void) | null = null
  onerror: (() => void) | null = null
  startTime: number = 0

  constructor(stream: any) {
    this.stream = stream
  }

  start() {
    this.state = 'recording'
  }

  stop() {
    this.state = 'inactive'
  }

  static isTypeSupported(type: string) {
    return ['audio/webm', 'audio/ogg;codecs=opus'].includes(type)
  }
}

global.MediaRecorder = MockMediaRecorder as any

// Mock navigator.mediaDevices
Object.defineProperty(global.navigator, 'mediaDevices', {
  value: {
    getUserMedia: vi.fn().mockResolvedValue({
      getTracks: () => [{ stop: vi.fn() }]
    })
  }
})

// Mock IntersectionObserver
class MockIntersectionObserver {
  constructor(public callback: any) {}
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()
}
;(global as any).IntersectionObserver = MockIntersectionObserver

// Suppress console errors in tests (optional)
const originalError = console.error
beforeAll(() => {
  console.error = vi.fn((...args) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning: ReactDOM.render')
    ) {
      return
    }
    originalError.call(console, ...args)
  })
})

afterAll(() => {
  console.error = originalError
})
