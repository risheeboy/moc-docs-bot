import { useTranslation } from 'react-i18next'

interface SourceBadgeProps {
  sourceSite: string
  language: string
}

export default function SourceBadge({
  sourceSite,
  language,
}: SourceBadgeProps) {
  const { t } = useTranslation()

  const getSourceLabel = (site: string): string => {
    const siteMap: Record<string, string> = {
      'culture.gov.in': t('sources:culture_ministry'),
      'asi.nic.in': t('sources:asi'),
      'ncert.nic.in': t('sources:ncert'),
      'nift.ac.in': t('sources:nift'),
      'iccr.gov.in': t('sources:iccr'),
    }
    return siteMap[site] || site
  }

  return (
    <span
      className="source-badge"
      title={`${t('search:source')}: ${sourceSite}`}
    >
      {getSourceLabel(sourceSite)}
    </span>
  )
}
