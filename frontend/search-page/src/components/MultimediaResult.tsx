import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { MultimediaResult as MultimediaResultType } from '../types'
import '../styles/search.css'

interface MultimediaResultProps {
  result: MultimediaResultType
}

export default function MultimediaResult({
  result,
}: MultimediaResultProps) {
  const { t } = useTranslation()
  const [isEnlarged, setIsEnlarged] = useState(false)

  const handleClick = () => {
    setIsEnlarged(!isEnlarged)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      handleClick()
    }
  }

  return (
    <div
      className={`multimedia-item ${result.type}`}
      role="region"
      aria-label={`${result.type}: ${result.alt_text}`}
    >
      {result.type === 'image' ? (
        <div className="image-wrapper">
          <img
            src={result.thumbnail_url || result.url}
            alt={result.alt_text}
            onClick={handleClick}
            onKeyDown={handleKeyDown}
            tabIndex={0}
            role="button"
            loading="lazy"
            className={isEnlarged ? 'enlarged' : ''}
          />
          {isEnlarged && (
            <div
              className="media-overlay"
              onClick={() => setIsEnlarged(false)}
              onKeyDown={(e) => {
                if (e.key === 'Escape') {
                  setIsEnlarged(false)
                }
              }}
              role="button"
              tabIndex={0}
              aria-label={t('search:aria_close')}
            >
              <img
                src={result.url}
                alt={result.alt_text}
                className="enlarged-media"
              />
            </div>
          )}
        </div>
      ) : (
        <div className="video-wrapper">
          <video
            controls
            src={result.url}
            poster={result.thumbnail_url}
            className="video-player"
          >
            {t('search:video_not_supported')}
          </video>
        </div>
      )}

      <div className="multimedia-meta">
        <p className="multimedia-alt">{result.alt_text}</p>
        <a
          href={result.url}
          target="_blank"
          rel="noopener noreferrer"
          className="multimedia-source"
        >
          {t('search:view_source')} - {result.source_site}
        </a>
      </div>
    </div>
  )
}
