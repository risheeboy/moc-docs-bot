/**
 * FileUpload Component
 * Upload documents for OCR/querying
 */

import React, { useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { apiClient } from '../services/api'
import { CHAT_CONFIG } from '../utils/constants'
import '../styles/widget.css'

interface Props {
  onUpload: (text: string) => void
  disabled?: boolean
}

export const FileUpload: React.FC<Props> = ({ onUpload, disabled = false }) => {
  const { t } = useTranslation()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Validate file size
    if (file.size > CHAT_CONFIG.FILE_UPLOAD_MAX_SIZE_MB * 1024 * 1024) {
      setError(t('file.too_large') || 'File too large')
      return
    }

    // Validate file type
    if (!CHAT_CONFIG.ALLOWED_FILE_TYPES.includes(file.type)) {
      setError(t('file.invalid') || 'Invalid file type')
      return
    }

    setIsUploading(true)
    setError(null)

    try {
      const response = await apiClient.uploadFile(file)
      onUpload(response.text)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Upload failed'
      setError(message)
    } finally {
      setIsUploading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const handleClick = () => {
    fileInputRef.current?.click()
  }

  return (
    <div className="file-upload-wrapper">
      <input
        ref={fileInputRef}
        type="file"
        onChange={handleFileChange}
        accept={CHAT_CONFIG.ALLOWED_FILE_TYPES.join(',')}
        disabled={disabled || isUploading}
        className="file-input"
        aria-label={t('file.upload')}
      />

      <button
        type="button"
        onClick={handleClick}
        disabled={disabled || isUploading}
        className="file-upload-btn"
        aria-label={t('file.upload')}
        title={t('file.upload')}
      >
        {isUploading ? (
          <svg className="loading-spinner" viewBox="0 0 24 24" width="20" height="20">
            <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" />
          </svg>
        ) : (
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm3.5-9c.83 0 1.5-.67 1.5-1.5S16.33 8 15.5 8 14 8.67 14 9.5s.67 1.5 1.5 1.5zm-7 0c.83 0 1.5-.67 1.5-1.5S9.33 8 8.5 8 7 8.67 7 9.5 7.67 11 8.5 11zm3.5 6.5c2.33 0 4.31-1.46 5.11-3.5H6.89c.8 2.04 2.78 3.5 5.11 3.5z" />
          </svg>
        )}
      </button>

      {error && (
        <div className="upload-error" role="alert">
          {error}
        </div>
      )}
    </div>
  )
}
