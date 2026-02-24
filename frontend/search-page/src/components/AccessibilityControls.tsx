import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useAccessibility } from '../hooks/useAccessibility'
import '../styles/accessibility.css'

export default function AccessibilityControls() {
  const { t } = useTranslation()
  const [showPanel, setShowPanel] = useState(false)
  const {
    settings,
    toggleHighContrast,
    toggleLargeText,
    toggleReduceMotion,
    toggleScreenReaderMode,
    toggleDyslexicFont,
    resetToDefaults,
  } = useAccessibility()

  return (
    <>
      <button
        className="a11y-toggle-button"
        onClick={() => setShowPanel(!showPanel)}
        aria-expanded={showPanel}
        aria-label={t('search:aria_accessibility')}
        title={t('search:accessibility_options')}
      >
        <svg
          width="20"
          height="20"
          viewBox="0 0 20 20"
          fill="currentColor"
          aria-hidden="true"
        >
          <path d="M10 2C5.58172 2 2 5.58172 2 10C2 14.4183 5.58172 18 10 18C14.4183 18 18 14.4183 18 10C18 5.58172 14.4183 2 10 2ZM10 4C13.3137 4 16 6.68629 16 10C16 13.3137 13.3137 16 10 16C6.68629 16 4 13.3137 4 10C4 6.68629 6.68629 4 10 4Z" />
          <path d="M10 7C9.44772 7 9 7.44772 9 8C9 8.55228 9.44772 9 10 9C10.5523 9 11 8.55228 11 8C11 7.44772 10.5523 7 10 7Z" />
          <path d="M9 11C8.44772 11 8 11.4477 8 12V14C8 14.5523 8.44772 15 9 15H11C11.5523 15 12 14.5523 12 14V12C12 11.4477 11.5523 11 11 11H9Z" />
        </svg>
        <span className="a11y-count">
          {Object.values(settings).filter(Boolean).length}
        </span>
      </button>

      {showPanel && (
        <div
          className="a11y-panel"
          role="region"
          aria-label={t('search:aria_accessibility_panel')}
        >
          <div className="a11y-panel-header">
            <h2>{t('search:accessibility_settings')}</h2>
            <button
              type="button"
              onClick={() => setShowPanel(false)}
              aria-label={t('search:aria_close')}
              className="a11y-close"
            >
              ✕
            </button>
          </div>

          <div className="a11y-settings">
            <label className="a11y-setting">
              <input
                type="checkbox"
                checked={settings.highContrast}
                onChange={toggleHighContrast}
              />
              <span>{t('search:high_contrast')}</span>
            </label>

            <label className="a11y-setting">
              <input
                type="checkbox"
                checked={settings.largeText}
                onChange={toggleLargeText}
              />
              <span>{t('search:large_text')}</span>
            </label>

            <label className="a11y-setting">
              <input
                type="checkbox"
                checked={settings.reduceMotion}
                onChange={toggleReduceMotion}
              />
              <span>{t('search:reduce_motion')}</span>
            </label>

            <label className="a11y-setting">
              <input
                type="checkbox"
                checked={settings.screenReaderMode}
                onChange={toggleScreenReaderMode}
              />
              <span>{t('search:screen_reader_mode')}</span>
            </label>

            <label className="a11y-setting">
              <input
                type="checkbox"
                checked={settings.dyslexicFont}
                onChange={toggleDyslexicFont}
              />
              <span>{t('search:dyslexic_font')}</span>
            </label>
          </div>

          <button
            type="button"
            onClick={resetToDefaults}
            className="a11y-reset-button"
          >
            {t('search:reset_defaults')}
          </button>
        </div>
      )}
    </>
  )
}
