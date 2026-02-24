import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import ResultCard from '../src/components/ResultCard'
import { SearchResult } from '../src/types'

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: {
      language: 'en',
    },
  }),
}))

const mockResult: SearchResult = {
  title: 'Test Result',
  url: 'https://culture.gov.in/test',
  snippet: 'This is a test snippet',
  score: 0.95,
  source_site: 'culture.gov.in',
  language: 'en',
  content_type: 'webpage',
  published_date: '2024-01-15',
}

describe('ResultCard', () => {
  it('renders result title', () => {
    render(<ResultCard result={mockResult} />)
    expect(screen.getByText('Test Result')).toBeInTheDocument()
  })

  it('renders result snippet', () => {
    render(<ResultCard result={mockResult} />)
    expect(screen.getByText('This is a test snippet')).toBeInTheDocument()
  })

  it('renders source badge', () => {
    render(<ResultCard result={mockResult} />)
    expect(screen.getByText('sources:culture_ministry')).toBeInTheDocument()
  })

  it('renders content type badge', () => {
    render(<ResultCard result={mockResult} />)
    expect(screen.getByText('webpage')).toBeInTheDocument()
  })

  it('has clickable result link', () => {
    render(<ResultCard result={mockResult} />)
    const link = screen.getByRole('link', { name: 'Test Result' })
    expect(link).toHaveAttribute('href', 'https://culture.gov.in/test')
    expect(link).toHaveAttribute('target', '_blank')
  })

  it('shows feedback options on button click', () => {
    render(<ResultCard result={mockResult} />)
    const feedbackButton = screen.getByLabelText('search:aria_feedback')
    fireEvent.click(feedbackButton)
    expect(screen.getByLabelText('search:aria_helpful')).toBeInTheDocument()
  })

  it('calls onFeedback callback when feedback is submitted', () => {
    const mockFeedback = vi.fn()
    render(<ResultCard result={mockResult} onFeedback={mockFeedback} />)
    const feedbackButton = screen.getByLabelText('search:aria_feedback')
    fireEvent.click(feedbackButton)
    const helpfulButton = screen.getByLabelText('search:aria_helpful')
    fireEvent.click(helpfulButton)
    expect(mockFeedback).toHaveBeenCalledWith(true)
  })

  it('renders thumbnail if available', () => {
    const resultWithThumbnail = {
      ...mockResult,
      thumbnail_url: 'https://example.com/thumb.jpg',
    }
    render(<ResultCard result={resultWithThumbnail} />)
    const image = screen.getByAltText('Test Result')
    expect(image).toHaveAttribute('src', 'https://example.com/thumb.jpg')
  })
})
