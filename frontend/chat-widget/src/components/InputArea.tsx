/**
 * InputArea Component
 * Text input, send button, voice input, file upload
 */

import React, { useState, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { LanguageCode } from '../types'
import { VoiceButton } from './VoiceButton'
import { FileUpload } from './FileUpload'
import { CHAT_CONFIG } from '../utils/constants'
import '../styles/widget.css'

interface Props {
  onSendMessage: (text: string) => void
  isLoading: boolean
  language: LanguageCode
}

export const InputArea: React.FC<Props> = ({ onSendMessage, isLoading, language }) => {
  const { t } = useTranslation()
  const [input, setInput] = useState('')
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim() && !isLoading) {
      onSendMessage(input.trim())
      setInput('')
      if (inputRef.current) {
        inputRef.current.focus()
      }
    }
  }

  const handleVoiceTranscription = (text: string) => {
    setInput(text)
  }

  const handleFileUpload = (text: string) => {
    setInput((prev) => (prev ? prev + '\n\n' + text : text))
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey && !isLoading) {
      handleSubmit(e as any)
    }
  }

  const characterCount = input.length
  const isNearLimit = characterCount > CHAT_CONFIG.MAX_MESSAGE_LENGTH * 0.9

  return (
    <form className="input-area" onSubmit={handleSubmit}>
      <div className="input-container">
        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value.slice(0, CHAT_CONFIG.MAX_MESSAGE_LENGTH))}
          onKeyDown={handleKeyDown}
          placeholder={t('chat.placeholder')}
          disabled={isLoading}
          aria-label={t('chat.placeholder')}
          rows={1}
          className="message-input"
        />

        {isNearLimit && (
          <div className="character-warning" aria-live="polite">
            {characterCount} / {CHAT_CONFIG.MAX_MESSAGE_LENGTH}
          </div>
        )}
      </div>

      <div className="input-controls">
        <VoiceButton
          onTranscription={handleVoiceTranscription}
          language={language}
          disabled={isLoading}
        />

        <FileUpload onUpload={handleFileUpload} disabled={isLoading} />

        <button
          type="submit"
          disabled={!input.trim() || isLoading}
          aria-label={t('chat.send')}
          className="send-button"
        >
          {isLoading ? (
            <svg className="loading-spinner" viewBox="0 0 24 24" width="20" height="20">
              <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="2" />
            </svg>
          ) : (
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
              <path d="M16.6915026,12.4744748 L3.50612381,13.2599618 C3.19218622,13.2599618 3.03521743,13.4170592 3.03521743,13.5741566 L1.15159189,20.0151496 C0.8376543,20.8006365 0.99,21.89 1.77946707,22.52 C2.41,22.99 3.50612381,23.1 4.13399899,22.9429026 L21.714504,14.0454487 C22.6563168,13.5741566 23.1272231,12.6315722 22.9702544,11.6889879 L4.13399899,1.05757588 C3.34915502,0.9 2.40734225,0.9 1.77946707,1.38565598 C0.994623095,2.01449553 0.837654326,3.10604706 1.15159189,3.89154396 L3.03521743,10.3325369 C3.03521743,10.4896343 3.19218622,10.6467317 3.50612381,10.6467317 L16.6915026,11.4322186 C16.6915026,11.4322186 17.1624089,11.4322186 17.1624089,12.0610581 C17.1624089,12.6898976 16.6915026,12.4744748 16.6915026,12.4744748 Z" />
            </svg>
          )}
        </button>
      </div>
    </form>
  )
}
