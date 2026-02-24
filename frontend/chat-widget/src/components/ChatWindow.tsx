/**
 * ChatWindow Component
 * Main chat interface with messages and input
 */

import React, { useState, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useChat } from '../hooks/useChat'
import { MessageBubble } from './MessageBubble'
import { InputArea } from './InputArea'
import { LanguageSelector } from './LanguageSelector'
import { Header } from './Header'
import { Footer } from './Footer'
import '../styles/widget.css'

interface Props {
  onClose: () => void
}

export const ChatWindow: React.FC<Props> = ({ onClose }) => {
  const { t } = useTranslation()
  const {
    messages,
    isLoading,
    currentLanguage,
    error,
    sendMessageStream,
    changeLanguage,
    clearMessages
  } = useChat()

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [currentStreamingContent, setCurrentStreamingContent] = useState('')

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isLoading])

  const handleSendMessage = (text: string) => {
    setCurrentStreamingContent('')
    sendMessageStream(
      text,
      (token) => {
        setCurrentStreamingContent((prev) => prev + token)
      }
    )
  }

  return (
    <div className="chat-window">
      <Header onClose={onClose} />

      <div className="chat-language-selector">
        <LanguageSelector
          currentLanguage={currentLanguage}
          onLanguageChange={changeLanguage}
        />
      </div>

      <div className="chat-messages" role="log" aria-label="Chat messages">
        {messages.length === 0 && !isLoading && (
          <div className="chat-empty-state">
            <p>{t('chat.empty')}</p>
            <p className="subtitle">{t('app.subtitle')}</p>
          </div>
        )}

        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}

        {isLoading && (
          <MessageBubble
            message={{
              id: 'streaming',
              role: 'assistant',
              content: currentStreamingContent || ' ',
              language: currentLanguage,
              created_at: new Date().toISOString()
            }}
            isStreaming={true}
          />
        )}

        {error && (
          <div className="error-message" role="alert">
            {error}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <InputArea
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
        language={currentLanguage}
      />

      <Footer />
    </div>
  )
}
