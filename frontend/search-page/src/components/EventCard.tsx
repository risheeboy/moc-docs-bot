import { useTranslation } from 'react-i18next'
import { EventResult } from '../types'
import '../styles/search.css'

interface EventCardProps {
  event: EventResult
}

export default function EventCard({ event }: EventCardProps) {
  const { t, i18n } = useTranslation()

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat(i18n.language, {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      weekday: 'long',
    }).format(date)
  }

  return (
    <article className="event-card">
      <div className="event-icon" aria-hidden="true">
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
        >
          <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
          <line x1="16" y1="2" x2="16" y2="6" />
          <line x1="8" y1="2" x2="8" y2="6" />
          <line x1="3" y1="10" x2="21" y2="10" />
        </svg>
      </div>

      <div className="event-content">
        <h3 className="event-title">{event.title}</h3>

        <div className="event-details">
          <div className="event-date">
            <svg
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              aria-hidden="true"
            >
              <path
                d="M2 4V14C2 14.5523 2.44772 15 3 15H13C13.5523 15 14 14.5523 14 14V4M2 4C2 3.44772 2.44772 3 3 3H13C13.5523 3 14 3.44772 14 4M2 4H14M5 7H11M5 10H11"
                stroke="currentColor"
                strokeWidth="1"
                strokeLinecap="round"
              />
            </svg>
            <time dateTime={event.date}>{formatDate(event.date)}</time>
          </div>

          <div className="event-venue">
            <svg
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              aria-hidden="true"
            >
              <path
                d="M8 1C4.686 1 2 3.686 2 7C2 11 8 15 8 15S14 11 14 7C14 3.686 11.314 1 8 1Z"
                stroke="currentColor"
                strokeWidth="1"
              />
              <circle cx="8" cy="7" r="1.5" fill="currentColor" />
            </svg>
            <span>{event.venue}</span>
          </div>
        </div>

        <p className="event-description">{event.description}</p>

        <a
          href={event.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="event-link"
        >
          {t('search:learn_more')} →
        </a>
      </div>
    </article>
  )
}
