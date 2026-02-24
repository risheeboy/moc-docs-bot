/**
 * MessageBubble Component
 * Renders individual messages with markdown and sources
 */

import React, { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import ReactMarkdown from 'react-markdown'
import { Message } from '../types'
import { SourceCard } from './SourceCard'
import { TypingIndicator } from './TypingIndicator'
import { FeedbackWidget } from './FeedbackWidget'
import { containsDevanagari } from '../utils/markdown'
import '../styles/widget.css'

interface Props {
  message: Message
  isStreaming?: boolean
}

export const MessageBubble: React.FC<Props> = ({ message, isStreaming = false }) => {
  const { t } = useTranslation()
  const isUser = message.role === 'user'
  const isDev = containsDevanagari(message.content)

  const messageClass = `message-bubble ${message.role} ${isDev ? 'devanagari' : 'latin'}`

  return (
    <div className={messageClass}>
      <div className="message-content">
        {isStreaming && !message.content ? (
          <TypingIndicator />
        ) : (
          <ReactMarkdown
            className="markdown-content"
            components={{
              a: ({ node, ...props }) => (
                <a {...props} target="_blank" rel="noopener noreferrer" />
              ),
              code: ({ inline, ...props }: any) =>
                inline ? (
                  <code className="inline-code" {...props} />
                ) : (
                  <pre className="code-block" {...props} />
                ),
              h1: ({ ...props }) => <h3 {...props} />,
              h2: ({ ...props }) => <h4 {...props} />
            }}
          >
            {message.content}
          </ReactMarkdown>
        )}
      </div>

      {isStreaming && <TypingIndicator />}

      {/* Sources for assistant messages */}
      {!isUser && message.sources && message.sources.length > 0 && (
        <div className="message-sources">
          <h4>{t('sources.title')}</h4>
          <div className="sources-list">
            {message.sources.map((source, idx) => (
              <SourceCard key={idx} source={source} />
            ))}
          </div>
        </div>
      )}

      {/* Fallback indicator */}
      {!isUser && message.has_fallback && (
        <div className="fallback-indicator" role="note">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="16" x2="12" y2="12" />
            <line x1="12" y1="8" x2="12.01" y2="8" />
          </svg>
          <span>{t('chat.fallback')}</span>
        </div>
      )}

      {/* Feedback widget for assistant messages */}
      {!isUser && !isStreaming && (
        <FeedbackWidget messageId={message.id} sessionId={message.id} />
      )}
    </div>
  )
}
