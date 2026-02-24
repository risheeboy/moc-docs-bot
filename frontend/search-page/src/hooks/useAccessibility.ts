import { useState, useCallback, useEffect } from 'react'

export interface AccessibilitySettings {
  highContrast: boolean
  largeText: boolean
  reduceMotion: boolean
  focusIndicator: boolean
  screenReaderMode: boolean
  dyslexicFont: boolean
}

export function useAccessibility() {
  const [settings, setSettings] = useState<AccessibilitySettings>(() => {
    const saved = localStorage.getItem('a11y-settings')
    return saved ? JSON.parse(saved) : getDefaultSettings()
  })

  function getDefaultSettings(): AccessibilitySettings {
    return {
      highContrast: false,
      largeText: false,
      reduceMotion:
        window.matchMedia('(prefers-reduced-motion: reduce)').matches,
      focusIndicator: true,
      screenReaderMode: false,
      dyslexicFont: false,
    }
  }

  const toggleHighContrast = useCallback(() => {
    setSettings((prev) => ({
      ...prev,
      highContrast: !prev.highContrast,
    }))
  }, [])

  const toggleLargeText = useCallback(() => {
    setSettings((prev) => ({
      ...prev,
      largeText: !prev.largeText,
    }))
  }, [])

  const toggleReduceMotion = useCallback(() => {
    setSettings((prev) => ({
      ...prev,
      reduceMotion: !prev.reduceMotion,
    }))
  }, [])

  const toggleFocusIndicator = useCallback(() => {
    setSettings((prev) => ({
      ...prev,
      focusIndicator: !prev.focusIndicator,
    }))
  }, [])

  const toggleScreenReaderMode = useCallback(() => {
    setSettings((prev) => ({
      ...prev,
      screenReaderMode: !prev.screenReaderMode,
    }))
  }, [])

  const toggleDyslexicFont = useCallback(() => {
    setSettings((prev) => ({
      ...prev,
      dyslexicFont: !prev.dyslexicFont,
    }))
  }, [])

  const resetToDefaults = useCallback(() => {
    setSettings(getDefaultSettings())
  }, [])

  useEffect(() => {
    localStorage.setItem('a11y-settings', JSON.stringify(settings))

    const root = document.documentElement
    if (settings.highContrast) {
      root.classList.add('high-contrast')
    } else {
      root.classList.remove('high-contrast')
    }

    if (settings.largeText) {
      root.classList.add('large-text')
    } else {
      root.classList.remove('large-text')
    }

    if (settings.reduceMotion) {
      root.classList.add('reduce-motion')
    } else {
      root.classList.remove('reduce-motion')
    }

    if (settings.dyslexicFont) {
      root.classList.add('dyslexic-font')
    } else {
      root.classList.remove('dyslexic-font')
    }
  }, [settings])

  return {
    settings,
    toggleHighContrast,
    toggleLargeText,
    toggleReduceMotion,
    toggleFocusIndicator,
    toggleScreenReaderMode,
    toggleDyslexicFont,
    resetToDefaults,
  }
}
