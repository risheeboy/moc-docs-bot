import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import hiTranslations from './hi.json'
import enTranslations from './en.json'

const resources = {
  hi: {
    translation: hiTranslations
  },
  en: {
    translation: enTranslations
  }
}

i18n.use(initReactI18next).init({
  resources,
  lng: localStorage.getItem('language') || 'hi',
  fallbackLng: 'en',
  interpolation: {
    escapeValue: false
  },
  react: {
    useSuspense: false
  }
})

export default i18n
