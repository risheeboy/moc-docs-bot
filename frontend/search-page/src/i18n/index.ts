import i18next from 'i18next'
import { initReactI18next } from 'react-i18next'
import enTranslations from './en.json'
import hiTranslations from './hi.json'

i18next.use(initReactI18next).init({
  resources: {
    en: { translation: enTranslations },
    hi: { translation: hiTranslations },
  },
  lng: localStorage.getItem('language') || 'hi',
  fallbackLng: 'en',
  interpolation: {
    escapeValue: false,
  },
})

export default i18next
