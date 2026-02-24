export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export const SUPPORTED_LANGUAGES = [
  { code: 'en', label: 'English', native: 'English' },
  { code: 'hi', label: 'Hindi', native: 'हिंदी' },
  { code: 'bn', label: 'Bengali', native: 'বাংলা' },
  { code: 'te', label: 'Telugu', native: 'తెలుగు' },
  { code: 'mr', label: 'Marathi', native: 'मराठी' },
  { code: 'ta', label: 'Tamil', native: 'தமிழ்' },
  { code: 'ur', label: 'Urdu', native: 'اردو' },
  { code: 'gu', label: 'Gujarati', native: 'ગુજરાતી' },
  { code: 'kn', label: 'Kannada', native: 'ಕನ್ನಡ' },
  { code: 'ml', label: 'Malayalam', native: 'മലയാളം' },
  { code: 'or', label: 'Odia', native: 'ଓଡ଼ିଆ' },
  { code: 'pa', label: 'Punjabi', native: 'ਪੰਜਾਬੀ' },
  { code: 'as', label: 'Assamese', native: 'অসমীয়া' },
  { code: 'mai', label: 'Maithili', native: 'मैथिली' },
  { code: 'sa', label: 'Sanskrit', native: 'संस्कृत' },
  { code: 'ne', label: 'Nepali', native: 'नेपाली' },
  { code: 'sd', label: 'Sindhi', native: 'سنڌي' },
  { code: 'kok', label: 'Konkani', native: 'कोंकणी' },
  { code: 'doi', label: 'Dogri', native: 'डोगरी' },
  { code: 'mni', label: 'Manipuri', native: 'ম্যানিপুরি' },
  { code: 'sat', label: 'Santali', native: 'ᱥᱟᱱᱛᱟᱲᱤ' },
  { code: 'bo', label: 'Bodo', native: 'बोडो' },
  { code: 'ks', label: 'Kashmiri', native: 'کشمیری' },
]

export const DEFAULT_PAGE_SIZE = 20
export const MAX_PAGE_SIZE = 100
export const DEBOUNCE_MS = 300

export const CONTENT_TYPES = [
  { value: 'webpage', label: 'Web Page' },
  { value: 'document', label: 'Document' },
  { value: 'event', label: 'Event' },
  { value: 'multimedia', label: 'Multimedia' },
]

export const DEFAULT_SOURCE_SITES = [
  'culture.gov.in',
  'asi.nic.in',
  'ncert.nic.in',
  'nift.ac.in',
  'iccr.gov.in',
]

export const ACCESSIBILITY_LABELS = {
  SKIP_TO_CONTENT: 'Skip to main content',
  SEARCH_INPUT: 'Search input field',
  SEARCH_BUTTON: 'Search button',
  VOICE_SEARCH: 'Voice search button',
  CLEAR_SEARCH: 'Clear search input',
  FILTERS: 'Filters panel',
  ACCESSIBILITY: 'Accessibility settings',
}
