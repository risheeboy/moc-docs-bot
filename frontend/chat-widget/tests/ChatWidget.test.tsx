/**
 * ChatWidget Component Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { ChatWidget } from '../src/components/ChatWidget'

describe('ChatWidget', () => {
  const mockOnToggle = vi.fn()

  beforeEach(() => {
    mockOnToggle.mockClear()
  })

  it('renders floating chat bubble when closed', () => {
    render(<ChatWidget isOpen={false} onToggle={mockOnToggle} />)
    const bubble = screen.getByRole('button', { name: /open chat widget/i })
    expect(bubble).toBeInTheDocument()
  })

  it('opens chat window when bubble clicked', () => {
    render(<ChatWidget isOpen={false} onToggle={mockOnToggle} />)
    const bubble = screen.getByRole('button', { name: /open chat widget/i })
    fireEvent.click(bubble)
    expect(mockOnToggle).toHaveBeenCalled()
  })

  it('renders chat window when open', () => {
    render(<ChatWidget isOpen={true} onToggle={mockOnToggle} />)
    const container = screen.getByRole('complementary')
    expect(container).toBeInTheDocument()
  })

  it('hides bubble when chat window is open', () => {
    render(<ChatWidget isOpen={true} onToggle={mockOnToggle} />)
    const bubbles = screen.queryAllByRole('button', { name: /open chat widget/i })
    expect(bubbles).toHaveLength(0)
  })

  it('has proper ARIA labels', () => {
    render(<ChatWidget isOpen={true} onToggle={mockOnToggle} />)
    const complementary = screen.getByRole('complementary')
    expect(complementary).toHaveAttribute('aria-label')
  })

  it('applies animation on mount', () => {
    const { container } = render(<ChatWidget isOpen={true} onToggle={mockOnToggle} />)
    const windowContainer = container.querySelector('.chat-widget-container')
    expect(windowContainer).toHaveStyle('animation: slideUp')
  })
})
