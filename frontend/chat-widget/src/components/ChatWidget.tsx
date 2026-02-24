/**
 * ChatWidget Component
 * Main floating chat bubble and expandable widget
 */

import React, { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { ChatWindow } from './ChatWindow'
import { WIDGET_CONFIG } from '../utils/constants'
import '../styles/widget.css'

interface Props {
  isOpen: boolean
  onToggle: () => void
}

export const ChatWidget: React.FC<Props> = ({ isOpen, onToggle }) => {
  const { t } = useTranslation()
  const [isMounted, setIsMounted] = useState(false)

  useEffect(() => {
    setIsMounted(true)
  }, [])

  if (!isMounted) return null

  return (
    <>
      {/* Floating bubble */}
      {!isOpen && (
        <button
          className="chat-bubble"
          onClick={onToggle}
          aria-label={t('aria.chat_bubble')}
          title={t('app.title')}
        >
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
        </button>
      )}

      {/* Expanded chat window */}
      {isOpen && (
        <div
          className="chat-widget-container"
          role="complementary"
          aria-label={t('app.title')}
        >
          <ChatWindow onClose={onToggle} />
        </div>
      )}
    </>
  )
}
