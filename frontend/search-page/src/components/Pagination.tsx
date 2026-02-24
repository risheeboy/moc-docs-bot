import { useTranslation } from 'react-i18next'
import '../styles/search.css'

interface PaginationProps {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
}

export default function Pagination({
  currentPage,
  totalPages,
  onPageChange,
}: PaginationProps) {
  const { t } = useTranslation()

  if (totalPages <= 1) {
    return null
  }

  const getPageNumbers = () => {
    const delta = 2
    const left = currentPage - delta
    const right = currentPage + delta + 1
    const range: (number | string)[] = []
    const rangeWithDots: (number | string)[] = []
    let l: number | string

    for (let i = 1; i <= totalPages; i++) {
      if (i === 1 || i === totalPages || (i >= left && i < right)) {
        range.push(i)
      }
    }

    range.forEach((i) => {
      if (l) {
        if (i - (l as number) === 2) {
          rangeWithDots.push((l as number) + 1)
        } else if (i - (l as number) !== 1) {
          rangeWithDots.push('...')
        }
      }
      rangeWithDots.push(i)
      l = i
    })

    return rangeWithDots
  }

  const handlePageClick = (page: number) => {
    if (page !== currentPage) {
      onPageChange(page)
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }

  return (
    <nav
      className="pagination"
      aria-label={t('search:aria_pagination')}
    >
      <button
        onClick={() => handlePageClick(currentPage - 1)}
        disabled={currentPage === 1}
        className="pagination-button prev"
        aria-label={t('search:previous_page')}
      >
        ← {t('search:previous')}
      </button>

      <div className="pagination-numbers">
        {getPageNumbers().map((page, idx) => (
          <div key={idx}>
            {page === '...' ? (
              <span className="pagination-ellipsis">...</span>
            ) : (
              <button
                onClick={() => handlePageClick(page as number)}
                className={`pagination-number ${
                  page === currentPage ? 'active' : ''
                }`}
                aria-label={t('search:page_number', { number: page })}
                aria-current={page === currentPage ? 'page' : undefined}
              >
                {page}
              </button>
            )}
          </div>
        ))}
      </div>

      <button
        onClick={() => handlePageClick(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="pagination-button next"
        aria-label={t('search:next_page')}
      >
        {t('search:next')} →
      </button>
    </nav>
  )
}
