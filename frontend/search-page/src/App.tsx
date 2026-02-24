import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import SearchPage from './pages/SearchPage'
import './App.css'

export default function App() {
  const { i18n } = useTranslation()
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const savedLanguage = localStorage.getItem('language') || 'en'
    i18n.changeLanguage(savedLanguage)
    document.documentElement.lang = savedLanguage
    setIsLoading(false)
  }, [i18n])

  if (isLoading) {
    return <div className="loading-screen">Loading...</div>
  }

  return (
    <div className="app" data-language={i18n.language}>
      <SearchPage />
    </div>
  )
}
