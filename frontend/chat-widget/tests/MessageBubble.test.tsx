/**
 * MessageBubble Component Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { MessageBubble } from '../src/components/MessageBubble'
import { Message } from '../src/types'

describe('MessageBubble', () => {
  const mockMessage: Message = {
    id: 'msg-1',
    role: 'user',
    content: 'Hello',
    language: 'en',
    created_at: new Date().toISOString()
  }

  const mockAssistantMessage: Message = {
    id: 'msg-2',
    role: 'assistant',
    content: 'Hi there!',
    language: 'en',
    created_at: new Date().toISOString(),
    sources: [
      {
        title: 'Test Source',
        url: 'https://example.com',
        snippet: 'Test snippet',
        score: 0.95,
        source_site: 'example.com',
        language: 'en',
        content_type: 'webpage'
      }
    ]
  }

  it('renders user message', () => {
    render(<MessageBubble message={mockMessage} />)
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })

  it('renders assistant message', () => {
    render(<MessageBubble message={mockAssistantMessage} />)
    expect(screen.getByText('Hi there!')).toBeInTheDocument()
  })

  it('displays sources for assistant message', () => {
    render(<MessageBubble message={mockAssistantMessage} />)
    expect(screen.getByText('Sources')).toBeInTheDocument()
    expect(screen.getByText('Test Source')).toBeInTheDocument()
  })

  it('renders typing indicator when streaming', () => {
    const streamingMessage: Message = {
      ...mockAssistantMessage,
      content: ''
    }
    render(<MessageBubble message={streamingMessage} isStreaming={true} />)
    const indicator = screen.getByRole('status', { hidden: true })
    expect(indicator).toBeInTheDocument()
  })

  it('displays markdown content', () => {
    const markdownMessage: Message = {
      ...mockAssistantMessage,
      content: '**Bold text**'
    }
    render(<MessageBubble message={markdownMessage} />)
    const boldElement = screen.getByText('Bold text')
    expect(boldElement.tagName).toBe('STRONG')
  })

  it('applies correct CSS classes', () => {
    const { container } = render(<MessageBubble message={mockMessage} />)
    const bubble = container.querySelector('.message-bubble')
    expect(bubble).toHaveClass('user')
  })

  it('renders source links as external', () => {
    render(<MessageBubble message={mockAssistantMessage} />)
    const link = screen.getByRole('link', { name: /visit source/i })
    expect(link).toHaveAttribute('target', '_blank')
    expect(link).toHaveAttribute('rel', 'noopener noreferrer')
  })

  it('detects fallback messages', () => {
    const fallbackMessage: Message = {
      ...mockAssistantMessage,
      content: 'I am unable to find a reliable answer to your question',
      has_fallback: true
    }
    render(<MessageBubble message={fallbackMessage} />)
    expect(screen.getByRole('note')).toBeInTheDocument()
  })
})
