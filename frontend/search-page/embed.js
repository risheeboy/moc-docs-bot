/**
 * Embeddable Search Bar for Drupal Header Integration
 * Include on any page with: <script src="https://search.culture.gov.in/embed.js"></script>
 */

(function () {
  const SEARCH_PAGE_URL = 'https://culture.gov.in/search'
  const API_SUGGEST_URL = '/api/v1/search/suggest'

  class EmbeddableSearchBar {
    constructor(options = {}) {
      this.container = options.container || 'search-bar-container'
      this.placeholder =
        options.placeholder || 'Search Ministry of Culture...'
      this.minChars = options.minChars || 3
      this.maxSuggestions = options.maxSuggestions || 5
      this.language = options.language || 'en'

      this.init()
    }

    init() {
      this.container =
        typeof this.container === 'string'
          ? document.getElementById(this.container)
          : this.container

      if (!this.container) {
        console.error('Search bar container not found')
        return
      }

      this.render()
      this.attachListeners()
    }

    render() {
      const html = `
        <div class="rag-search-embed">
          <form class="rag-search-form" role="search">
            <div class="rag-search-wrapper">
              <input
                type="text"
                class="rag-search-input"
                placeholder="${this.placeholder}"
                aria-label="Search Ministry of Culture"
                autocomplete="off"
              />
              <button type="submit" class="rag-search-button" aria-label="Search">
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                  <path d="M8 15C11.866 15 15 11.866 15 8C15 4.13401 11.866 1 8 1C4.13401 1 1 4.13401 1 8C1 11.866 4.13401 15 8 15Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M17 17L12.5 12.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
              <div class="rag-suggestions" role="region" aria-label="Search suggestions"></div>
            </div>
          </form>
          <style>
            .rag-search-embed {
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            }

            .rag-search-form {
              margin: 0;
              padding: 0;
            }

            .rag-search-wrapper {
              position: relative;
              display: flex;
              align-items: center;
              background: white;
              border: 1px solid #e0e0e0;
              border-radius: 6px;
              padding: 8px 12px;
              gap: 8px;
            }

            .rag-search-input {
              flex: 1;
              border: none;
              outline: none;
              font-size: 14px;
              padding: 0;
              font-family: inherit;
            }

            .rag-search-button {
              background: none;
              border: none;
              cursor: pointer;
              color: #666;
              display: flex;
              align-items: center;
              justify-content: center;
              width: 24px;
              height: 24px;
              padding: 0;
              margin: 0;
            }

            .rag-search-button:hover {
              color: #1f3a93;
            }

            .rag-suggestions {
              position: absolute;
              top: 100%;
              left: 0;
              right: 0;
              background: white;
              border: 1px solid #e0e0e0;
              border-top: none;
              border-radius: 0 0 6px 6px;
              max-height: 300px;
              overflow-y: auto;
              display: none;
              margin-top: -1px;
            }

            .rag-suggestions.active {
              display: block;
            }

            .rag-suggestion {
              padding: 10px 12px;
              cursor: pointer;
              font-size: 14px;
              color: #333;
            }

            .rag-suggestion:hover {
              background-color: #f5f5f5;
            }

            .rag-suggestion-text {
              display: flex;
              align-items: center;
              gap: 8px;
            }

            .rag-suggestion-icon {
              color: #999;
              flex-shrink: 0;
            }
          </style>
        </div>
      `

      this.container.innerHTML = html
      this.form = this.container.querySelector('.rag-search-form')
      this.input = this.container.querySelector('.rag-search-input')
      this.button = this.container.querySelector('.rag-search-button')
      this.suggestionsBox = this.container.querySelector('.rag-suggestions')
    }

    attachListeners() {
      this.form.addEventListener('submit', (e) => this.handleSubmit(e))
      this.input.addEventListener('input', (e) => this.handleInput(e))
      this.input.addEventListener('blur', () => this.hideSuggestions())
      document.addEventListener('click', (e) => {
        if (!this.container.contains(e.target)) {
          this.hideSuggestions()
        }
      })
    }

    handleSubmit(e) {
      e.preventDefault()
      const query = this.input.value.trim()
      if (query) {
        const params = new URLSearchParams({
          q: query,
          lang: this.language,
        })
        window.location.href = `${SEARCH_PAGE_URL}?${params.toString()}`
      }
    }

    async handleInput(e) {
      const query = e.target.value.trim()

      if (query.length < this.minChars) {
        this.hideSuggestions()
        return
      }

      try {
        const params = new URLSearchParams({
          q: query,
          language: this.language,
        })
        const response = await fetch(`${API_SUGGEST_URL}?${params}`)
        const data = await response.json()

        if (data.suggestions && data.suggestions.length > 0) {
          this.showSuggestions(data.suggestions)
        } else {
          this.hideSuggestions()
        }
      } catch (error) {
        console.error('Failed to fetch suggestions:', error)
        this.hideSuggestions()
      }
    }

    showSuggestions(suggestions) {
      this.suggestionsBox.innerHTML = suggestions
        .slice(0, this.maxSuggestions)
        .map(
          (suggestion) => `
        <div class="rag-suggestion" data-query="${suggestion.text}">
          <div class="rag-suggestion-text">
            <svg class="rag-suggestion-icon" width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M6 12C9.31371 12 12 9.31371 12 6C12 2.68629 9.31371 0 6 0C2.68629 0 0 2.68629 0 6C0 9.31371 2.68629 12 6 12Z" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M11 11L13 13" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            ${suggestion.text}
          </div>
        </div>
      `
        )
        .join('')

      this.suggestionsBox.classList.add('active')

      this.suggestionsBox.querySelectorAll('.rag-suggestion').forEach((el) => {
        el.addEventListener('click', () => {
          this.input.value = el.dataset.query
          this.handleSubmit(new Event('submit'))
        })
      })
    }

    hideSuggestions() {
      this.suggestionsBox.classList.remove('active')
    }
  }

  // Auto-initialize if container exists
  document.addEventListener('DOMContentLoaded', function () {
    if (document.getElementById('rag-search-bar')) {
      window.ragSearchBar = new EmbeddableSearchBar({
        container: 'rag-search-bar',
        language: document.documentElement.lang || 'en',
      })
    }
  })

  // Export for manual initialization
  window.RagSearchBar = EmbeddableSearchBar
})()
