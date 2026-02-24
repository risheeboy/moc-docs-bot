/**
 * Markdown utility functions
 */

/**
 * Sanitize markdown to prevent XSS
 */
export function sanitizeMarkdown(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

/**
 * Extract URLs from markdown text
 */
export function extractUrls(text: string): string[] {
  const urlRegex = /(https?:\/\/[^\s]+)/g
  const matches = text.match(urlRegex)
  return matches ? [...new Set(matches)] : []
}

/**
 * Truncate text with ellipsis
 */
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

/**
 * Format text for display (remove extra whitespace)
 */
export function formatText(text: string): string {
  return text
    .trim()
    .replace(/\n\n+/g, '\n\n')
    .replace(/\s+/g, ' ')
    .trim()
}

/**
 * Check if text contains Hindi/Devanagari characters
 */
export function containsDevanagari(text: string): boolean {
  const devanagariRegex = /[\u0900-\u097F]/
  return devanagariRegex.test(text)
}

/**
 * Check if text contains emoji
 */
export function containsEmoji(text: string): boolean {
  const emojiRegex = /[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{27BF}]/u
  return emojiRegex.test(text)
}

/**
 * Format timestamp to readable string
 */
export function formatTimestamp(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: 'numeric',
    hour12: true
  }).format(d)
}

/**
 * Parse response and check for fallback indicators
 */
export function detectFallbackResponse(text: string): boolean {
  const fallbackIndicators = [
    'unable to find',
    'no reliable answer',
    'पर्याप्त जानकारी नहीं',
    'helpline',
    'hel'
  ]
  return fallbackIndicators.some(indicator =>
    text.toLowerCase().includes(indicator.toLowerCase())
  )
}
