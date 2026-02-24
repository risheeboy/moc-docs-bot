import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import SearchPage from '../src/pages/SearchPage'

// Mock i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: {
      language: 'en',
      changeLanguage: vi.fn(),
    },
  }),
  initReactI18next: {
    type: '3rdParty',
    init: vi.fn(),
  },
}))

// Mock API client
vi.mock('../src/services/api', () => ({
  apiClient: {
    search: vi.fn(),
    getSuggestions: vi.fn(),
    submitFeedback: vi.fn(),
  },
}))

describe('SearchPage', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('renders the search page', () => {
    render(<SearchPage />)
    expect(screen.getByRole('banner')).toBeInTheDocument()
    expect(screen.getByRole('main')).toBeInTheDocument()
  })

  it('renders search bar with placeholder', () => {
    render(<SearchPage />)
    const searchInput = screen.getByPlaceholderText('search:placeholder')
    expect(searchInput).toBeInTheDocument()
  })

  it('renders footer with GIGW elements', () => {
    render(<SearchPage />)
    const footer = screen.getByRole('contentinfo')
    expect(footer).toBeInTheDocument()
    expect(screen.getByText('search:content_managed_by')).toBeInTheDocument()
  })

  it('renders skip to content link', () => {
    render(<SearchPage />)
    const skipLink = screen.getByText('search:skip_to_content')
    expect(skipLink).toBeInTheDocument()
  })

  it('has proper ARIA landmarks', () => {
    render(<SearchPage />)
    expect(screen.getByRole('banner')).toBeInTheDocument()
    expect(screen.getByRole('main')).toBeInTheDocument()
    expect(screen.getByRole('contentinfo')).toBeInTheDocument()
  })
})
