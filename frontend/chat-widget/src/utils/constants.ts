/**
 * Constants and configuration
 */

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export const DEFAULT_LANGUAGE = 'hi'
export const SUPPORTED_LANGUAGES = [
  { code: 'hi', label: 'हिंदी' },
  { code: 'en', label: 'English' },
  { code: 'bn', label: 'বাংলা' },
  { code: 'te', label: 'తెలుగు' },
  { code: 'mr', label: 'मराठी' },
  { code: 'ta', label: 'தமிழ்' },
  { code: 'ur', label: 'اردو' },
  { code: 'gu', label: 'ગુજરાતી' },
  { code: 'kn', label: 'ಕನ್ನಡ' },
  { code: 'ml', label: 'മലയാളം' },
  { code: 'or', label: 'ଓଡ଼ିଆ' },
  { code: 'pa', label: 'ਪੰਜਾਬੀ' }
]

export const CHAT_CONFIG = {
  MAX_MESSAGE_LENGTH: 2000,
  MAX_CONTEXT_MESSAGES: 20,
  CONTEXT_WINDOW_TOKENS: 4096,
  SESSION_TIMEOUT_MS: 30 * 60 * 1000, // 30 minutes
  TYPING_INDICATOR_DELAY_MS: 500,
  VOICE_RECORDING_TIMEOUT_MS: 60 * 1000, // 1 minute
  FILE_UPLOAD_MAX_SIZE_MB: 50,
  ALLOWED_FILE_TYPES: ['application/pdf', 'image/png', 'image/jpeg', 'text/plain']
}

export const ACCESSIBILITY_CONFIG = {
  FONT_SIZES: {
    small: '12px',
    normal: '14px',
    large: '16px',
    xlarge: '18px'
  },
  FONT_FAMILY_HINDI: "'Noto Sans Devanagari', 'Noto Sans', sans-serif",
  FONT_FAMILY_ENGLISH: "'Noto Sans', sans-serif"
}

export const WIDGET_CONFIG = {
  BUBBLE_SIZE: 60,
  BUBBLE_POSITION: 'bottom-right' as const,
  Z_INDEX: 2147483647,
  ANIMATION_DURATION_MS: 300,
  SHADOW_DOM_ID: 'rag-qa-chat-widget'
}

export const FALLBACK_MESSAGES = {
  hi: "मुझे इस विषय पर पर्याप्त जानकारी नहीं मिली। कृपया संस्कृति मंत्रालय हेल्पलाइन 011-23388261 पर संपर्क करें या arit-culture@gov.in पर ईमेल करें।",
  en: "I'm unable to find a reliable answer to your question. Please contact the Ministry of Culture helpline at 011-23388261 or email arit-culture@gov.in."
}

export const GIGW_CONFIG = {
  MINISTRY_NAME: 'Ministry of Culture, Government of India',
  MINISTRY_NAME_HI: 'भारतीय संस्कृति मंत्रालय, भारत सरकार',
  NIC_CREDIT: 'Designed, Developed and Hosted by NIC',
  CONTENT_MANAGED: 'Website Content Managed by Ministry of Culture',
  EMBLEM_ALT: 'National Emblem of India',
  HELPLINE: '011-23388261',
  EMAIL: 'arit-culture@gov.in'
}

export const API_ENDPOINTS = {
  CHAT: '/chat',
  CHAT_STREAM: '/chat/stream',
  SPEECH_STT: '/speech/stt',
  SPEECH_TTS: '/speech/tts',
  TRANSLATE: '/translate',
  FEEDBACK: '/feedback',
  SESSION: '/session',
  OCR: '/ocr/upload',
  HEALTH: '/health'
}

export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network error. Please check your connection.',
  TIMEOUT_ERROR: 'Request timeout. Please try again.',
  API_ERROR: 'API error. Please try again later.',
  FILE_TOO_LARGE: 'File size exceeds maximum limit.',
  INVALID_FILE: 'Invalid file type.',
  SPEECH_NOT_SUPPORTED: 'Speech is not supported in your browser.',
  MIC_PERMISSION_DENIED: 'Microphone permission denied.',
  UNKNOWN_ERROR: 'An unknown error occurred.'
}

export const ARIA_LABELS = {
  CHAT_BUBBLE: 'Open chat widget',
  CLOSE_BUTTON: 'Close chat',
  SEND_BUTTON: 'Send message',
  VOICE_BUTTON: 'Send voice message',
  LANGUAGE_SELECT: 'Select language',
  FEEDBACK_HELPFUL: 'Mark as helpful',
  FEEDBACK_NOT_HELPFUL: 'Mark as not helpful',
  FILE_UPLOAD: 'Upload file',
  ACCESSIBILITY_MENU: 'Accessibility options'
}
