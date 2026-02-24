/**
 * useAccessibility Hook
 * Manages accessibility preferences
 */

import { useState, useCallback, useEffect } from 'react'
import { AccessibilityPreferences } from '../types'

export function useAccessibility() {
  const [preferences, setPreferences] = useState<AccessibilityPreferences>(() => {
    const saved = localStorage.getItem('accessibility_preferences')
    if (saved) {
      try {
        return JSON.parse(saved)
      } catch {
        // Fall through to default
      }
    }

    return {
      font_size: 'normal',
      high_contrast: false,
      reduce_motion: false,
      screen_reader_mode: false
    }
  })

  /**
   * Update preference
   */
  const updatePreference = useCallback(
    <K extends keyof AccessibilityPreferences>(
      key: K,
      value: AccessibilityPreferences[K]
    ) => {
      setPreferences((prev) => ({ ...prev, [key]: value }))
    },
    []
  )

  /**
   * Save to localStorage
   */
  useEffect(() => {
    localStorage.setItem('accessibility_preferences', JSON.stringify(preferences))
  }, [preferences])

  /**
   * Get CSS variables for font size
   */
  const getFontSizeCSS = useCallback(() => {
    const sizes = {
      small: '12px',
      normal: '14px',
      large: '16px',
      xlarge: '18px'
    }
    return sizes[preferences.font_size]
  }, [preferences.font_size])

  /**
   * Get CSS class for contrast
   */
  const getContrastClass = useCallback(() => {
    return preferences.high_contrast ? 'high-contrast' : ''
  }, [preferences.high_contrast])

  /**
   * Check if motion should be reduced
   */
  const shouldReduceMotion = useCallback(() => {
    return preferences.reduce_motion || window.matchMedia('(prefers-reduced-motion: reduce)').matches
  }, [preferences.reduce_motion])

  /**
   * Check if screen reader mode is enabled
   */
  const isScreenReaderMode = useCallback(() => {
    return preferences.screen_reader_mode
  }, [preferences.screen_reader_mode])

  /**
   * Apply accessibility settings to document
   */
  useEffect(() => {
    const root = document.documentElement
    root.style.fontSize = getFontSizeCSS()

    if (preferences.high_contrast) {
      root.classList.add('high-contrast')
    } else {
      root.classList.remove('high-contrast')
    }

    if (preferences.reduce_motion) {
      root.classList.add('reduce-motion')
    } else {
      root.classList.remove('reduce-motion')
    }

    if (preferences.screen_reader_mode) {
      root.setAttribute('aria-label', 'Screen reader mode enabled')
    }
  }, [preferences, getFontSizeCSS])

  return {
    preferences,
    updatePreference,
    getFontSizeCSS,
    getContrastClass,
    shouldReduceMotion,
    isScreenReaderMode
  }
}
