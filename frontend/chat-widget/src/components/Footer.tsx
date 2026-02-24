/**
 * Footer Component
 * GIGW compliant footer with required links and info
 */

import React from 'react'
import { useTranslation } from 'react-i18next'
import { GIGW_CONFIG } from '../utils/constants'
import '../styles/widget.css'

export const Footer: React.FC = () => {
  const { t } = useTranslation()

  const today = new Date().toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })

  return (
    <footer className="chat-footer" role="contentinfo">
      <div className="footer-content">
        <p className="footer-text">{t('footer.copyright')}</p>
        <p className="footer-text">{t('footer.designed')}</p>
        <p className="footer-text">
          {t('footer.updated')}: {today}
        </p>
      </div>

      <nav className="footer-links" aria-label="Footer links">
        <a href="/" title="Sitemap">
          {t('footer.sitemap')}
        </a>
        <a href="/" title="Feedback">
          {t('footer.feedback')}
        </a>
        <a href="/" title="Terms and Conditions">
          {t('footer.terms')}
        </a>
        <a href="/" title="Privacy Policy">
          {t('footer.privacy')}
        </a>
        <a href="/" title="Copyright Policy">
          {t('footer.copyright_policy')}
        </a>
        <a href="/" title="Hyperlinking Policy">
          {t('footer.linking_policy')}
        </a>
        <a href="/" title="Accessibility Statement">
          {t('footer.accessibility')}
        </a>
      </nav>

      <div className="footer-contact" aria-label="Contact information">
        <p>
          <strong>{t('footer.helpline')}:</strong> {GIGW_CONFIG.HELPLINE}
        </p>
        <p>
          <strong>Email:</strong>{' '}
          <a href={`mailto:${GIGW_CONFIG.EMAIL}`}>{GIGW_CONFIG.EMAIL}</a>
        </p>
      </div>
    </footer>
  )
}
