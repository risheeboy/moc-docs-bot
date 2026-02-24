/**
 * FeedbackWidget Component
 * Thumbs up/down and optional comment
 */

import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useChat } from '../hooks/useChat'
import { apiClient } from '../services/api'
import '../styles/widget.css'

interface Props {
  messageId: string
  sessionId: string
}

export const FeedbackWidget: React.FC<Props> = ({ messageId, sessionId }) => {
  const { t } = useTranslation()
  const { currentLanguage } = useChat()
  const [selectedRating, setSelectedRating] = useState<'helpful' | 'not_helpful' | null>(
    null
  )
  const [showComment, setShowComment] = useState(false)
  const [comment, setComment] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isSubmitted, setIsSubmitted] = useState(false)

  const handleRating = async (rating: 'helpful' | 'not_helpful') => {
    setSelectedRating(rating)
    setShowComment(true)

    if (!comment.trim()) {
      // Submit without comment if not shown
      await submitFeedback(rating)
    }
  }

  const submitFeedback = async (rating: 'helpful' | 'not_helpful') => {
    setIsSubmitting(true)
    try {
      await apiClient.submitFeedback({
        message_id: messageId,
        session_id: sessionId,
        rating,
        comment: comment.trim() || undefined,
        language: currentLanguage
      })
      setIsSubmitted(true)
      setTimeout(() => {
        setIsSubmitted(false)
        setSelectedRating(null)
        setShowComment(false)
        setComment('')
      }, 2000)
    } catch (error) {
      console.error('Failed to submit feedback:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleSubmitComment = async () => {
    if (selectedRating) {
      await submitFeedback(selectedRating)
    }
  }

  if (isSubmitted) {
    return (
      <div className="feedback-widget submitted">
        <p>{t('feedback.thank_you')}</p>
      </div>
    )
  }

  return (
    <div className="feedback-widget">
      <div className="feedback-buttons">
        <button
          type="button"
          onClick={() => handleRating('helpful')}
          disabled={isSubmitting}
          className={`feedback-btn helpful ${selectedRating === 'helpful' ? 'active' : ''}`}
          aria-label={t('feedback.helpful')}
          title={t('feedback.helpful')}
        >
          <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
            <path d="M14 21H10a2 2 0 0 1-2-2v-9a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2zM7 10.5a1.5 1.5 0 0 1 0-3H2v3h5z" />
          </svg>
        </button>

        <button
          type="button"
          onClick={() => handleRating('not_helpful')}
          disabled={isSubmitting}
          className={`feedback-btn not-helpful ${selectedRating === 'not_helpful' ? 'active' : ''}`}
          aria-label={t('feedback.not_helpful')}
          title={t('feedback.not_helpful')}
        >
          <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
            <path d="M10 3h4a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2zm7 7a1.5 1.5 0 0 0 0-3h5v3h-5z" />
          </svg>
        </button>
      </div>

      {showComment && selectedRating && (
        <div className="feedback-comment-form">
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder={t('feedback.comment')}
            rows={2}
            className="comment-input"
          />
          <button
            type="button"
            onClick={handleSubmitComment}
            disabled={isSubmitting}
            className="submit-comment-btn"
          >
            {t('feedback.submit')}
          </button>
        </div>
      )}
    </div>
  )
}
