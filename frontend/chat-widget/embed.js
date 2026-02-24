/**
 * Embed Script
 * Standalone script to embed chat widget on Drupal site
 * Usage: <script src="https://culture.gov.in/chat-widget/embed.js"></script>
 */

(function () {
  // Configuration
  const config = {
    widgetId: 'rag-qa-chat-widget',
    apiBaseUrl: window.RAG_QA_API_BASE_URL || '/api/v1',
    containerId: 'rag-qa-chat-container',
    shadowDomId: 'rag-qa-shadow-root'
  }

  // Check if widget is already loaded
  if (document.getElementById(config.widgetId)) {
    console.warn('RAG QA Chat Widget already loaded')
    return
  }

  /**
   * Create Shadow DOM container
   */
  function createShadowContainer() {
    const container = document.createElement('div')
    container.id = config.containerId
    container.style.cssText = `
      position: fixed;
      bottom: 0;
      right: 0;
      z-index: 2147483647;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', sans-serif;
    `
    document.body.appendChild(container)

    // Attach Shadow DOM
    const shadowRoot = container.attachShadow({ mode: 'open' })
    return shadowRoot
  }

  /**
   * Load CSS dynamically
   */
  function loadCSS(shadowRoot, cssUrl) {
    return new Promise((resolve, reject) => {
      const link = document.createElement('link')
      link.rel = 'stylesheet'
      link.href = cssUrl
      link.onload = resolve
      link.onerror = reject
      shadowRoot.appendChild(link)
    })
  }

  /**
   * Load JavaScript dynamically
   */
  function loadScript(src) {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script')
      script.src = src
      script.type = 'module'
      script.onload = resolve
      script.onerror = reject
      document.head.appendChild(script)
    })
  }

  /**
   * Get embed script directory
   */
  function getScriptDir() {
    const scripts = document.querySelectorAll('script[src*="embed.js"]')
    if (scripts.length > 0) {
      const src = scripts[scripts.length - 1].src
      return src.substring(0, src.lastIndexOf('/') + 1)
    }
    return '/'
  }

  /**
   * Initialize widget
   */
  async function init() {
    try {
      // Create Shadow DOM container
      const shadowRoot = createShadowContainer()

      // Get script directory for asset loading
      const scriptDir = getScriptDir()

      // Create wrapper div for React app
      const appWrapper = document.createElement('div')
      appWrapper.id = 'react-app-root'
      appWrapper.style.cssText = `
        width: 100%;
        height: 100%;
        all: initial;
        display: block;
      `
      shadowRoot.appendChild(appWrapper)

      // Set config globally for widget
      window.RAG_QA_CONFIG = {
        ...config,
        scriptDir
      }

      // Inject CSS
      const styles = document.createElement('style')
      styles.textContent = `
        :host {
          all: initial;
          display: block;
        }

        * {
          box-sizing: border-box;
        }

        #react-app-root {
          width: 100%;
          height: 100%;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', sans-serif;
        }
      `
      shadowRoot.appendChild(styles)

      // Load and initialize React app
      // In production, this would be bundled as a single file
      console.log('RAG QA Chat Widget initialized')

      // Dispatch custom event
      const event = new CustomEvent('ragqaChatReady', {
        detail: { config }
      })
      document.dispatchEvent(event)
    } catch (error) {
      console.error('Failed to initialize RAG QA Chat Widget:', error)
    }
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init)
  } else {
    init()
  }

  // Expose widget control API
  window.RAG_QA_Chat = {
    open() {
      const event = new CustomEvent('ragqaChatOpen')
      document.dispatchEvent(event)
    },
    close() {
      const event = new CustomEvent('ragqaChatClose')
      document.dispatchEvent(event)
    },
    toggle() {
      const event = new CustomEvent('ragqaChatToggle')
      document.dispatchEvent(event)
    },
    setLanguage(lang) {
      const event = new CustomEvent('ragqaChatSetLanguage', {
        detail: { language: lang }
      })
      document.dispatchEvent(event)
    },
    sendMessage(message) {
      const event = new CustomEvent('ragqaChatSendMessage', {
        detail: { message }
      })
      document.dispatchEvent(event)
    }
  }
})()
