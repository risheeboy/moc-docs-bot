/**
 * TypingIndicator Component
 * Animated typing indicator for assistant
 */

import React from 'react'
import { useTranslation } from 'react-i18next'
import '../styles/widget.css'

export const TypingIndicator: React.FC = () => {
  const { t } = useTranslation()

  return (
    <div className="typing-indicator" aria-label={t('chat.typing')}>
      <span className="dot" />
      <span className="dot" />
      <span className="dot" />
    </div>
  )
}
